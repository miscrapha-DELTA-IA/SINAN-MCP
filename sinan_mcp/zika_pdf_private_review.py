"""Prepare and diagnose a private DOCUMENTARY Zika peer-review checklist.

A checklist is neither a signed independent scientific opinion nor a
release/case-data authorization. All assertions of independent approval
are immutable False. The operator can record field-by-field documentary
notes, but no software action can turn these into verified peer review.

No PDF, ZIP, 2024 record, database, network, or public MCP is used.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .zika_pdf_37_field_curation import carregar_transcricao_zika_pdf

SCHEMA = "sinan-zika-pdf-37-field-private-review-checklist-v1"
FIELD_CHOICES = frozenset({
    "PENDENTE", "CONFERIDO_MANUALMENTE",
    "DIVERGENCIA_DOCUMENTAL", "ILEGIVEL",
})
ISSUE_CHOICES = frozenset({
    "PENDENTE", "OBSERVACAO_DOCUMENTADA", "DIVERGENCIA_IDENTIFICADA",
})
STATIC_FLAGS = {
    "revisao_independente_autenticada": False,
    "assinatura_de_parecer_verificada": False,
    "dicionario_aplicavel_a_2024_validado": False,
    "esquema_arquivo_2024_conferido": False,
    "registros_clinicos_acessados": False,
    "indicadores_homologados": 0,
    "publicacao_autorizada": False,
}
BASE_KEYS = frozenset({
    "schema_version", "agravo", "ano_do_arquivo_pretendido",
    "recurso_uuid_documental", "url_pdf_publico",
    "hash_do_catalogo_versionado_nao_hash_oficial_pdf",
    "tipo_de_pacote", "campos", "ressalvas",
}) | frozenset(STATIC_FLAGS)
FIELD_KEYS = frozenset({
    "seq", "campo", "pagina_pdf", "tipo_documental",
    "dominio_descritor", "codigos_citados", "significado_resumido",
    "avaliacao_declarada_operador", "nota_documental",
})
ISSUE_KEYS = frozenset({
    "campo", "motivo_documental", "avaliacao_declarada_operador",
    "nota_documental",
})


def _no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Chave repetida no pacote local")
        result[key] = value
    return result


def _safe_note(value):
    # Notes are private and never echoed by the program.
    return (isinstance(value, str) and len(value) <= 600
            and all((ord(c) >= 32 or c == "\n") and ord(c) != 127
                    for c in value))


def _build_checklist():
    source = carregar_transcricao_zika_pdf()
    report = {
        "schema_version": SCHEMA,
        "agravo": "ZIKA",
        "ano_do_arquivo_pretendido": 2024,
        "recurso_uuid_documental": (
            "58038262-c745-46ea-979b-8727eb08ec5c"
        ),
        "url_pdf_publico": source["source_pdf"],
        "hash_do_catalogo_versionado_nao_hash_oficial_pdf": (
            source["local_catalog_sha256_not_official_pdf_hash"]
        ),
        "tipo_de_pacote": "RASCUNHO_PRIVADO_DE_CONFERENCIA_NAO_AUTENTICADO",
        "campos": [
            {
                "seq": row["seq"],
                "campo": row["campo"],
                "pagina_pdf": row["pagina_pdf"],
                "tipo_documental": row["tipo_documental"],
                "dominio_descritor": row["dominio_descritor"],
                "codigos_citados": list(row["codigos_citados"]),
                "significado_resumido": row["significado_resumido"],
                "avaliacao_declarada_operador": "PENDENTE",
                "nota_documental": "",
            }
            for row in source["documentary_field_rows"]
        ],
        "ressalvas": [
            {
                "campo": row["campo"],
                "motivo_documental": row["motivo"],
                "avaliacao_declarada_operador": "PENDENTE",
                "nota_documental": "",
            }
            for row in source["issues_requiring_independent_review"]
        ],
    }
    report.update(STATIC_FLAGS)
    return report


def validar_pacote_revisao_zika(pdf_review: object) -> dict:
    """Validate operator declarations; NEVER authenticate an independent reviewer."""
    expected = _build_checklist()
    if not isinstance(pdf_review, dict) or set(pdf_review) != BASE_KEYS:
        raise ValueError("Estrutura do pacote de revisao documental invalida")
    for key in BASE_KEYS - {"campos", "ressalvas"}:
        if type(pdf_review[key]) is not type(expected[key]) or (
                pdf_review[key] != expected[key]):
            raise ValueError("Identidade ou bloqueios cientificos divergentes")
    rows = pdf_review["campos"]
    if not isinstance(rows, list) or len(rows) != 37:
        raise ValueError("Checklist precisa dos 37 campos")
    for item, original in zip(rows, expected["campos"]):
        if not isinstance(item, dict) or set(item) != FIELD_KEYS:
            raise ValueError("Linha documental incompleta")
        for key in FIELD_KEYS - {
                "avaliacao_declarada_operador", "nota_documental"}:
            if type(item[key]) is not type(original[key]) or (
                    item[key] != original[key]):
                raise ValueError("Origem, pagina, tipo ou dominio documental alterado")
        status = item["avaliacao_declarada_operador"]
        note = item["nota_documental"]
        if (type(status) is not str or status not in FIELD_CHOICES
                or not _safe_note(note)
                or (status in ("DIVERGENCIA_DOCUMENTAL", "ILEGIVEL")
                    and not note.strip())):
            raise ValueError("Avaliacao documental de campo invalida")
    issues = pdf_review["ressalvas"]
    if not isinstance(issues, list) or len(issues) != 7:
        raise ValueError("Todas as sete ressalvas devem permanecer listadas")
    for item, original in zip(issues, expected["ressalvas"]):
        if not isinstance(item, dict) or set(item) != ISSUE_KEYS:
            raise ValueError("Ressalva documental incompleta")
        for key in ("campo", "motivo_documental"):
            if item[key] != original[key]:
                raise ValueError("Ressalva original alterada")
        status = item["avaliacao_declarada_operador"]
        note = item["nota_documental"]
        if (type(status) is not str or status not in ISSUE_CHOICES
                or not _safe_note(note)
                or (status != "PENDENTE" and not note.strip())):
            raise ValueError("Tratamento declarado de ressalva invalido")
    return pdf_review


def _private_path(file_path, *, creating):
    path = Path(file_path).expanduser()
    if (path.suffix.lower() != ".json" or path.is_symlink()
            or not path.parent.is_dir() or path.parent.is_symlink()):
        raise ValueError("Caminho de pacote privado invalido")
    parent = path.parent.resolve()
    # Refuse creating or inspecting private review notes in git worktrees.
    if any((entry / ".git").exists() for entry in (parent, *parent.parents)):
        raise ValueError("Nao armazenar parecer privado dentro do repositorio Git")
    if not creating:
        if not path.is_file() or not 1 <= path.stat().st_size <= 120_000:
            raise ValueError("Pacote privado ausente ou excede limite")
    return path


def criar_pacote_revisao_zika(destino) -> dict:
    """O_EXCL 0600 private file. Never overwrite an operator's review."""
    out = _private_path(destino, creating=True)
    data = validar_pacote_revisao_zika(_build_checklist())
    fd = os.open(str(out), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except BaseException:
        try:
            out.unlink()
        except OSError:
            pass
        raise
    return diagnosticar_dados_pacote_revisao_zika(data)


def diagnosticar_dados_pacote_revisao_zika(data) -> dict:
    doc = validar_pacote_revisao_zika(data)
    counts = {name: sum(row["avaliacao_declarada_operador"] == name
                        for row in doc["campos"]) for name in sorted(FIELD_CHOICES)}
    caveats = {name: sum(row["avaliacao_declarada_operador"] == name
                         for row in doc["ressalvas"]) for name in sorted(ISSUE_CHOICES)}
    return {
        "schema_version": "sinan-zika-private-review-diagnostic-v1",
        "campos_documentais_total": 37,
        "campos_por_declaracao_do_operador": counts,
        "ressalvas_documentais_total": 7,
        "ressalvas_por_declaracao_do_operador": caveats,
        "notas_privadas_exibidas": False,
        "hash_do_catalogo_publico_validado_localmente": True,
        "hash_oficial_pdf_autenticado": False,
        "parecer_independente_autenticado": False,
        "assinatura_revisor_verificada": False,
        "campos_2024_efetivamente_conferidos": 0,
        "topicos_cientificos_pendentes": 10,
        "indicadores_homologados": 0,
        "publicacao_autorizada": False,
        "status": "CHECKLIST_OPERADOR_SEM_PARECER_INDEPENDENTE",
    }


def diagnosticar_pacote_revisao_zika(arquivo) -> dict:
    path = _private_path(arquivo, creating=False)
    try:
        # Limit before decoding. Never print untrusted JSON, names or notes.
        with path.open("rb") as stream:
            raw = stream.read(120_001)
        if not 1 <= len(raw) <= 120_000:
            raise ValueError("Pacote privado fora do limite")
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
        return diagnosticar_dados_pacote_revisao_zika(data)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("Pacote de revisao JSON invalido") from None
