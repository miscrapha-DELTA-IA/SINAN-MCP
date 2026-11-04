"""Offline versioned operator observations for Zika's documentary review.

This tool DOES NOT confer independent review, verify a PDF or read any
2024 clinical archive. It stores an explicitly user-entered documentary
observation in a *new*, private JSON; it cannot modify its source.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path

from .zika_pdf_private_review import (
    FIELD_CHOICES, ISSUE_CHOICES, _no_duplicate_keys, _private_path,
    _safe_note, diagnosticar_dados_pacote_revisao_zika,
    validar_pacote_revisao_zika,
)

MAX_BYTES = 120_000


def registrar_observacao_documental_zika(
    arquivo: str | Path, saida: str | Path, *, tipo: str,
    campo: str, avaliacao: str, nota: str,
) -> dict:
    """Create a new checklist version; no status can authenticate approval.

    Deliberately require a descriptive note for any non-PENDENTE decision
    so a manual statement has an auditable page/ambiguity reference.
    """
    source = _private_path(arquivo, creating=False)
    target = _private_path(saida, creating=True)
    if (source.resolve() == target.resolve()
            or source.parent.resolve() != target.parent.resolve()):
        raise ValueError("Saida deve ser uma nova versao na mesma pasta privada")
    if (type(tipo) is not str or tipo not in ("campo", "ressalva")
            or type(campo) is not str or len(campo) > 32
            or type(avaliacao) is not str or type(nota) is not str
            or not _safe_note(nota)
            or (avaliacao != "PENDENTE" and not nota.strip())):
        raise ValueError("Observacao documental invalida ou sem justificativa")

    valid_choices = FIELD_CHOICES if tipo == "campo" else ISSUE_CHOICES
    if avaliacao not in valid_choices:
        raise ValueError("Estado documental nao permitido para o tipo escolhido")

    with source.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES or len(raw) < 1:
        raise ValueError("Arquivo de origem privado fora do limite")
    try:
        base = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("Pacote de origem privado malformado") from None
    validar_pacote_revisao_zika(base)

    revised = deepcopy(base)
    section = "campos" if tipo == "campo" else "ressalvas"
    matches = [row for row in revised[section] if row["campo"] == campo]
    if len(matches) != 1:
        raise ValueError("Campo ou ressalva nao reconhecido")
    matches[0]["avaliacao_declarada_operador"] = avaliacao
    matches[0]["nota_documental"] = nota
    validar_pacote_revisao_zika(revised)

    # Prevalidate output size before exclusive file creation. Never mutate
    # the original, overwrite a previous revision, or print personal notes.
    payload = (json.dumps(revised, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(payload) > MAX_BYTES:
        raise ValueError("Nova versao excede limite do pacote privado")
    fd = os.open(str(target), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
    except BaseException:
        try:
            target.unlink()
        except OSError:
            pass
        raise
    return diagnosticar_dados_pacote_revisao_zika(revised)
