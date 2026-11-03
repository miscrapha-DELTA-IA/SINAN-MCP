"""DENG/2024 quality/cohort PROTOCOL candidate (metadata only, no records).

Creates a private checklist of specific scientific quality questions grounded in
previous local audit SHA-256 digests. It DOES NOT assess actual completeness,
case definitions, dates, unique patients, denominators or code validity.

No ZIP/CSV/DB/PySUS/network/MCP access. No publication, no roadmap quality
gate promotion. This prevents a mere plan from masquerading as clinical QC.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .local_annual_source_evidence import (
    _crosswalk, _safe_json_file, _validate_dossier, MAX_DOSSIER,
)
from .local_dengue_dictionary_crosswalk import RESOURCE_ID
from .roadmap_readiness import (
    SHA, load_checklist, avaliar_checklist,
)

PLAN_SCHEMA = "sinan-private-dengue-quality-cohort-protocol-v1"
CHECKPOINTS = {
    "escopo_unidade_observacional": (
        "Definir notificacao, episodio, pessoa, caso, inclusoes e exclusoes "
        "antes de contar ou deduplicar"
    ),
    "reconciliacao_arquivo_projecao": (
        "Conferir linhas de dados do arquivo contra registros realmente "
        "importados, perdas de linhas e regras de conversao"
    ),
    "completude_e_ignorados": (
        "Inspecionar nulos, codigos ignorados e faltantes por campo com "
        "supressao de contagens sensiveis"
    ),
    "dominios_codigos_clinicos": (
        "Resolver CLASSI_FIN, CLINC_CHIK/CLINIC_CHIK, UF e outros "
        "dominios e tipos antes de validar valores"
    ),
    "consistencia_temporal": (
        "Definir ano do arquivo versus data de notificacao, sintomas, "
        "diagnostico, encerramento e data de corte"
    ),
    "territorio_geografia": (
        "Distinguir UF de residencia, notificacao, investigacao "
        "e avaliar municipio, valores divergentes e desconhecidos"
    ),
    "unicidade_e_duplicacoes": (
        "Nao confundir tuplas de atributos iguais com notificacoes "
        "repetidas ou individuos duplicados; usar criterio revisado"
    ),
    "reconciliacao_tabnet": (
        "Comparar ao TabNet/boletim de referencia da mesma versao, "
        "definicao de caso, ano, estratos e filtro, explicando diferencas"
    ),
    "risco_divulgacao_resultados": (
        "Avaliar vazamento por tabulacoes pequenas, subgrupos "
        "e composicao; resultados QC permanecem privados"
    ),
}


def _same_private_directory(*paths: str | Path) -> bool:
    p = [Path(path).expanduser() for path in paths]
    return len({x.parent.resolve() for x in p}) == 1


def preparar_plano_qualidade_dengue_local(
    checklist_path: str | Path,
    parecer_path: str | Path,
    dossie_path: str | Path,
    destino: str | Path,
) -> dict:
    """Generate an UNAPPROVED plan, not a data-quality result."""
    if not _same_private_directory(checklist_path, parecer_path, dossie_path, destino):
        raise ValueError("Todos os documentos devem permanecer na mesma pasta privada")

    checklist = load_checklist(checklist_path)
    sc = checklist["scope"]
    if sc != {
        "agravo": "DENG", "ano_do_arquivo": 2024, "resource_id": RESOURCE_ID
    }:
        raise ValueError("Escopo diferente do recurso DENG/2024 curado")
    if checklist["gates"]["qualidade_coorte"] != {
        "situacao": "PENDENTE", "evidencia_sha256_local": None
    }:
        raise ValueError("Gate qualidade_coorte nao esta pendente")

    previous, report_digest = _crosswalk(parecer_path)
    source, source_raw = _safe_json_file(dossie_path, MAX_DOSSIER)
    _validate_dossier(source)
    source_digest = hashlib.sha256(source_raw).hexdigest()
    expected_dict = {
        "situacao": "EVIDENCIA_LOCAL_NAO_VALIDADA",
        "evidencia_sha256_local": report_digest,
    }
    expected_source = {
        "situacao": "EVIDENCIA_LOCAL_NAO_VALIDADA",
        "evidencia_sha256_local": source_digest,
    }
    if (checklist["gates"]["dicionario_esquema"] != expected_dict
            or checklist["gates"]["fonte_agravo_ano"] != expected_source):
        raise ValueError("Checklist nao concilia com os dois pareceres locais")
    if (source["crosswalk_pending_sha256_local"] != report_digest
            or source["zip_sha256_local"] != previous["zip_sha256_local"]
            or source["pdf_documental_sha256_local"]
                != previous["pdf_atual_sha256_local"]):
        raise ValueError("Dossie de fonte e parecer documental nao conciliados")

    plan = {
        "schema_version": PLAN_SCHEMA,
        "scope": sc,
        "parecer_esquema_sha256_local": report_digest,
        "dossie_fonte_sha256_local": source_digest,
        "zip_sha256_local": source["zip_sha256_local"],
        "quality_checkpoints": {
            key: {"status": "PENDENTE", "definicao_de_aceite": detail}
            for key, detail in CHECKPOINTS.items()
        },
        "unidade_observacional": "NAO_DEFINIDA",
        "coorte_definida_independentemente": False,
        "revisao_clinica_independente": "PENDENTE",
        "data_cutoff_confirmada": False,
        "qualidade_dados_clinicos_auditada": False,
        "n_linhas_clinicas_lidas": 0,
        "indicadores_reais_calculados": False,
        "apto_analise_ou_publicacao": False,
        "roadmap_quality_gate_alterado": False,
        "status": "PLANO_PRIVADO_NAO_VALIDADO",
        "aviso": (
            "Este e um plano de auditoria, NAO um resultado de controle "
            "de qualidade. Nunca transformar plano em qualidade validada. "
            "A origem do ZIP, coorte, padroes clinicos e riscos de divulgacao "
            "ainda requerem verificacao independente."
        ),
    }
    out = Path(destino).expanduser()
    if (out.is_symlink() or out.suffix.lower() != ".json"
            or not out.parent.is_dir() or out.parent.is_symlink()):
        raise ValueError("Destino privado JSON invalido")
    fd = os.open(str(out), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except BaseException:
        try:
            out.unlink()
        except OSError:
            pass
        raise
    diagnostic = avaliar_checklist(checklist)
    return {
        "agravo": "DENG",
        "ano_do_arquivo": 2024,
        "checkpoints_pendentes": len(CHECKPOINTS),
        "frentes_roadmap_ainda_pendentes": diagnostic["n_frentes_pendentes"],
        "qualidade_coorte_concluida": False,
        "dados_clinicos_lidos": False,
        "publicacao_autorizada": False,
        "status": "PLANO_PRIVADO_NAO_VALIDADO",
    }
