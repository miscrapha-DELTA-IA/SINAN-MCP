"""Conservative disease-year documentary crosswalk plan, no patient data.

This is NOT a field-level schema comparison. No clinical file, schema
header, ZIP, database, network endpoint, or institutional data is read.
"""
from __future__ import annotations

from typing import Any

from .official_annual_resources import consultar_recursos_oficiais_ano
from .shared_notification_documents import diagnosticar_documentacao_transversal
from .year_evidence_registry import consultar_evidencia_agravo_ano
from .zika_resource_identity import confrontar_snapshot_portal_zika_2024

SCHEMA = "sinan-2024-documentary-crosswalk-plan-v1"
SUPPORTED = frozenset(("ZIKA", "SIFA"))
# These are review topics, NOT claims about physical columns in the 2024 file.
REVIEW_TOPICS = (
    ("identidade_do_recurso", "Confirmar URL/UUID/nome de arquivo, escopo nacional e data de corte"),
    ("sistema_origem", "Confirmar sistema de entrada, módulo e eventuais migrações"),
    ("instrumento_notificacao", "Conferir modelo de ficha aplicável e sua revisão"),
    ("campos_comuns", "Comparar nomes, tipos e códigos dos campos gerais sem ler linhas clínicas"),
    ("campos_proprios", "Determinar se existem campos adicionais por agravo e documentar fonte"),
    ("semantica_de_casos", "Revisar definição de caso e critérios de exclusão sem calcular indicadores"),
    ("temporalidade", "Distinguir data de notificação, início dos sintomas e ano do arquivo"),
    ("qualidade_e_duplicidades", "Planejar verificação de completude e duplicidades em ambiente autorizado"),
    ("privacidade", "Avaliar finalidade, minimização, supressão e risco cumulativo de divulgação"),
    ("revisao_independente", "Exigir parecer epidemiológico e decisão de governança antes de publicar"),
)


def planejar_confronto_documental_2024(agravo: str) -> dict[str, Any]:
    """Prepare a reproducible, all-pending review map for ZIKA/SIFA in 2024."""
    if type(agravo) is not str or agravo not in SUPPORTED:
        raise ValueError("Use ZIKA ou SIFA em maiúsculas; nenhum ano é inferido")
    year = 2024
    transversal = diagnosticar_documentacao_transversal(year, agravo)["registros"][0]
    official = consultar_recursos_oficiais_ano(agravo, year)
    disease_doc = consultar_evidencia_agravo_ano(agravo, year)
    n = official["quantidade_recursos_catalogados"]
    if (disease_doc["link_dicionario_oficial_localizado"]
            or transversal["compatibilidade_com_arquivo_anual_demonstrada"]
            or official["arquivo_binario_verificado"]
            or official["publicacao_autorizada"]):
        raise ValueError("Confronto documental exige entrada não homologada")
    sources = [
        {
            "id": "dicionario_geral_2018",
            "natureza": "dicionario_compartilhado_historico",
            "url": transversal["url_dicionario_compartilhado"],
            "aplica_automaticamente_ao_arquivo_2024": False,
        },
    ]
    if agravo == "SIFA":
        sources.extend((
            {
                "id": "guia_ministerial_2024",
                "natureza": "orientacao_oficial_do_instrumento_de_notificacao",
                "url": transversal["url_guia_ministerial_2024"],
                "pagina_impressa": 506,
                "aplica_automaticamente_ao_arquivo_2024": False,
            },
            {
                "id": "nota_ms_2017",
                "natureza": "orientacao_historica_de_ficha_de_notificacao",
                "url": transversal["url_nota_informativa_ministerial_2017"],
                "aplica_automaticamente_ao_arquivo_2024": False,
            },
        ))
    else:
        sources.append({
            "id": "pagina_oficial_zika",
            "natureza": "ligacao_direta_ao_dicionario_geral_na_pagina_do_agravo",
            "url": transversal["pagina_oficial"],
            "aplica_automaticamente_ao_arquivo_2024": False,
        })
    sources.extend({
        "id": "distribuicao_catalogada_" + str(i + 1),
        "natureza": "ponteiro_publico_de_arquivo_nao_verificado",
        "url": row["pagina_recurso_oficial"],
        "aplica_automaticamente_ao_arquivo_2024": False,
    } for i, row in enumerate(official["recursos"]))
    if any(source["url"] is None for source in sources):
        raise ValueError("Falta proveniência para a referência documental")
    # This narrows one documentary sub-question for ZIKA. The full
    # resource-identity topic still requires provenance, cutoff and release
    # context, so all ten scientific review gates remain PENDING.
    identity_snapshot = (
        confrontar_snapshot_portal_zika_2024() if agravo == "ZIKA" else None
    )
    topics = [{
        "topico": code,
        "questao_de_revisao": description,
        "status": "PENDENTE_DE_EVIDENCIA_E_REVISAO_HUMANA",
        "campos_2024_conferidos": False,
        "parecer_independente_autenticado": False,
    } for code, description in REVIEW_TOPICS]
    return {
        "schema_version": SCHEMA,
        "agravo": agravo,
        "ano_do_arquivo_pretendido": year,
        "referencias_documentais": sources,
        "numero_de_distribuicoes_catalogadas": n,
        "identidade_publica_uuid_formato_documentada": identity_snapshot is not None,
        "recursos_cotejados_com_snapshot_portal": (
            identity_snapshot["registros_documentais_concordantes"]
            if identity_snapshot is not None else 0
        ),
        "data_curadoria_identidade_portal": (
            identity_snapshot["data_curadoria_documental"]
            if identity_snapshot is not None else None
        ),
        "metadados_site_reconsultados_na_execucao": False,
        "dicionario_especifico_curado": False,
        "orientacao_ministerial_2024_sobre_a_ficha": (
            transversal["orientacao_especifica_de_notificacao_no_guia_2024"]
        ),
        "instrumento_de_notificacao_orientado": (
            transversal["instrumento_de_notificacao_orientado"]
        ),
        "vinculo_direto_do_pdf_na_pagina_do_agravo": (
            transversal["vinculo_direto_na_pagina_do_agravo"]
        ),
        "topicos_pendentes": topics,
        "total_topicos_pendentes": len(topics),
        "campos_de_arquivo_real_lidos": 0,
        "arquivos_anuais_autenticados": 0,
        "compatibilidade_dicionario_2024_verificada": False,
        "indicadores_homologados": 0,
        "autorizacao_analise_real": False,
        "autorizacao_publicacao": False,
        "status": "PLANO_DOCUMENTAL_SEM_CONFRONTO_DE_ARQUIVO_REAL",
        "aviso": (
            "Referências documentais e tarefas propostas; não são um cotejo real "
            "de cabeçalhos ou variáveis. Sem acesso a bancos, pacientes, ZIP, "
            "distribuições nem autorização para uso ou publicação."
        ),
    }
