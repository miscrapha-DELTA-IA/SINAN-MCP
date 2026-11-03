"""Optional LOCAL reviewer-only sidecar for names not covered by a public PDF.

No patient rows; the only CSV bytes parsed are the bounded first line.
Unlike the regular crosswalk report, this opt-in PRIVATE file contains
previously unknown header names: NEVER upload, print, log, or release it.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import zipfile

from .local_dengue_dictionary_crosswalk import (
    RESOURCE_ID, examinar_pdf_dengue_local,
)
from .local_distribution_review import conferir_zip_recurso_local
from .local_schema_review import (
    _header_csv, _reject_duplicate_keys, _resource, load_candidate,
)

PRIVATE_SCHEMA = "sinan-private-dengue-csv-header-unknowns-v1"
MAX_PREVIOUS_REPORT_BYTES = 128_000
MAX_UNEXPECTED_NAMES = 2000


def _load_previous_crosswalk(path: str | Path) -> dict:
    p = Path(path).expanduser()
    if (p.is_symlink() or not p.is_file()
            or not 2 <= p.stat().st_size <= MAX_PREVIOUS_REPORT_BYTES):
        raise ValueError("Parecer anterior ausente ou acima do limite")
    with p.open("r", encoding="utf-8") as f:
        result = json.load(f, object_pairs_hook=_reject_duplicate_keys)
    if (not isinstance(result, dict)
            or result.get("schema_version") != "sinan-private-dengue-crosswalk-candidate-v1"
            or result.get("resource_id") != RESOURCE_ID
            or result.get("status_revisao") != "PENDENTE"
            or result.get("autorizacao_analise_real") is not False
            or result.get("publicacao_autorizada") is not False):
        raise ValueError("Parecer anterior não corresponde ao escopo local")
    return result


def gerar_revisao_privada_cabecalhos_dengue(
    pdf_path: str | Path, contrato_2015_path: str | Path,
    zip_path: str | Path, parecer_anterior_path: str | Path,
    destino: str | Path,
) -> dict:
    """Record only extra CSV HEADER names in an explicitly requested private file.

    All hashes/counts are compared to the previous pending crosswalk to
    avoid combining unrelated versions. No stdout or MCP exposure of names.
    """
    pdf = examinar_pdf_dengue_local(pdf_path)
    old = load_candidate(contrato_2015_path)
    if old["resource_id"] != RESOURCE_ID or old["format"] != "CSV":
        raise ValueError("Contrato histórico local não corresponde a DENG/2024")
    prior = _load_previous_crosswalk(parecer_anterior_path)
    if (prior.get("pdf_atual_sha256_local") != pdf["pdf_sha256_local"]
            or prior.get("pdf2015_sha256_local") != old["pdf_sha256_local_observado"]):
        raise ValueError("Parecer anterior vinculado a outros dicionários")

    inspected = conferir_zip_recurso_local(RESOURCE_ID, zip_path)
    if prior.get("zip_sha256_local") != inspected["arquivo_pacote_sha256_local"]:
        raise ValueError("Parecer anterior vinculado a outro ZIP")
    meta = _resource(RESOURCE_ID)
    zip_local = Path(zip_path).expanduser()
    stat_before = zip_local.stat()
    with zipfile.ZipFile(zip_local, "r") as arc:
        members = arc.infolist()
        if (len(members) != 1
                or members[0].filename != meta["archive_filename"][:-4]):
            raise ValueError("Estrutura ZIP incompatível")
        with arc.open(members[0], "r") as stream:
            observed = _header_csv(stream, old)
    stat_after = zip_local.stat()
    if (stat_before.st_size != stat_after.st_size
            or stat_before.st_mtime_ns != stat_after.st_mtime_ns):
        raise ValueError("ZIP alterado durante leitura")

    documented = pdf["nomes_documentais"]
    extra = sorted(observed - documented)
    if (len(extra) > MAX_UNEXPECTED_NAMES
            or len(extra) != prior.get("quantidade_csv_fora_pdf_atual")
            or len(observed) != prior.get("n_campos_csv")
            or len(documented & observed) != prior.get("nome_comum_pdf_atual_csv")
            or sorted(documented - observed)
                 != prior.get("nomes_pdf_atual_ausentes_csv")):
        raise ValueError("Cabeçalho e parecer anterior não reconciliados")

    out = Path(destino).expanduser()
    if (out.suffix.lower() != ".json" or out.is_symlink()
            or not out.parent.is_dir() or out.parent.is_symlink()):
        raise ValueError("Destino local privado inválido")

    private = {
        "schema_version": PRIVATE_SCHEMA,
        "resource_id": RESOURCE_ID,
        "agravo": "DENG",
        "ano_rotulado_no_portal": 2024,
        "pdf_sha256_local": pdf["pdf_sha256_local"],
        "zip_sha256_local": inspected["arquivo_pacote_sha256_local"],
        "nomes_adicionais_csv_nao_documentados_no_pdf": extra,
        "quantidade": len(extra),
        "origem_nomes": "APENAS_PRIMEIRA_LINHA_CSV",
        "n_linhas_clinicas_lidas": 0,
        "revisao_independente": "PENDENTE",
        "nomes_publicaveis": False,
        "publicacao_autorizada": False,
        "aviso": (
            "ARQUIVO PRIVADO DO REVISOR. NAO enviar ao GitHub, ChatGPT ou "
            "servidores MCP. Verifique os nomes e seu significado apenas "
            "localmente, antes de solicitar classificacao documental. "
            "Nenhum valor de notificacao foi acessado."
        ),
    }
    fd = os.open(str(out), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(private, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except BaseException:
        try:
            out.unlink()
        except OSError:
            pass
        raise
    return {
        "quantidade": len(extra),
        "revisao": "PENDENTE",
        "dados_clinicos_lidos": False,
        "nomes_exibidos_no_terminal": False,
        "publicacao_autorizada": False,
    }
