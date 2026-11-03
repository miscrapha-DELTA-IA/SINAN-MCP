"""Offline conservative composition check for existing approved release packages.

This does not approve, sign, upload, deploy or otherwise publish releases.
No differential privacy guarantee, and no comparison to outside publications.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .aggregate_contract import load_approved_release

HEX64 = re.compile(r"[a-f0-9]{64}\Z")


def assess_release_set(packages: Iterable[tuple[str | Path, str]]) -> dict:
    """Fail closed for overlapping disease/UF across *any* file-year or dimension.

    This is deliberately stricter than checking marginal cells: re-releasing
    different versions, dimensions or years can enable cross-table inference.
    Other combinations still require independent disclosure assessment.
    """
    inputs = list(packages)
    if not 1 <= len(inputs) <= 100:
        raise ValueError("Informe entre 1 e 100 pacotes existentes")
    seen_files = set()
    seen_partitions = {}
    scopes = []
    for path, sha in inputs:
        source = Path(path).expanduser()
        if source.is_symlink() or not source.is_file():
            raise ValueError("Pacote ausente ou link simbólico")
        canonical = str(source.resolve())
        if canonical in seen_files:
            raise ValueError("Arquivo de release repetido")
        seen_files.add(canonical)
        if not isinstance(sha, str) or not HEX64.fullmatch(sha):
            raise ValueError("SHA-256 de aprovação inválido")
        approved = load_approved_release(source, sha)
        candidate = approved["candidate"]
        scope = candidate["scope"]
        key = (scope["agravo"], scope["uf"])
        if key in seen_partitions:
            raise ValueError(
                "RISCO DE COMPOSIÇÃO: dois releases do mesmo agravo e UF, "
                "inclusive em anos, dimensões ou versões diferentes. "
                "Requer avaliação externa; combinação bloqueada nesta política."
            )
        seen_partitions[key] = True
        scopes.append({
            "agravo": scope["agravo"],
            "uf": scope["uf"],
            "ano_do_arquivo": scope["ano_do_arquivo"],
            "dimensao": scope["dimensao"],
            "sha256_pacote": sha,
        })
    return {
        "schema_version": "sinan-release-composition-v1",
        "pacotes_validados_estruturalmente": len(scopes),
        "escopos": scopes,
        "sobreposicao_direta_detectada": False,
        "revisao_de_composicao_externa_concluida": False,
        "publicacao_autorizada": False,
        "garantia_de_anonimizacao": False,
        "aviso": (
            "Conjunto sem sobreposição agravo/UF dentro dos pacotes fornecidos. "
            "Isto NÃO examina publicações anteriores ou externas, riscos de "
            "inferência, pareceres reais, condições de acesso ou base legal. "
            "Não libera nenhum agregado para a internet."
        ),
    }
