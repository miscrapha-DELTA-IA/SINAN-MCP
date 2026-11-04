"""Offline dictionary-to-file structure comparison, always unapproved.

Administrators supply a locally obtained, named ZIP and a PDF, then review
a *manual* transcription of DBF field names from the cited dictionary.
The PDF is bound by a locally observed hash. This DOES NOT authenticate the
publisher, prove that the dictionary applies to 2024, validate records,
disclose patients or grant permission to analyze/publish.

CSV: reads bounded header only, no record values.
JSON: opt-in ijson streaming parses a bounded sample of records, including
their values transiently in the local process; values are NEVER retained,
reported or logged. Nested objects are flagged for review. No JSON support
is enabled in the public MCP or automatic ingestion path.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
import zipfile

from .local_distribution_review import conferir_zip_recurso_local
from .official_annual_resources import _index
from .year_evidence_registry import consultar_evidencia_agravo_ano

SCHEMA = "sinan-local-dictionary-structure-candidate-v1"
REPORT_SCHEMA = "sinan-private-schema-comparison-v1"
REGEX_FIELD = re.compile(r"[A-Z][A-Z0-9_]{0,31}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
MAX_CONTRACT_BYTES = 96_000
MAX_FIELDS = 350
MAX_PDF_BYTES = 40 * 1024 * 1024
MAX_CSV_HEADER_BYTES = 128 * 1024
MAX_JSON_READ_BYTES = 16 * 1024 * 1024
MAX_JSON_RECORDS = 64
# These three examples apply ONLY to Dengue/Chikungunya. Zika uses its own
# human-reviewed PDF excerpts; the samples are not a full official schema.
EXAMPLE_FIELDS = (
    {"name": "ID_AGRAVO", "pdf_page_1_based": 2},
    {"name": "DT_INVEST", "pdf_page_1_based": 2},
    {"name": "ID_OCUPA_N", "pdf_page_1_based": 2},
)
CONTRACT_KEYS = {
    "schema_version", "agravo", "ano_rotulado_no_portal", "resource_id",
    "dictionary_url", "pdf_sha256_local_observado", "format",
    "csv_encoding", "csv_delimiter", "json_layout", "cobertura",
    "campos_dbf", "situacao_transcricao",
}
ALLOWED_COVERAGE = {"excerto_parcial", "transcricao_pretendida_completa"}
WARN = (
    "CANDIDATO PRIVADO: confronto entre nomes de campos e transcrição "
    "manual, NÃO validação do dicionário oficial para o ano. Hashes são "
    "locais, sem autenticação independente. Nenhuma análise epidemiológica, "
    "cálculo, divulgação ou publicação autorizada."
)


def _reject_duplicate_keys(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("Contrato com chave JSON repetida")
        out[key] = value
    return out


def _resource(resource_id):
    if not isinstance(resource_id, str):
        raise ValueError("Identificador do recurso não reconhecido")
    _, rows = _index()
    item = next((x for x in rows if x["resource_id"] == resource_id), None)
    if item is None:
        raise ValueError("Identificador do recurso ausente da curadoria")
    return item


def _local_pdf_hash(pdf_path: str | Path, *, expected_url: str) -> str:
    path = Path(pdf_path).expanduser()
    basename = urlsplit(expected_url).path.rsplit("/", 1)[-1]
    if (path.is_symlink() or not path.is_file() or path.name != basename
            or not 8 <= path.stat().st_size <= MAX_PDF_BYTES):
        raise ValueError("Documento PDF local ausente ou fora da referência")
    digest = hashlib.sha256()
    n = 0
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError("Arquivo informado não possui cabeçalho PDF")
        stream.seek(0)
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            n += len(block)
            if n > MAX_PDF_BYTES:
                raise ValueError("PDF mudou ou excedeu limite durante leitura")
            digest.update(block)
    if n != path.stat().st_size:
        raise ValueError("Documento PDF mudou durante leitura")
    return digest.hexdigest()


def validate_candidate(candidate: object) -> dict:
    if (not isinstance(candidate, dict) or set(candidate) != CONTRACT_KEYS
            or candidate["schema_version"] != SCHEMA
            or candidate["situacao_transcricao"] != "manual_nao_revisada"):
        raise ValueError("Contrato candidato inválido ou indevidamente aprovado")
    row = _resource(candidate["resource_id"])
    if row["distribution_format"] not in ("CSV", "JSON"):
        raise ValueError(
            "Comparador privado ainda nao suporta PARQUET; nao converter "
            "ou tratar os bytes como JSON"
        )
    if (candidate["agravo"] != row["agravo_alias_interno"]
            or type(candidate["ano_rotulado_no_portal"]) is not int
            or candidate["ano_rotulado_no_portal"] != row["ano_rotulado_no_portal"]
            or candidate["format"] != row["distribution_format"]):
        raise ValueError("Agravo, ano ou formato não correspondem ao recurso curado")
    expected_doc = consultar_evidencia_agravo_ano(
        row["agravo_alias_interno"], row["ano_rotulado_no_portal"]
    )["evidencia_documental"]
    if expected_doc is None or candidate["dictionary_url"] != expected_doc["documento_url"]:
        raise ValueError("Dicionário diverge da referência documental curada")
    sha = candidate["pdf_sha256_local_observado"]
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise ValueError("Checksum local de PDF ausente ou inválido")
    if (not isinstance(candidate["cobertura"], str)
            or candidate["cobertura"] not in ALLOWED_COVERAGE):
        raise ValueError("Cobertura da transcrição inválida")
    if row["distribution_format"] == "CSV":
        if (candidate["csv_encoding"] not in ("utf-8-sig", "latin-1", "cp1252")
                or candidate["csv_delimiter"] not in (",", ";", "\t", "|")
                or candidate["json_layout"] is not None):
            raise ValueError("Codificação ou delimitador CSV não permitido")
    elif (candidate["csv_encoding"] is not None
          or candidate["csv_delimiter"] is not None
          or candidate["json_layout"] not in (
              "array_of_objects", "ndjson",
              "nao_determinado" if row["agravo_alias_interno"] == "ZIKA"
              else "array_of_objects",
          )):
        raise ValueError("Layout de JSON fora do protocolo local")
    fields = candidate["campos_dbf"]
    if (not isinstance(fields, list) or not 1 <= len(fields) <= MAX_FIELDS):
        raise ValueError("Transcrição de campos vazia ou excessiva")
    names = set()
    for field in fields:
        if (not isinstance(field, dict)
                or set(field) != {"name", "pdf_page_1_based"}
                or not isinstance(field["name"], str)
                or not REGEX_FIELD.fullmatch(field["name"])
                or type(field["pdf_page_1_based"]) is not int
                or not 1 <= field["pdf_page_1_based"] <= 200
                or field["name"] in names):
            raise ValueError("Campo DBF inválido, repetido ou sem página")
        names.add(field["name"])
    return candidate


def load_candidate(path: str | Path) -> dict:
    p = Path(path).expanduser()
    if (p.is_symlink() or not p.is_file()
            or not 2 <= p.stat().st_size <= MAX_CONTRACT_BYTES):
        raise ValueError("Contrato local ausente ou acima do limite")
    try:
        with p.open("r", encoding="utf-8") as stream:
            value = json.load(stream, object_pairs_hook=_reject_duplicate_keys)
        return validate_candidate(value)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("Contrato JSON malformado") from None


def _prepare_template_dict(resource_id: str, pdf: str | Path) -> dict:
    row = _resource(resource_id)
    evidence = consultar_evidencia_agravo_ano(
        row["agravo_alias_interno"], row["ano_rotulado_no_portal"]
    )["evidencia_documental"]
    if evidence is None:
        raise ValueError("Não existe dicionário documental curado para este ano")
    fmt = row["distribution_format"]
    if fmt not in ("CSV", "JSON"):
        raise ValueError("Modelo de esquema para PARQUET ainda nao implementado")
    agravo = row["agravo_alias_interno"]
    if agravo == "ZIKA":
        from .zika_official_dictionary_reference import (
            VISIBLE_FIELD_EXAMPLES, PDF_URL,
        )
        if evidence["documento_url"] != PDF_URL:
            raise ValueError("Fonte PDF Zika difere da referência oficial")
        fields = [
            {"name": name.upper(), "pdf_page_1_based": page}
            for name, page, _field_type in VISIBLE_FIELD_EXAMPLES
        ]
        json_layout = "nao_determinado"  # Never infer 2024 export topology.
    elif agravo in ("DENG", "CHIK"):
        fields = [dict(item) for item in EXAMPLE_FIELDS]
        json_layout = "array_of_objects" if fmt == "JSON" else None
    else:
        raise ValueError("Modelo de exemplos indisponivel para este agravo")
    sha = _local_pdf_hash(pdf, expected_url=evidence["documento_url"])
    template = {
        "schema_version": SCHEMA,
        "agravo": row["agravo_alias_interno"],
        "ano_rotulado_no_portal": row["ano_rotulado_no_portal"],
        "resource_id": resource_id,
        "dictionary_url": evidence["documento_url"],
        "pdf_sha256_local_observado": sha,
        "format": fmt,
        "csv_encoding": "utf-8-sig" if fmt == "CSV" else None,
        "csv_delimiter": "," if fmt == "CSV" else None,
        "json_layout": json_layout,
        "cobertura": "excerto_parcial",
        # Source-specific excerpt only; NEVER the full annual schema.
        "campos_dbf": fields,
        "situacao_transcricao": "manual_nao_revisada",
    }
    return validate_candidate(template)


def preparar_modelo_local(resource_id: str, pdf: str | Path, destino: str | Path) -> dict:
    """Create a local template with owner-only permissions; never auto-approve."""
    doc = _prepare_template_dict(resource_id, pdf)
    out = Path(destino).expanduser()
    if (out.is_symlink() or out.suffix.lower() != ".json"
            or not out.parent.is_dir() or out.parent.is_symlink()):
        raise ValueError("Destino JSON local inválido")
    fd = os.open(str(out), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(doc, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except BaseException:
        try:
            out.unlink()
        except OSError:
            pass
        raise
    return {
        "resource_id": resource_id,
        "arquivo_modelo_criado_localmente": True,
        "campos_exemplo_documentados": len(doc["campos_dbf"]),
        "cobertura": "excerto_parcial",
        "aprovado": False,
        "aviso": WARN,
    }


def _header_csv(stream, contract: dict) -> set[str]:
    raw = stream.readline(MAX_CSV_HEADER_BYTES + 1)
    if (not raw or len(raw) > MAX_CSV_HEADER_BYTES
            or not raw.endswith(b"\n")):
        raise ValueError("Cabeçalho CSV excede limite ou não terminou em linha")
    try:
        header_text = raw.decode(contract["csv_encoding"], errors="strict")
        header = next(csv.reader(io.StringIO(header_text, newline=""),
                                 delimiter=contract["csv_delimiter"], strict=True))
    except (UnicodeError, csv.Error, StopIteration):
        raise ValueError("Cabeçalho CSV incompatível com o contrato") from None
    if (not 1 <= len(header) <= 2000
            or any(not REGEX_FIELD.fullmatch(x) for x in header)
            or len(set(header)) != len(header)):
        raise ValueError(
            "Cabeçalho CSV duplicado, não padronizado ou com nomes inválidos"
        )
    return set(header)


class _BoundedBinary:
    """Cap decompression bytes consumed by the JSON event parser."""
    def __init__(self, stream, limit: int):
        self._stream = stream
        self._left = limit
    def read(self, size=-1):
        if size is None or size < 0:
            size = self._left + 1
        size = min(size, self._left + 1)
        data = self._stream.read(size)
        self._left -= len(data)
        if self._left < 0:
            raise ValueError("Orçamento de leitura do JSON excedido")
        return data


def _json_keys(stream, contract: dict) -> tuple[set[str], int, bool]:
    try:
        import ijson
    except ImportError:
        raise RuntimeError(
            "JSON exige dependência local opcional: pip install -e '.[schemaaudit]'"
        ) from None
    layout = contract["json_layout"]
    seen: set[str] = set()
    count = 0
    nested = False
    in_root_record = False
    first = True
    events = ijson.parse(
        _BoundedBinary(stream, MAX_JSON_READ_BYTES),
        multiple_values=(layout == "ndjson"),
    )
    try:
        for prefix, event, value in events:
            if first:
                expected_first = ("start_array" if layout == "array_of_objects"
                                  else "start_map")
                if prefix != "" or event != expected_first:
                    raise ValueError("Topologia JSON incompatível com o modelo")
                first = False
            row_prefix = "item" if layout == "array_of_objects" else ""
            if event == "start_map" and prefix == row_prefix:
                if in_root_record:
                    raise ValueError("JSON com objeto aninhado ambíguo")
                in_root_record = True
                continue
            if event == "map_key" and prefix == row_prefix and in_root_record:
                if (not isinstance(value, str)
                        or not REGEX_FIELD.fullmatch(value)):
                    raise ValueError("Campo JSON fora do padrão DBF controlado")
                seen.add(value)
                if len(seen) > 2000:
                    raise ValueError("JSON excede limite de campos distintos")
            if in_root_record and prefix != row_prefix and event in (
                "start_array", "start_map",
            ):
                nested = True
            if event == "end_map" and prefix == row_prefix and in_root_record:
                in_root_record = False
                count += 1
                if count >= MAX_JSON_RECORDS:
                    break
            if event == "end_array" and prefix == "" and count == 0:
                raise ValueError("JSON sem objetos para leitura")
    except (ValueError, OverflowError):
        raise ValueError("Estrutura JSON incompatível ou leitura limitada") from None
    except Exception:
        # Parser exception messages can include raw values: never propagate.
        raise ValueError("JSON malformado ou não suportado") from None
    if count < 1 or not seen or in_root_record:
        raise ValueError("JSON sem registro ou campos reconhecíveis")
    return seen, count, nested


def comparar_esquema_local(
    resource_id: str, arquivo_zip: str | Path,
    pdf: str | Path, contrato: str | Path,
) -> dict:
    """Conservative offline structural report; no data release or approval."""
    expected = load_candidate(contrato)
    if expected["resource_id"] != resource_id:
        raise ValueError("Contrato e recurso anual não correspondem")
    if expected["format"] == "JSON" and expected["json_layout"] == "nao_determinado":
        raise ValueError(
            "Layout JSON ZIKA/2024 nao identificado: revisar manualmente "
            "array_of_objects ou ndjson antes de qualquer comparacao privada"
        )
    actual_pdf_sha = _local_pdf_hash(
        pdf, expected_url=expected["dictionary_url"]
    )
    if actual_pdf_sha != expected["pdf_sha256_local_observado"]:
        raise ValueError("PDF local mudou desde a criação do contrato")
    result = conferir_zip_recurso_local(resource_id, arquivo_zip)
    row = _resource(resource_id)
    path = Path(arquivo_zip).expanduser()
    stat_before = path.stat()
    try:
        with zipfile.ZipFile(path, "r") as archive:
            only = archive.infolist()
            if len(only) != 1 or only[0].filename != row["archive_filename"][:-4]:
                raise ValueError("Arquivo compactado fora da referência curada")
            with archive.open(only[0], "r") as member:
                if expected["format"] == "CSV":
                    observed = _header_csv(member, expected)
                    rows_read = 0
                    nested = False
                    values_touched = False
                else:
                    observed, rows_read, nested = _json_keys(member, expected)
                    values_touched = True
    except (zipfile.BadZipFile, OSError, UnicodeError, RuntimeError):
        raise ValueError("Não foi possível inspecionar estrutura local") from None
    stat_after = path.stat()
    if (stat_after.st_size != stat_before.st_size
            or stat_after.st_mtime_ns != stat_before.st_mtime_ns):
        raise ValueError("ZIP local foi alterado durante a auditoria")
    documented = {f["name"] for f in expected["campos_dbf"]}
    missing = sorted(documented - observed)
    extras = observed - documented
    # Do not echo arbitrary header names: a malicious header may contain PII.
    discrepancy = bool(missing or nested or (
        extras and expected["cobertura"] == "transcricao_pretendida_completa"
    ))
    return {
        "schema_version": REPORT_SCHEMA,
        "resource_id": resource_id,
        "agravo": row["agravo_alias_interno"],
        "ano_rotulado_no_portal": row["ano_rotulado_no_portal"],
        "edicao_documental": consultar_evidencia_agravo_ano(
            row["agravo_alias_interno"], row["ano_rotulado_no_portal"]
        )["evidencia_documental"]["edicao_documental"],
        "dictionary_url": expected["dictionary_url"],
        "pdf_sha256_local": actual_pdf_sha,
        "zip_sha256_local": result["arquivo_pacote_sha256_local"],
        "zip_bytes_local": result["arquivo_pacote_bytes_local"],
        "cobertura_transcricao": expected["cobertura"],
        "n_campos_documentados": len(documented),
        "n_campos_observados": len(observed),
        "campos_documentados_presentes": sorted(documented & observed),
        "campos_documentados_ausentes": missing,
        "n_campos_nao_documentados": len(extras),
        "nomes_de_campos_nao_documentados_expostos": False,
        "json_registros_amostrados_localmente": rows_read,
        "json_limite_registros_amostrados": MAX_JSON_RECORDS,
        "json_valores_examinados_transitoriamente": values_touched,
        "json_objetos_aninhados_detectados": nested,
        "dados_clinicos_no_relatorio": False,
        "divergencia_na_cobertura_declarada": discrepancy,
        "estado": (
            "divergencia_estrutural_para_revisao" if discrepancy else
            "correspondencia_parcial_sem_validacao_anual"
        ),
        "origem_dos_bytes_autenticada": False,
        "dicionario_aplicavel_ao_ano_verificado": False,
        "campos_dominios_e_tipos_validados": False,
        "coorte_e_indicador_validados": False,
        "revisao_epidemiologica_independente": False,
        "publicacao_autorizada": False,
        "aviso": WARN,
    }


def salvar_parecer_pendente_local(relatorio: dict, destino: str | Path) -> dict:
    """Write owner-only REVIEW PACKAGE (not a signed independent decision).

    Evidence + checklist are private and deliberately immutable on creation.
    Nothing in this function can turn a review into an approved release.
    """
    if (not isinstance(relatorio, dict)
            or relatorio.get("schema_version") != REPORT_SCHEMA
            or relatorio.get("publicacao_autorizada") is not False
            or relatorio.get("revisao_epidemiologica_independente") is not False):
        raise ValueError("Relatório incompatível com o estado pendente")
    out = Path(destino).expanduser()
    if (out.is_symlink() or not out.parent.is_dir()
            or out.parent.is_symlink() or out.suffix.lower() != ".json"):
        raise ValueError("Destino privado JSON inválido")
    result = {
        "schema_version": "sinan-independent-epidemiology-review-pending-v1",
        "observacao_estrutural": relatorio,
        "verificacoes_pendentes": {
            "identidade_e_origem_do_arquivo": "pendente",
            "hash_publicado_pela_autoridade": "pendente",
            "edicao_do_dicionario_aplicavel_ao_ano": "pendente",
            "transcricao_completa_de_nomes_e_tipos": "pendente",
            "dominios_e_codigos_de_categorias": "pendente",
            "sistema_origem_e_data_de_corte": "pendente",
            "qualidade_e_cobertura_de_notificacoes": "pendente",
            "unidade_observacional_deduplicacao_e_coorte": "pendente",
            "parecer_epidemiologico_independente": "pendente",
            "privacidade_composicao_entre_publicacoes": "pendente",
        },
        "resultado_revisao": "NAO_AVALIADO",
        "declaracao_nao_e_parecer_assinado": True,
        "autorizacao_uso_cientifico": False,
        "autorizacao_publicacao": False,
        "aviso": WARN,
    }
    fd = os.open(str(out), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except BaseException:
        try:
            out.unlink()
        except OSError:
            pass
        raise
    return {
        "parecer_pendente_gerado_localmente": True,
        "autorizacao_publicacao": False,
        "total_etapas_pendentes": len(result["verificacoes_pendentes"]),
        "aviso": WARN,
    }
