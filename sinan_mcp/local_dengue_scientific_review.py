"""DENG/2024: versioned SCIENTIFIC REVIEW REQUEST, not a data release.

Administrative, offline, metadata-only. This module reads *only* the previous
local quality-plan JSON and the fully synthetic quality-rehearsal JSON. It
cannot read ZIP, CSV, PDF patient data, SQLite, network sources, or MCP tools.

The generated research questions do not authorize use of health data.
No software validation here can authenticate a reviewer or a ministry file.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .local_dengue_dictionary_crosswalk import RESOURCE_ID
from .local_dengue_quality_protocol import CHECKPOINTS
from .roadmap_readiness import SHA, _strict_json_pairs
from .synthetic_dengue_csv_audit import (
    SCHEMA as SIMULATION_SCHEMA,
    _plan_digest,
    _fixture,
    _scan_marked_synthetic_csv,
)

SCHEMA = "sinan-private-dengue-scientific-review-request-v1"
MAX_DOCUMENT = 32_768
DECISIONS = {
    "classi_fin": {
        "questao": (
            "Qual edicao de dicionario, sistema e regra de CLASSI_FIN se "
            "aplica exatamente ao arquivo CSV DENG/2024?"
        ),
        "hipotese_documental": (
            "Nota historica 59/2016 traz 5,10,11,12,13; PDF recente "
            "apresenta tabela 1,2,8 e regras com 11,12,13. "
            "Nenhum dominio se aplica automaticamente ao CSV 2024."
        ),
        "evidencia_necessaria": (
            "Parecer epidemiologico sobre dicionario/versao de exportacao, "
            "tipos e codigos; confrontacao de referencia oficial."
        ),
    },
    "clinc_chik": {
        "questao": (
            "CLINC_CHIK exportado em 2024 e semanticamente equivalente "
            "ao CLINIC_CHIK do documento, ou nao?"
        ),
        "hipotese_documental": (
            "Uma letra diverge; documento descreve campo de apresentacao "
            "clinica condicional a chikungunya. Alias NAO autorizado."
        ),
        "evidencia_necessaria": (
            "Layout oficial da distribuicao, regra de preenchimento, "
            "versao e revisao clinica independente."
        ),
    },
    "uf": {
        "questao": (
            "Qual e a origem/semantica da coluna adicional UF, distinta "
            "dos campos de UF de residencia e notificacao?"
        ),
        "hipotese_documental": (
            "Identificador extra do cabecalho; pode ser derivado ou "
            "metadado de exportacao, mas nao ha equivalencia demonstrada."
        ),
        "evidencia_necessaria": (
            "Contrato oficial do ETL/exportacao e transformacoes "
            "territoriais, sem inferir SG_UF ou SG_UF_NOT."
        ),
    },
    "unidade_observacional": {
        "questao": (
            "O que cada linha representa e como diferenciar notificacao, "
            "episodio, caso e pessoa, incluindo criterios de exclusao?"
        ),
        "hipotese_documental": (
            "Linhas de CSV nao demonstram unicidade de individuos, "
            "casos confirmados ou incidencia."
        ),
        "evidencia_necessaria": (
            "Protocolo de coorte, fluxograma, criterio de unidade e "
            "parecer de analista de vigilancia."
        ),
    },
    "janela_temporal": {
        "questao": (
            "Qual data define o ano 2024, a janela de coorte e a data "
            "de corte da versao da distribuicao?"
        ),
        "hipotese_documental": (
            "Ano no titulo do arquivo nao prova inclusao por sintomas, "
            "notificacao, confirmacao ou consolidacao final."
        ),
        "evidencia_necessaria": (
            "Regra temporal documentada, versao do snapshot, data de "
            "extracao, regras para atrasos e registros tardios."
        ),
    },
    "indicador_denominador": {
        "questao": (
            "Qual numerador, denominador, definicao de caso, fonte e "
            "metodo de reconciliacao externa se aplica a cada indicador?"
        ),
        "hipotese_documental": (
            "O CSV de notificacoes nao substitui populacao em risco ou "
            "um indicador oficial com janela/filtros diferentes."
        ),
        "evidencia_necessaria": (
            "Protocolo de indicador, referencia TabNet/boletim da mesma "
            "versao/corte e justificativa de divergencias."
        ),
    },
    "privacidade_e_acesso": {
        "questao": (
            "Quem pode custodiar, revisar e processar a base real e "
            "como impedir reidentificacao entre releases agregados?"
        ),
        "hipotese_documental": (
            "Limiares de celula e checksums isolados nao certificam "
            "anonimizacao nem autorizam acesso publico."
        ),
        "evidencia_necessaria": (
            "Base legal, protocolo institucional/etico se aplicavel, "
            "avaliacao de privacidade por composicao e plano de acesso."
        ),
    },
}
SIMULATION_KEYS = frozenset({
    "schema_version", "agravo_apenas_de_contexto",
    "ano_arquivo_apenas_de_contexto", "plano_privado_sha256_local",
    "origem_dados", "referencia_csv_real_lida", "caminhos_csv_ou_zip_aceitos",
    "registros_reais_lidos", "verificacoes_sinteticas",
    "cenarios_de_entrada_invalida_recusados", "checkpoints_cientificos_validados",
    "qualidade_coorte_homologada", "roadmap_alterado",
    "publicacao_autorizada", "status", "aviso",
})
MANIFEST_KEYS = frozenset({
    "schema_version", "scope", "plano_qualidade_sha256_local",
    "simulacao_sintetica_sha256_local", "zip_sha256_local",
    "questoes_para_revisao_independente", "checkpoints_qualidade_pendentes",
    "revisores_autenticados", "parecer_epidemiologico",
    "parecer_privacidade_institucional", "evidencia_oficial_2024_autenticada",
    "aliases_de_campos_aprovados", "dominios_clinicos_validados",
    "coorte_e_unidade_observacional_validadas",
    "indicadores_reais_calculados", "registros_reais_lidos",
    "qualidade_coorte_homologada", "roadmap_alterado",
    "autorizacao_uso_real", "publicacao_autorizada", "status", "aviso",
})


def _read_json_private(path: str | Path) -> tuple[dict, bytes]:
    p = Path(path).expanduser()
    if (p.is_symlink() or not p.is_file() or p.suffix.lower() != ".json"
            or not 2 <= p.stat().st_size <= MAX_DOCUMENT):
        raise ValueError("Documento privado ausente ou fora do limite")
    raw = p.read_bytes()
    if len(raw) > MAX_DOCUMENT:
        raise ValueError("Documento privado excede limite")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_json_pairs)
    except (UnicodeError, ValueError):
        raise ValueError("Documento privado JSON recusado") from None
    if not isinstance(obj, dict):
        raise ValueError("Documento privado requer objeto JSON")
    return obj, raw


def _simulation_digest(path: str | Path, expected_plan_hash: str) -> str:
    simulation, raw = _read_json_private(path)
    expected = {
        "schema_version": SIMULATION_SCHEMA,
        "agravo_apenas_de_contexto": "DENG",
        "ano_arquivo_apenas_de_contexto": 2024,
        "plano_privado_sha256_local": expected_plan_hash,
        "origem_dados": "FIXTURE_INTERNA_100_POR_CENTO_SINTETICA",
        "referencia_csv_real_lida": False,
        "caminhos_csv_ou_zip_aceitos": False,
        "registros_reais_lidos": 0,
        "cenarios_de_entrada_invalida_recusados": 4,
        "checkpoints_cientificos_validados": 0,
        "qualidade_coorte_homologada": False,
        "roadmap_alterado": False,
        "publicacao_autorizada": False,
        "status": "SIMULACAO_TECNICA_SEM_DADOS_CLINICOS",
    }
    if (set(simulation) != SIMULATION_KEYS
            or any(
                type(simulation.get(key)) is not type(value)
                or simulation[key] != value
                for key, value in expected.items()
            )
            or simulation.get("verificacoes_sinteticas")
                != _scan_marked_synthetic_csv(_fixture())
            or not isinstance(simulation.get("aviso"), str)
            or not simulation["aviso"].startswith("Todos os numeros neste arquivo")):
        raise ValueError("Simulacao incompatível, adulterada ou nao sintética")
    return hashlib.sha256(raw).hexdigest()


def validate_review_packet(doc: object) -> dict:
    if (not isinstance(doc, dict) or set(doc) != MANIFEST_KEYS
            or doc["schema_version"] != SCHEMA
            or doc["scope"] != {
                "agravo": "DENG", "ano_do_arquivo": 2024,
                "resource_id": RESOURCE_ID,
            }
            or doc["checkpoints_qualidade_pendentes"] != len(CHECKPOINTS)
            or doc["revisores_autenticados"] != 0
            or doc["parecer_epidemiologico"] != "PENDENTE"
            or doc["parecer_privacidade_institucional"] != "PENDENTE"
            or doc["evidencia_oficial_2024_autenticada"] is not False
            or doc["aliases_de_campos_aprovados"] is not False
            or doc["dominios_clinicos_validados"] is not False
            or doc["coorte_e_unidade_observacional_validadas"] is not False
            or doc["indicadores_reais_calculados"] is not False
            or type(doc["registros_reais_lidos"]) is not int
            or doc["registros_reais_lidos"] != 0
            or doc["qualidade_coorte_homologada"] is not False
            or doc["roadmap_alterado"] is not False
            or doc["autorizacao_uso_real"] is not False
            or doc["publicacao_autorizada"] is not False
            or doc["status"] != "PEDIDO_DE_REVISAO_NAO_HOMOLOGADO"):
        raise ValueError("Pacote cientifico com escopo ou autorizacao invalida")
    for key in (
        "plano_qualidade_sha256_local", "simulacao_sintetica_sha256_local",
        "zip_sha256_local",
    ):
        sha = doc[key]
        if not isinstance(sha, str) or not SHA.fullmatch(sha):
            raise ValueError("SHA-256 do pacote cientifico invalido")
    decisions = doc["questoes_para_revisao_independente"]
    if not isinstance(decisions, dict) or set(decisions) != set(DECISIONS):
        raise ValueError("Lista de decisoes cientificas incompleta")
    for key, template in DECISIONS.items():
        if decisions[key] != {
            **template,
            "situacao": "PENDENTE",
            "equivalencia_validada": False,
            "evidencia_independente_autenticada": False,
        }:
            raise ValueError("Decisao cientifica adulterada ou declarada validada")
    if (not isinstance(doc["aviso"], str)
            or doc["aviso"] != (
                "Perguntas para revisao externa; nao sao dados SINAN, "
                "parecer independente, certificacao LGPD, permissao de "
                "acesso ou publicacao."
            )):
        raise ValueError("Aviso obrigatorio do pacote cientifico invalido")
    return doc


def preparar_pacote_revisao_dengue_local(
    plano_path: str | Path,
    simulacao_path: str | Path,
    destino: str | Path,
) -> dict:
    paths = [Path(p).expanduser() for p in (plano_path, simulacao_path, destino)]
    if len({p.parent.resolve() for p in paths}) != 1:
        raise ValueError("Artefatos devem estar na mesma pasta privada")
    plan_hash = _plan_digest(plano_path)
    plan, raw = _read_json_private(plano_path)
    if hashlib.sha256(raw).hexdigest() != plan_hash:
        raise ValueError("Plano mudou durante a verificacao")
    simulation_hash = _simulation_digest(simulacao_path, plan_hash)
    zip_hash = plan["zip_sha256_local"]
    if not isinstance(zip_hash, str) or not SHA.fullmatch(zip_hash):
        raise ValueError("Hash ZIP do plano invalido")
    doc = {
        "schema_version": SCHEMA,
        "scope": {
            "agravo": "DENG", "ano_do_arquivo": 2024,
            "resource_id": RESOURCE_ID,
        },
        "plano_qualidade_sha256_local": plan_hash,
        "simulacao_sintetica_sha256_local": simulation_hash,
        "zip_sha256_local": zip_hash,
        "questoes_para_revisao_independente": {
            key: {
                **entry,
                "situacao": "PENDENTE",
                "equivalencia_validada": False,
                "evidencia_independente_autenticada": False,
            } for key, entry in DECISIONS.items()
        },
        "checkpoints_qualidade_pendentes": len(CHECKPOINTS),
        "revisores_autenticados": 0,
        "parecer_epidemiologico": "PENDENTE",
        "parecer_privacidade_institucional": "PENDENTE",
        "evidencia_oficial_2024_autenticada": False,
        "aliases_de_campos_aprovados": False,
        "dominios_clinicos_validados": False,
        "coorte_e_unidade_observacional_validadas": False,
        "indicadores_reais_calculados": False,
        "registros_reais_lidos": 0,
        "qualidade_coorte_homologada": False,
        "roadmap_alterado": False,
        "autorizacao_uso_real": False,
        "publicacao_autorizada": False,
        "status": "PEDIDO_DE_REVISAO_NAO_HOMOLOGADO",
        "aviso": (
            "Perguntas para revisao externa; nao sao dados SINAN, "
            "parecer independente, certificacao LGPD, permissao de "
            "acesso ou publicacao."
        ),
    }
    validate_review_packet(doc)
    out = paths[-1]
    if (out.is_symlink() or out.suffix.lower() != ".json"
            or not out.parent.is_dir() or out.parent.is_symlink()):
        raise ValueError("Destino JSON privado invalido")
    fd = os.open(str(out), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except BaseException:
        try:
            out.unlink()
        except OSError:
            pass
        raise
    return resumo_pacote_cientifico(doc)


def resumo_pacote_cientifico(doc: object) -> dict:
    obj = validate_review_packet(doc)
    return {
        "agravo": "DENG",
        "ano": 2024,
        "questoes_cientificas_pendentes": len(DECISIONS),
        "checkpoints_qualidade_pendentes": obj["checkpoints_qualidade_pendentes"],
        "revisores_autenticados": 0,
        "dados_reais_lidos": 0,
        "uso_real_autorizado": False,
        "publicacao_autorizada": False,
        "status": obj["status"],
    }


def diagnosticar_pacote_cientifico_local(path: str | Path) -> dict:
    obj, _ = _read_json_private(path)
    return resumo_pacote_cientifico(obj)
