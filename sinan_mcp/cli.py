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
