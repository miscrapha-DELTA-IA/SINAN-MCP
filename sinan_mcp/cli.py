"""CLI: importação explícita pelo administrador e servidor de consulta read-only."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
from .core import ingest_csv, ingest_pysus, diagnosticar_base


def main() -> None:
    parser = argparse.ArgumentParser(description="SINAN MCP (dados públicos, agregações)")
    parser.add_argument("--db", default=os.getenv("SINAN_DB_PATH", "./data/sinan.sqlite3"),
                        help="Caminho do SQLite local")
    cmd = parser.add_subparsers(dest="comando", required=True)
    csvp = cmd.add_parser("importar-csv", help="Importar CSV local preparado do SINAN")
    csvp.add_argument("arquivo", type=Path)
    csvp.add_argument("--agravo", required=True)
    csvp.add_argument("--ano", required=True, type=int)
    csvp.add_argument("--status", choices=["final", "preliminar", "desconhecido"], default="desconhecido")
    csvp.add_argument("--encoding", default="utf-8-sig")
    csvp.add_argument("--delimiter", default="auto")
    py = cmd.add_parser("importar-pysus", help="Baixar base pública via PySUS e importar")
    py.add_argument("--agravo", required=True)
    py.add_argument("--ano", required=True, type=int)
    py.add_argument("--source", choices=["catalog", "origin"], default="catalog")
    py.add_argument("--status", choices=["final", "preliminar", "desconhecido"], default="desconhecido")
    preview = cmd.add_parser("planejar-pysus", help="Prévia de download: metadados, tamanho e checksum, sem microdados")
    preview.add_argument("--agravo", required=True)
    preview.add_argument("--ano", type=int, required=True)
    discovery = cmd.add_parser("descobrir-pysus", help="Descobrir arquivos remotos SINAN sem baixar microdados")
    discovery.add_argument("--agravo", required=True)
    discovery.add_argument("--ano", required=True, type=int)
    discovery.add_argument("--source", choices=["auto", "catalog", "origin"], default="auto")
    discovery.add_argument("--cache-novo", action="store_true",
                           help="Usa um cache PySUS isolado novo sem alterar o cache existente")
    discovery.add_argument("--diagnostico", action="store_true",
                           help="Mostra estado dos catálogos locais e testa HEAD HTTPS do catálogo público")
    fairness = cmd.add_parser("auditar-equidade", help="Auditoria LOCAL de previsões binárias fora da amostra; nunca expõe via MCP")
    fairness.add_argument("arquivo", type=Path, help="CSV privado com y_true, y_score e grupo")
    fairness.add_argument("--grupo", choices=["raca_cor", "sexo"], required=True)
    fairness.add_argument("--coorte", required=True, help="Referência textual à coorte de avaliação")
    fairness.add_argument("--limiar", type=float, default=0.5)
    fairness.add_argument("--min-grupo", type=int, default=50)
    fairness.add_argument("--bootstrap", type=int, default=0)
    fairness.add_argument("--semente", type=int, default=42)
    official = cmd.add_parser(
        "preparar-tabela-oficial",
        help="Conferir um JSON local com metadados oficiais declarados, SEM publicar",
    )
    official.add_argument("arquivo", type=Path, help="JSON local privado com tabela pré-agregada")
    candidate = cmd.add_parser(
        "preparar-agregado", help="Preparar CANDIDATO LOCAL NÃO APROVADO para revisão de divulgação"
    )
    candidate.add_argument("--agravo", choices=["TUBE", "DENG"], required=True)
    candidate.add_argument("--ano", type=int, required=True, help="Ano do arquivo (não diagnóstico)")
    candidate.add_argument("--uf", required=True)
    candidate.add_argument("--por", choices=["sexo", "raca_cor"], required=True)
    verify = cmd.add_parser(
        "validar-pacote-aprovado", help="Conferir formato, parecer e SHA-256 de pacote aprovado; NÃO publicar"
    )
    verify.add_argument("arquivo", type=Path)
    verify.add_argument("--sha256", required=True, help="SHA-256 externo aprovado")
    sourceproof = cmd.add_parser(
        "verificar-proveniencia", help="Conferir hash de arquivo LOCAL e manifesto de origem declarado"
    )
    sourceproof.add_argument("manifesto", type=Path)
    sourceproof.add_argument("arquivo", type=Path, help="Arquivo de dados local; conteúdo nunca é enviado")
    lineage = cmd.add_parser(
        "verificar-linhagem", help="Conferir SHA do CSV local também contra snapshot SQLite"
    )
    lineage.add_argument("manifesto", type=Path)
    lineage.add_argument("arquivo", type=Path)
    annual_index = cmd.add_parser(
        "listar-distribuicoes-oficiais", help="Mostra IDs de recursos anuais no catálogo do MS, sem downloads"
    )
    annual_find = cmd.add_parser(
        "consultar-distribuicao-ano", help="Consulta recurso oficial por agravo/ano, somente metadados"
    )
    annual_find.add_argument("--agravo", required=True)
    annual_find.add_argument("--ano", required=True, type=int)
    annual_zip = cmd.add_parser(
        "conferir-zip-distribuicao", help="Analisa APENAS o ZIP local, sem extrair conteúdo"
    )
    annual_zip.add_argument("arquivo", type=Path)
    annual_zip.add_argument("--resource-id", required=True)
    schema_template = cmd.add_parser(
        "preparar-modelo-esquema",
        help="Gera candidato local com 3 campos documentais de exemplo; SEM validar 2024",
    )
    schema_template.add_argument("--resource-id", required=True)
    schema_template.add_argument("--pdf", required=True, type=Path)
    schema_template.add_argument("--saida", required=True, type=Path)
    pdf_draft = cmd.add_parser(
        "rascunhar-campos-dbf-pdf",
        help="Candidatos DBF do PDF SINAN Online 2015; exige revisão humana, sem validação 2024",
    )
    pdf_draft.add_argument("--resource-id", required=True)
    pdf_draft.add_argument("--pdf", required=True, type=Path)
    pdf_draft.add_argument("--saida", required=True, type=Path)
    modern_dict = cmd.add_parser(
        "confrontar-dicionario-dengue-2024",
        help="Somente offline: PDF documental 2024 x rascunho 2015 x cabeçalho CSV",
    )
    modern_dict.add_argument("--pdf", required=True, type=Path)
    modern_dict.add_argument("--contrato-2015", required=True, type=Path)
    modern_dict.add_argument("--zip", required=True, type=Path)
    modern_dict.add_argument("--parecer-pendente", required=True, type=Path)
    spelling = cmd.add_parser("conferir-hipoteses-grafia-dengue", help="Gerar hipoteses locais a partir de pareceres privados; sem dados de pacientes")
    spelling.add_argument("--pdf", required=True, type=Path)
    spelling.add_argument("--parecer-anterior", required=True, type=Path)
    spelling.add_argument("--extras-privados", required=True, type=Path)
    spelling.add_argument("--saida-privada", required=True, type=Path)
    private_csv_names = cmd.add_parser(
        "preparar-revisao-local-extras-dengue",
        help="Grava NOMES extras CSV somente em arquivo PRIVADO local, nao exibe nomes",
    )
    private_csv_names.add_argument("--pdf", required=True, type=Path)
    private_csv_names.add_argument("--contrato-2015", required=True, type=Path)
    private_csv_names.add_argument("--zip", required=True, type=Path)
    private_csv_names.add_argument("--parecer-anterior", required=True, type=Path)
    private_csv_names.add_argument("--saida-privada", required=True, type=Path)
    schema_audit = cmd.add_parser(
        "comparar-esquema-privado",
        help="Compara campos localmente com PDF e contrato manual; NÃO autoriza uso real",
    )
    schema_audit.add_argument("--resource-id", required=True)
    schema_audit.add_argument("--zip", required=True, type=Path)
    schema_audit.add_argument("--pdf", required=True, type=Path)
    schema_audit.add_argument("--contrato", required=True, type=Path)
    schema_audit.add_argument("--parecer-pendente", required=True, type=Path)
    multi_year = cmd.add_parser(
        "diagnosticar-cobertura-multiagravo",
        help="Mapa documental por agravo/ano SEM abrir dados reais",
    )
    multi_year.add_argument("--ano", type=int, required=True)
    multi_year.add_argument("--agravo", help="Alias interno, opcional, ex.: DENG")
    shared_docs = cmd.add_parser(
        "diagnosticar-documentacao-transversal",
        help="Referencias gerais de notificacao (ZIKA/SIFA) sem homologacao 2024",
    )
    shared_docs.add_argument("--ano", type=int, required=True)
    shared_docs.add_argument("--agravo", help="Alias interno opcional, ex.: ZIKA")
    crosswalk = cmd.add_parser(
        "planejar-confronto-documental-2024",
        help="Matriz de revisão documental ZIKA/SIFA, sem acesso a dados reais",
    )
    crosswalk.add_argument("--agravo", required=True, help="ZIKA ou SIFA")
    cmd.add_parser(
        "confrontar-identidade-zika-2024",
        help="Conferir snapshot offline de UUID/formato/pacote do portal, nao de ZIP",
    )
    cmd.add_parser(
        "identificar-dicionario-zika-ckan",
        help="Compatibilidade: busca dicionario na pagina HTML oficial; CKAN antigo indisponivel",
    )
    cmd.add_parser(
        "identificar-dicionario-zika-portal",
        help="ADMIN: busca somente metadados do PDF Zika no HTML oficial sem baixar arquivos",
    )
    readiness_template = cmd.add_parser(
        "preparar-checklist-roadmap",
        help="Criar checklist privado multiagravo/ano, todos os gates PENDENTES",
    )
    readiness_template.add_argument("--agravo", required=True)
    readiness_template.add_argument("--ano", required=True, type=int)
    readiness_template.add_argument("--resource-id")
    readiness_template.add_argument("--saida", required=True, type=Path)
    evidence_link = cmd.add_parser(
        "vincular-evidencia-dengue-roadmap",
        help="Vincula SOMENTE SHA de parecer DENG/2024 pendente; nao aprova nenhuma frente",
    )
    evidence_link.add_argument("--checklist", required=True, type=Path)
    evidence_link.add_argument("--parecer-esquema", required=True, type=Path)
    evidence_link.add_argument("--saida", required=True, type=Path)
    annual_source = cmd.add_parser(
        "preparar-dossie-fonte-dengue",
        help="Inspeciona ZIP LOCAL e cria dossie NAO VALIDADO; sem dados clinicos",
    )
    annual_source.add_argument("--zip", required=True, type=Path)
    annual_source.add_argument("--parecer-esquema", required=True, type=Path)
    annual_source.add_argument("--saida", required=True, type=Path)
    annual_attach = cmd.add_parser(
        "vincular-fonte-dengue-roadmap",
        help="Vincula SHA de dossie de fonte DENG/2024 sem validar origem/consolidacao",
    )
    annual_attach.add_argument("--checklist", required=True, type=Path)
    annual_attach.add_argument("--parecer-esquema", required=True, type=Path)
    annual_attach.add_argument("--dossie-fonte", required=True, type=Path)
    annual_attach.add_argument("--saida", required=True, type=Path)
    quality_plan = cmd.add_parser(
        "preparar-plano-qualidade-dengue",
        help="Prepara plano privado de auditoria DENG/2024 SEM examinar pacientes",
    )
    quality_plan.add_argument("--checklist", required=True, type=Path)
    quality_plan.add_argument("--parecer-esquema", required=True, type=Path)
    quality_plan.add_argument("--dossie-fonte", required=True, type=Path)
    quality_plan.add_argument("--saida", required=True, type=Path)
    synthetic_qa = cmd.add_parser(
        "auditar-csv-sintetico-dengue",
        help="SIMULACAO 100% ARTIFICIAL: nao abre nenhum CSV, ZIP ou banco",
    )
    synthetic_qa.add_argument("--plano", required=True, type=Path)
    synthetic_qa.add_argument("--saida", required=True, type=Path)
    review_packet = cmd.add_parser(
        "preparar-pacote-revisao-cientifica-dengue",
        help="Prepara perguntas cientificas PENDENTES, sem dados nem aprovacao",
    )
    review_packet.add_argument("--plano", required=True, type=Path)
    review_packet.add_argument("--simulacao", required=True, type=Path)
    review_packet.add_argument("--saida", required=True, type=Path)
    review_check = cmd.add_parser(
        "diagnosticar-pacote-revisao-cientifica-dengue",
        help="Diagnostica somente pacote local de perguntas nao homologadas",
    )
    review_check.add_argument("--arquivo", required=True, type=Path)
    readiness_check = cmd.add_parser(
        "diagnosticar-checklist-roadmap",
        help="Mostrar pendencias declaradas, SEM autenticar ou autorizar publicacao",
    )
    readiness_check.add_argument("--arquivo", required=True, type=Path)
    list_year = cmd.add_parser(
        "listar-evidencias-ano", help="Lista documentos oficiais localizados, SEM validar arquivo anual"
    )
    look_year = cmd.add_parser(
        "consultar-evidencia-ano", help="Consulta documentação curada por agravo/ano (sem números)"
    )
    look_year.add_argument("--agravo", required=True)
    look_year.add_argument("--ano", required=True, type=int)
    document_head = cmd.add_parser(
        "monitorar-documento-ano", help="HEAD apenas em URL oficial curada, SEM baixar documentos"
    )
    document_head.add_argument("--agravo", required=True)
    document_head.add_argument("--ano", required=True, type=int)
    audit_year = cmd.add_parser(
        "confrontar-evidencia-ano", help="Hash local de PDF e arquivo conforme manifesto; SEM autenticar fonte"
    )
    audit_year.add_argument("manifesto", type=Path)
    audit_year.add_argument("arquivo_dados", type=Path)
    audit_year.add_argument("pdf_dicionario", type=Path)
    inspect_contracts = cmd.add_parser(
        "listar-contratos-demo", help="Lista contratos ilustrativos TUBE/DENG sem dados"
    )
    diff_contract = cmd.add_parser(
        "comparar-contratos-demo", help="Diff de definições sintéticas (não oficial)"
    )
    diff_contract.add_argument("primeiro")
    diff_contract.add_argument("segundo")
    validate_contract = cmd.add_parser(
        "validar-csv-demo", help="PoC Pandera local, apenas esquema sintético"
    )
    validate_contract.add_argument("arquivo", type=Path)
    validate_contract.add_argument("--contrato", required=True)
    quality = cmd.add_parser(
        "auditar-qualidade", help="Relatório privado de qualidade da projeção já importada"
    )
    quality.add_argument("--agravo", required=True)
    quality.add_argument("--ano", required=True, type=int)
    reconciliation = cmd.add_parser(
        "confrontar-tabnet", help="Comparar tabela declarada com base local, sem divulgar células"
    )
    reconciliation.add_argument("arquivo", type=Path)
    methods = cmd.add_parser(
        "planejar-indicador", help="Verificar propostas por agravo/ano, SEM calcular dados reais"
    )
    methods.add_argument("--agravo", required=True)
    methods.add_argument("--ano", required=True, type=int)
    methods.add_argument("--protocolo", default=None)
    composition = cmd.add_parser(
        "verificar-composicao", help="Bloqueio de releases sobrepostos, SEM publicar"
    )
    composition.add_argument(
        "--pacote", nargs=2, action="append", required=True,
        metavar=("CAMINHO_JSON", "SHA256"), help="Repetir para cada pacote aprovado"
    )
    diagnostic = cmd.add_parser("diagnosticar-base", help="Relatório LOCAL de completude (administrativo)")
    diagnostic.add_argument("--agravo", required=True)
    diagnostic.add_argument("--ano", required=True, type=int)
    demo = cmd.add_parser("demo", help="Criar base sintética separada e mostrar próximo passo")
    demo.add_argument("--demo-db", default="./data/sinan-demo.sqlite3")
    serve = cmd.add_parser("servir", help="Servidor MCP (stdio ou HTTP local)")
    serve.add_argument("--http", action="store_true", help="MCP Streamable HTTP somente em localhost")
    serve.add_argument("--rest", action="store_true", help="REST JSON somente em localhost (adaptador não-MCP)")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    os.environ["SINAN_DB_PATH"] = str(Path(args.db).expanduser().resolve())
    if args.comando == "importar-csv":
        r = ingest_csv(args.db, args.arquivo, agravo=args.agravo, ano=args.ano,
                       status=args.status, encoding=args.encoding, delimiter=args.delimiter)
        print(r)
    elif args.comando == "importar-pysus":
        r = ingest_pysus(args.db, agravo=args.agravo, ano=args.ano,
                         status=args.status, source=args.source)
        print(r)
    elif args.comando == "planejar-pysus":
        import json
        from .pysus_gateway import _pysus
        from .catalog_import import manifest
        from .core import validate_agravo
        agravo = validate_agravo(args.agravo)
        # Hydrate PySUS's metadata caches only; no clinical file downloads.
        _pysus().sinan(disease=agravo, year=args.ano, source="catalog",
                       download=False, as_dataframe=False)
        entries = manifest(agravo, args.ano)
        print(json.dumps({
            "agravo": agravo, "ano_do_arquivo": args.ano,
            "fonte": "pysus-ftp-mirror/ducklake",
            "total_arquivos": len(entries),
            "bytes_estimados": sum(x["size"] for x in entries),
            "arquivos": [
                {"nome": x["name"], "bytes": x["size"],
                 "checksum_disponivel": bool(x["sha256"])}
                for x in entries
            ],
            "download_realizado": False,
            "aviso": "Prévia apenas. A importação precisa de comando separado e dados reais exigem controles de acesso.",
        }, ensure_ascii=False, indent=2))
    elif args.comando == "descobrir-pysus":
        import json
        from .pysus_diagnostics import create_isolated_cache, catalog_diagnostics
        if args.cache_novo:
            create_isolated_cache()
        from .pysus_gateway import descobrir
        try:
            result = descobrir(args.agravo, args.ano, args.source)
        except (OSError, RuntimeError, ValueError) as exc:
            if not args.diagnostico:
                raise
            result = {"status": "erro", "tipo_erro": type(exc).__name__,
                      "aviso": "Descoberta falhou; consulte o diagnostico de catalogo/rede."}
        if args.diagnostico:
            result["diagnostico"] = catalog_diagnostics()
        if args.cache_novo:
            result["cache_isolado"] = True
            result["nota_cache"] = "Cache de metadados novo salvo em data/; cache PySUS anterior preservado."
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.comando == "auditar-equidade":
        import json
        from .fairness import audit_predictions
        result = audit_predictions(
            args.arquivo, group=args.grupo, threshold=args.limiar,
            min_group=args.min_grupo, bootstrap=args.bootstrap,
            seed=args.semente, cohort=args.coorte,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.comando == "preparar-tabela-oficial":
        from .official_table_intake import prepare_private_tabnet_candidate
        try:
            path = prepare_private_tabnet_candidate(args.arquivo)
        except (ValueError, OSError) as exc:
            parser.exit(2, "TABELA NÃO ADMITIDA — não publicada: " + str(exc) + "\\n")
        print("TABELA OFICIAL DECLARADA — CANDIDATO PRIVADO NÃO APROVADO.")
        print("Arquivo local:", path)
        print("A URL, conteúdo, checksum declarado e consolidação NÃO foram")
        print("verificados contra a fonte remota. Revisão humana obrigatória.")
        print("Nenhum dado foi publicado nem enviado ao MCP.")
    elif args.comando == "preparar-agregado":
        from .release_pipeline import prepare_candidate, write_private_candidate
        from .aggregate_contract import candidate_digest
        try:
            result = prepare_candidate(
                args.db, agravo=args.agravo, ano=args.ano, uf=args.uf, por=args.por
            )
            path = write_private_candidate(result)
        except (ValueError, FileExistsError) as exc:
            parser.exit(
                2,
                "AGREGADO NÃO PUBLICÁVEL — operação encerrada sem criar ou "
                "divulgar uma nova tabela. " + str(exc) + "\\n"
            )
        print("CANDIDATO PRIVADO NÃO APROVADO, sem publicação nem envio ao MCP.")
        print("Arquivo local:", path)
        print("SHA-256 do candidato:", candidate_digest(result))
        print("Requer revisão epidemiológica, privacidade e comparação entre releases.")
        print("Não envie o arquivo para serviços públicos sem parecer independente.")
    elif args.comando == "validar-pacote-aprovado":
        from .aggregate_contract import load_approved_release
        approved = load_approved_release(args.arquivo, args.sha256)
        scope = approved["candidate"]["scope"]
        print("Estrutura, revisão registrada e checksum conferidos; NÃO é certificação de anonimização.")
        print("Agravo:", scope["agravo"], "ano do arquivo:", scope["ano_do_arquivo"],
              "UF:", scope["uf"], "dimensão:", scope["dimensao"])
        print("Nenhum dado foi publicado ou enviado à nuvem.")
    elif args.comando == "verificar-proveniencia":
        import json
        from .provenance import verify_local_file
        try:
            report = verify_local_file(args.manifesto, args.arquivo)
        except (OSError, ValueError) as exc:
            parser.exit(2, "PROVENIÊNCIA NÃO VERIFICADA — " + str(exc) + "\n")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "verificar-linhagem":
        import json
        from .provenance import verify_csv_import_lineage
        try:
            report = verify_csv_import_lineage(args.manifesto, args.arquivo, args.db)
        except (OSError, ValueError) as exc:
            parser.exit(2, "LINHAGEM NÃO VERIFICADA — " + str(exc) + "\n")
        print("SOMENTE INTEGRIDADE LOCAL; ORIGEM E PUBLICAÇÃO NÃO CERTIFICADAS.")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "listar-distribuicoes-oficiais":
        import json
        from .official_annual_resources import listar_recursos_oficiais_anuais
        print(json.dumps(listar_recursos_oficiais_anuais(), ensure_ascii=False, indent=2))
    elif args.comando == "consultar-distribuicao-ano":
        import json
        from .official_annual_resources import consultar_recursos_oficiais_ano
        try:
            report = consultar_recursos_oficiais_ano(args.agravo, args.ano)
        except ValueError as exc:
            parser.exit(2, "RECURSO NÃO IDENTIFICADO — " + str(exc) + "\n")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "conferir-zip-distribuicao":
        import json
        from .local_distribution_review import conferir_zip_recurso_local
        try:
            report = conferir_zip_recurso_local(args.resource_id, args.arquivo)
        except (OSError, ValueError) as exc:
            parser.exit(2, "ZIP LOCAL NÃO ADMITIDO — " + str(exc) + "\n")
        print("AUDITORIA LOCAL: não autentica publicação oficial ou dados clínicos.")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "preparar-modelo-esquema":
        from .local_schema_review import preparar_modelo_local
        try:
            report = preparar_modelo_local(args.resource_id, args.pdf, args.saida)
        except (OSError, ValueError, RuntimeError):
            parser.exit(2, "MODELO NÃO CRIADO — verifique a referência, o PDF e o destino local.\n")
        print("CANDIDATO LOCAL NÃO REVISADO. Não enviar o arquivo ao GitHub.")
        print("Campos de exemplo:", report["campos_exemplo_documentados"])
    elif args.comando == "diagnosticar-cobertura-multiagravo":
        from .multiagravo_readiness import diagnosticar_cobertura_multiagravo
        try:
            result = diagnosticar_cobertura_multiagravo(args.ano, args.agravo)
        except (ValueError, OSError):
            parser.exit(2, "COBERTURA NAO DIAGNOSTICADA: confira agravo e ano.\n")
        print("COBERTURA DOCUMENTAL MULTIAGRAVO, NAO APROVACAO CLINICA.")
        print("Ano do arquivo:", result["ano_do_arquivo"])
        print("Agravos no indice consultados:", result["agravos_referenciados"])
        print("Agravos com documentacao localizada:", result["agravos_com_documentacao_localizada"])
        print("Distribuicoes anuais catalogadas:", result["distribuicoes_catalogadas"])
        for row in result["registros"]:
            print(row["agravo"], "documento:",
                  "SIM" if row["documento_oficial_localizado"] else "NAO",
                  "distribuicoes:", row["distribuicoes_anuais_catalogadas"],
                  "indicador homologado: NAO")
        print("Acesso real e publicacao autorizados: NAO")
        print("Status:", result["status"])
    elif args.comando == "diagnosticar-documentacao-transversal":
        from .shared_notification_documents import diagnosticar_documentacao_transversal
        try:
            report = diagnosticar_documentacao_transversal(args.ano, args.agravo)
        except ValueError:
            parser.exit(2, "DOCUMENTACAO TRANSVERSAL NAO DIAGNOSTICADA: confira agravo e ano.\n")
        print("DOCUMENTACAO TRANSVERSAL, NAO DICIONARIO ESPECIFICO NEM VALIDACAO CLINICA.")
        print("Ano do arquivo pretendido:", report["ano_do_arquivo_pretendido"])
        print("Referencias transversais candidatas:", report["referencias_transversais_candidatas"])
        print("Vinculos diretos na pagina do agravo:", report["vinculos_diretos_na_pagina_do_agravo"])
        for row in report["registros"]:
            print(row["agravo"], "referencia transversal:",
                  "SIM" if row["referencia_transversal_candidata"] else "NAO",
                  "vinculo direto:",
                  "SIM" if row["vinculo_direto_na_pagina_do_agravo"] else "NAO",
                  "compatibilidade 2024: NAO")
        print("Acesso real e publicacao autorizados: NAO")
        print("Status:", report["status"])
    elif args.comando == "planejar-confronto-documental-2024":
        from .documentary_crosswalk_2024 import planejar_confronto_documental_2024
        try:
            report = planejar_confronto_documental_2024(args.agravo)
        except ValueError:
            parser.exit(2, "MATRIZ DOCUMENTAL NAO CRIADA: use ZIKA ou SIFA.\n")
        print("MATRIZ DOCUMENTAL 2024, NAO CONFRONTO DE DADOS OU APROVACAO.")
        print("Agravo:", report["agravo"])
        print("Distribuicoes anuais catalogadas:", report["numero_de_distribuicoes_catalogadas"])
        print("Orientacao ministerial 2024 da ficha:",
              "SIM" if report["orientacao_ministerial_2024_sobre_a_ficha"] else "NAO")
        print("UUID e formato da pagina oficial documentados:",
              "SIM" if report["identidade_publica_uuid_formato_documentada"] else "NAO")
        if report["agravo"] == "ZIKA":
            print("Sistema SINAN Net descrito no catalogo oficial:",
                  "SIM" if report["sinan_net_descrito_no_portal"] else "NAO")
            print("Dicionario especifico Zika listado no portal:",
                  "SIM" if report["dicionario_especifico_zika_listado_no_portal"] else "NAO")
            print("PDF especifico Zika auditado:",
                  "SIM" if report["pdf_exato_zika_auditado"] else "NAO")
            print("Data de corte exata do arquivo ZIKA/2024: NAO IDENTIFICADA")
        print("Topicos de revisao pendentes:", report["total_topicos_pendentes"])
        for entry in report["topicos_pendentes"]:
            print(entry["topico"] + ": PENDENTE")
        print("Campos reais lidos: 0; indicadores homologados: 0")
        print("Acesso real e publicacao autorizados: NAO")
        print("Status:", report["status"])
    elif args.comando == "confrontar-identidade-zika-2024":
        from .zika_resource_identity import confrontar_snapshot_portal_zika_2024
        try:
            report = confrontar_snapshot_portal_zika_2024()
        except (ValueError, OSError):
            parser.exit(2, "IDENTIDADE DOCUMENTAL ZIKA INCONSISTENTE.\n")
        print("IDENTIDADE DOCUMENTAL ZIKA/2024, NAO AUTENTICACAO DE ARQUIVO.")
        print("Data da curadoria:", report["data_curadoria_documental"])
        print("Recursos com identidade documental concordante:",
              report["registros_documentais_concordantes"])
        for row in report["registros"]:
            print(row["formato_documentado"], "UUID:", row["resource_id"],
                  "status da pagina na curadoria:", row["estado_observado_na_pagina"])
        print("Reconsulta online nesta execucao: NAO")
        print("Arquivos binarios acessados: 0; campos clinicos lidos: 0")
        print("Layout 2024 e consolidacao comprovados: NAO")
        print("Acesso real e publicacao autorizados: NAO")
        print("Status:", report["status"])
    elif args.comando in ("identificar-dicionario-zika-portal",
                            "identificar-dicionario-zika-ckan"):
        from .admin_zika_portal_html import descobrir_dicionario_zika_portal
        from .admin_zika_dictionary_discovery import classificar_falha_descoberta
        from urllib.error import HTTPError, URLError
        try:
            report = descobrir_dicionario_zika_portal()
        except (ValueError, OSError, UnicodeError, HTTPError, URLError) as exc:
            reason = classificar_falha_descoberta(exc)
            parser.exit(
                2, "DOCUMENTO ZIKA NAO IDENTIFICADO COM PROVENIENCIA SUFICIENTE.\n"
                "Causa tecnica: " + reason + "\n"
                "Pagina oficial: https://dadosabertos.saude.gov.br/dataset/"
                "arboviroses-zika-virus\n"
                "HTML pode omitir o UUID mesmo quando o titulo aparece na pagina. "
                "Nao usar resultados fabricados ou a antiga API CKAN.\n"
                "PDF auditado: NAO; layout 2024 validado: NAO; "
                "publicacao autorizada: NAO.\n"
            )
        print("METADADOS DE DICIONARIO ZIKA NO HTML OFICIAL; PDF NAO AUDITADO.")
        print("Origem:", report["fonte_html_oficial"])
        print("Metodo:", report["metodo_de_evidencia"])
        print("UUID recurso:", report["recurso_uuid_documentado"])
        print("Pagina oficial do recurso:", report["pagina_recurso_oficial"])
        print("Formato registrado:", report["formato_declarado_no_html"])
        if report["url_pdf_aprovada_estruturalmente"] is not None:
            print("URL PDF documental candidata:",
                  report["url_pdf_aprovada_estruturalmente"])
        print("PDF baixado: NAO; PDF auditado: NAO")
        print("Layout 2024 e data de corte confirmados: NAO")
        print("Indicadores homologados: 0; publicacao autorizada: NAO")
        print("Status:", report["status"])
    elif args.comando == "preparar-checklist-roadmap":
        from .roadmap_readiness import preparar_checklist_local
        try:
            result = preparar_checklist_local(
                args.agravo, args.ano, args.saida, args.resource_id
            )
        except (ValueError, OSError):
            parser.exit(2, "CHECKLIST NAO GERADO: confira escopo e destino novo.\n")
        print("CHECKLIST PRIVADO CRIADO, USO REAL BLOQUEADO.")
        print("Agravo:", result["agravo"], "ano do arquivo:", result["ano_do_arquivo"])
        print("Frentes pendentes:", result["n_frentes_pendentes"])
        print("Autorizacao de publicacao:", "NAO")
    elif args.comando == "vincular-evidencia-dengue-roadmap":
        from .local_roadmap_evidence import vincular_parecer_dengue_checklist_local
        try:
            result = vincular_parecer_dengue_checklist_local(
                args.checklist, args.parecer_esquema, args.saida,
            )
        except (ValueError, OSError, UnicodeError):
            parser.exit(2, "VINCULO NAO CRIADO: confira escopo, parecer, checklist e saida nova.\n")
        print("PARECER DE DENGUE VINCULADO COMO EVIDENCIA LOCAL NAO VALIDADA.")
        print("Frentes sem evidencia:", result["n_frentes_pendentes"])
        print("Frentes com evidencia nao validada:",
              result["n_frentes_com_evidencia_local_nao_validada"])
        print("Parecer cientifico:", "PENDENTE")
        print("Publicacao autorizada:", "NAO")
    elif args.comando == "preparar-dossie-fonte-dengue":
        from .local_annual_source_evidence import preparar_dossie_fonte_dengue_local
        try:
            result = preparar_dossie_fonte_dengue_local(
                args.zip, args.parecer_esquema, args.saida,
            )
        except (ValueError, OSError, UnicodeError):
            parser.exit(2, "DOSSIE NAO GERADO: confira ZIP, parecer e destino exclusivo.\n")
        print("DOSSIE PRIVADO DE FONTE CRIADO. ORIGEM OFICIAL NAO AUTENTICADA.")
        print("ZIP local vinculado ao parecer:", "SIM" if result["zip_local_conciliado_com_parecer"] else "NAO")
        print("Consolidacao:", result["status_consolidacao"])
        print("Publicacao:", "NAO AUTORIZADA")
    elif args.comando == "vincular-fonte-dengue-roadmap":
        from .local_annual_source_evidence import vincular_dossie_fonte_dengue_roadmap_local
        try:
            result = vincular_dossie_fonte_dengue_roadmap_local(
                args.checklist, args.parecer_esquema, args.dossie_fonte, args.saida,
            )
        except (ValueError, OSError, UnicodeError):
            parser.exit(2, "FONTE NAO VINCULADA: confira arquivos, hashes e destino.\n")
        print("EVIDENCIA LOCAL DE FONTE VINCULADA; NENHUMA HOMOLOGACAO.")
        print("Frentes sem evidencia:", result["n_frentes_pendentes"])
        print("Frentes com evidencia local nao validada:",
              result["n_frentes_com_evidencia_local_nao_validada"])
        print("Status:", result["status"])
    elif args.comando == "preparar-plano-qualidade-dengue":
        from .local_dengue_quality_protocol import preparar_plano_qualidade_dengue_local
        try:
            result = preparar_plano_qualidade_dengue_local(
                args.checklist, args.parecer_esquema, args.dossie_fonte, args.saida,
            )
        except (ValueError, OSError, UnicodeError):
            parser.exit(2, "PLANO NAO GERADO: confira checklist, hashes e destino local.\n")
        print("PLANO PRIVADO DE QUALIDADE GERADO; NENHUM DADO CLINICO LIDO.")
        print("Verificacoes pendentes:", result["checkpoints_pendentes"])
        print("Frentes roadmap ainda pendentes:", result["frentes_roadmap_ainda_pendentes"])
        print("Qualidade/coorte validada:", "NAO")
        print("Publicacao autorizada:", "NAO")
    elif args.comando == "auditar-csv-sintetico-dengue":
        from .synthetic_dengue_csv_audit import auditar_fixture_dengue_local
        try:
            result = auditar_fixture_dengue_local(args.plano, args.saida)
        except (ValueError, OSError, UnicodeError):
            parser.exit(2, "SIMULACAO NAO GERADA: confira plano privado e destino novo.\n")
        print("AUDITORIA EXCLUSIVAMENTE SINTETICA. NENHUM DADO SINAN LIDO.")
        print("Linhas artificiais:", result["linhas_sinteticas"])
        print("Entradas invalidas recusadas:", result["casos_adversariais_recusados"])
        print("Checkpoints cientificos homologados:", result["checkpoints_cientificos_validados"])
        print("Status:", result["status"])
        print("Publicacao autorizada:", "NAO")
    elif args.comando == "preparar-pacote-revisao-cientifica-dengue":
        from .local_dengue_scientific_review import preparar_pacote_revisao_dengue_local
        try:
            result = preparar_pacote_revisao_dengue_local(
                args.plano, args.simulacao, args.saida
            )
        except (ValueError, OSError, UnicodeError):
            parser.exit(2, "PACOTE CIENTIFICO NAO GERADO: confira hashes e destino novo.\n")
        print("PEDIDO DE REVISAO CIENTIFICA, NAO HOMOLOGACAO.")
        print("Questoes pendentes:", result["questoes_cientificas_pendentes"])
        print("Checkpoints de qualidade pendentes:", result["checkpoints_qualidade_pendentes"])
        print("Pareceres autenticados:", result["revisores_autenticados"])
        print("Dados reais lidos:", result["dados_reais_lidos"])
        print("Status:", result["status"])
    elif args.comando == "diagnosticar-pacote-revisao-cientifica-dengue":
        from .local_dengue_scientific_review import diagnosticar_pacote_cientifico_local
        try:
            result = diagnosticar_pacote_cientifico_local(args.arquivo)
        except (ValueError, OSError, UnicodeError):
            parser.exit(2, "PACOTE CIENTIFICO INVALIDO OU NAO PENDENTE.\n")
        print("QUESTOES CIENTIFICAS AINDA NAO HOMOLOGADAS.")
        print("Questoes pendentes:", result["questoes_cientificas_pendentes"])
        print("Checkpoints de qualidade pendentes:", result["checkpoints_qualidade_pendentes"])
        print("Pareceres autenticados:", result["revisores_autenticados"])
        print("Status:", result["status"])
        print("Publicacao autorizada:", "NAO")
    elif args.comando == "diagnosticar-checklist-roadmap":
        from .roadmap_readiness import diagnosticar_checklist_local
        try:
            result = diagnosticar_checklist_local(args.arquivo)
        except (ValueError, OSError):
            parser.exit(2, "CHECKLIST NAO VALIDADO: arquivo privado invalido.\n")
        print("DIAGNOSTICO OPERACIONAL, NAO APROVACAO CIENTIFICA.")
        print("Agravo:", result["agravo"], "ano:", result["ano_do_arquivo"])
        print("Frentes pendentes:", result["n_frentes_pendentes"],
              "de", result["total_frentes"])
        print("Pendencias:", ", ".join(result["pendencias_sem_evidencia"]))
        print("Declaracoes locais:", result["n_frentes_com_evidencia_local_nao_validada"])
        print("Pareceres externos nao autenticados:",
              result["n_frentes_com_parecer_declarado_nao_autenticado"])
        print("Status:", result["status"])
    elif args.comando == "conferir-hipoteses-grafia-dengue":
        from .local_dengue_spelling_review import gerar_hipoteses_grafia_dengue_local
        try:
            result = gerar_hipoteses_grafia_dengue_local(
                args.pdf, args.parecer_anterior, args.extras_privados, args.saida_privada,
            )
        except (ValueError, OSError, RuntimeError, UnicodeError):
            parser.exit(2, "HIPOTESES NAO GERADAS: confira documentos e destino.\n")
        print("HIPOTESES PRIVADAS, NAO APROVADAS.")
        print("Extras examinados:", result["extras_avaliados"])
        print("Hipoteses de grafia:", result["hipoteses_grafia"])
        print("Sem correspondencia:", result["sem_correspondencia"])
        print("Revisao independente:", result["revisao_independente"])
    elif args.comando == "preparar-revisao-local-extras-dengue":
        from .local_dengue_csv_extra_review import gerar_revisao_privada_cabecalhos_dengue
        try:
            result = gerar_revisao_privada_cabecalhos_dengue(
                args.pdf, args.contrato_2015, args.zip,
                args.parecer_anterior, args.saida_privada,
            )
        except (ValueError, OSError, RuntimeError, UnicodeError):
            parser.exit(2, "REVISAO PRIVADA NAO GERADA - confira documentos, "
                           "ZIP, hashes, parecer e destino exclusivo.\n")
        print("REVISAO DE CABECALHO PRIVADA CRIADA; NAO PUBLICAR.")
        print("Quantidade de nomes extras:", result["quantidade"])
        print("Nomes no terminal:", "NAO")
        print("Parecer independente:", result["revisao"])
    elif args.comando == "confrontar-dicionario-dengue-2024":
        from .local_dengue_dictionary_crosswalk import confrontar_dengue_dicionarios_local
        try:
            summary = confrontar_dengue_dicionarios_local(
                args.pdf, args.contrato_2015, args.zip, args.parecer_pendente,
            )
        except (ValueError, OSError, RuntimeError):
            parser.exit(2, "CONFRONTO LOCAL NÃO CONCLUÍDO — confira PDF, ZIP, "
                           "contrato privado de 2015 e destino novo.\n")
        print("MATRIZ PRIVADA PENDENTE; NENHUM INDICADOR REAL AUTORIZADO.")
        print("PDF atual: entradas:", summary["total_pdf_atual"],
              "nomes distintos:", summary["unicos_pdf_atual"])
        print("CSV: campos observados:", summary["csv_observados"])
        print("PDF atual e CSV: nomes comuns:", summary["comuns_pdf_atual_csv"])
        print("PDF atual ausentes do CSV:", summary["ausentes_csv_do_pdf_atual"])
        print("CSV fora do PDF atual:", summary["adicionais_csv_fora_pdf_atual"])
        print("Hipóteses de diferença de escopo (NÃO validadas):",
              summary["ausencias_com_hipotese_de_escopo"])
        print("Revisão independente:", summary["revisao"])
    elif args.comando == "rascunhar-campos-dbf-pdf":
        from .local_pdf_dictionary_candidate import gerar_rascunho_pdf_dbf_local
        try:
            report = gerar_rascunho_pdf_dbf_local(
                args.resource_id, args.pdf, args.saida
            )
        except (ValueError, OSError, RuntimeError):
            parser.exit(
                2, "RASCUNHO PDF NÃO GERADO — perfil de layout, PDF ou destino "
                   "não conferem. Verifique o PDF local e revise manualmente.\n"
            )
        print("CANDIDATO DBF EXTRAÍDO; DICIONÁRIO 2024 NÃO VALIDADO.")
        print("Campos candidatos:", report["campos_candidatos_extraidos"])
        print("Nomes ambíguos não normalizados:", report["nomes_ambiguos_nao_normalizados"])
        print("Repetições no PDF:", report["nomes_repetidos_no_pdf"])
        print("Falsos positivos revisados excluídos:", report["falsos_positivos_revisados_excluidos"])
        print("Revisão humana:", "PENDENTE")
    elif args.comando == "comparar-esquema-privado":
        from .local_schema_review import (
            comparar_esquema_local, salvar_parecer_pendente_local,
        )
        try:
            report = comparar_esquema_local(
                args.resource_id, args.zip, args.pdf, args.contrato
            )
            summary = salvar_parecer_pendente_local(
                report, args.parecer_pendente
            )
        except (OSError, ValueError, RuntimeError):
            parser.exit(2, "COMPARAÇÃO LOCAL RECUSADA — confira contrato, PDF, pacote e destino.\n")
        print("PACOTE DE REVISÃO PRIVADA GERADO; NENHUM INDICADOR REAL AUTORIZADO.")
        print("Estado:", report["estado"])
        print("Campos do dicionário não encontrados:", len(report["campos_documentados_ausentes"]))
        print("Campos fora da transcrição:", report["n_campos_nao_documentados"])
        print("Parecer independente:", "PENDENTE")
    elif args.comando == "listar-evidencias-ano":
        import json
        from .year_evidence_registry import listar_evidencias_documentais
        print(json.dumps(listar_evidencias_documentais(), ensure_ascii=False, indent=2))
    elif args.comando == "consultar-evidencia-ano":
        import json
        from .year_evidence_registry import consultar_evidencia_agravo_ano
        try:
            report = consultar_evidencia_agravo_ano(args.agravo, args.ano)
        except ValueError as exc:
            parser.exit(2, "CONSULTA DOCUMENTAL RECUSADA — " + str(exc) + "\n")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "monitorar-documento-ano":
        import json
        from .document_link_probe import monitorar_link_documental
        try:
            report = monitorar_link_documental(args.agravo, args.ano)
        except ValueError as exc:
            parser.exit(2, "DOCUMENTO NÃO MONITORÁVEL — " + str(exc) + "\n")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "confrontar-evidencia-ano":
        import json
        from .year_evidence_review import confrontar_documento_e_arquivo_local
        try:
            report = confrontar_documento_e_arquivo_local(
                args.manifesto, args.arquivo_dados, args.pdf_dicionario
            )
        except (OSError, ValueError) as exc:
            parser.exit(2, "EVIDÊNCIA LOCAL NÃO VERIFICADA — " + str(exc) + "\n")
        print("INTEGRIDADE DE ARQUIVOS LOCAIS; AUTENTICIDADE OFICIAL NÃO COMPROVADA.")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "listar-contratos-demo":
        import json
        from .schema_contracts import list_example_contracts
        print(json.dumps(list_example_contracts(), ensure_ascii=False, indent=2))
    elif args.comando == "comparar-contratos-demo":
        import json
        from .schema_contracts import diff_example_contracts
        try:
            report = diff_example_contracts(args.primeiro, args.segundo)
        except ValueError as exc:
            parser.exit(2, "CONTRATOS NÃO COMPARÁVEIS — " + str(exc) + "\n")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "validar-csv-demo":
        import json
        from .schema_contracts import validate_example_csv
        try:
            report = validate_example_csv(args.arquivo, contract_id=args.contrato)
        except (ValueError, RuntimeError, OSError) as exc:
            parser.exit(2, "VALIDAÇÃO LOCAL RECUSADA — " + str(exc) + "\n")
        print("VALIDAÇÃO DE EXEMPLO LOCAL, NÃO CERTIFICA DADOS SINAN.")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "auditar-qualidade":
        import json
        from .quality_gate import audit_projected_snapshot
        try:
            report = audit_projected_snapshot(args.db, agravo=args.agravo, ano=args.ano)
        except (OSError, ValueError) as exc:
            parser.exit(2, "AUDITORIA LOCAL INDISPONÍVEL — " + str(exc) + "\n")
        print("AVISO: RELATÓRIO SENSÍVEL LOCAL; NÃO COMPARTILHAR/ENVIAR AO MCP.")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "confrontar-tabnet":
        import json
        from .reconciliation import reconcile_declared_table
        try:
            report = reconcile_declared_table(args.db, args.arquivo)
        except (OSError, ValueError) as exc:
            parser.exit(2, "COMPARAÇÃO NÃO ADMITIDA — " + str(exc) + "\n")
        print("RESULTADO LOCAL PRIVADO, NÃO PUBLICÁVEL AUTOMATICAMENTE.")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "planejar-indicador":
        import json
        from .indicator_protocols import plan_indicator
        try:
            report = plan_indicator(args.agravo, args.ano, args.protocolo)
        except ValueError as exc:
            parser.exit(2, "PROTOCOLO NÃO DISPONÍVEL — " + str(exc) + "\n")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "verificar-composicao":
        import json
        from .release_composition import assess_release_set
        try:
            report = assess_release_set([(path, sha) for path, sha in args.pacote])
        except (OSError, ValueError) as exc:
            parser.exit(2, "COMPOSIÇÃO NÃO ADMITIDA — " + str(exc) + "\n")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.comando == "diagnosticar-base":
        import json
        print(json.dumps(diagnosticar_base(args.db, args.agravo, args.ano), ensure_ascii=False, indent=2))
    elif args.comando == "demo":
        from .demo import build_demo
        demo_db = Path(args.demo_db).expanduser().resolve()
        if demo_db == Path(args.db).expanduser().resolve():
            parser.error("A base demo não pode sobrescrever a base principal")
        print(build_demo(demo_db))
        print("DADOS 100% SINTÉTICOS; nunca utilizar em análises epidemiológicas.")
        print(f"Inicie: python -m sinan_mcp --db {str(demo_db)!r} servir")
        print("Experimente: contagens TUBE, ano 2024, UF PI, por raca_cor")
    else:
        if args.http and args.rest:
            parser.error("Use apenas --http ou --rest")
        if args.rest:
            from .rest import run_rest
            run_rest(args.port)
            return
        from .server import mcp
        if args.http:
            if not 1024 <= args.port <= 65535:
                parser.error("porta fora do intervalo 1024-65535")
            mcp.run(transport="streamable-http", host="127.0.0.1", port=args.port)
        else:
            mcp.run()
