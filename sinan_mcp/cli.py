"""CLI: importação explícita pelo administrador e servidor de consulta read-only."""
from __future__ import annotations
import argparse
import os
import sys
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
    parquet = cmd.add_parser("importar-parquet", help="Importar Parquet local já obtido (sem depender do catálogo PySUS)")
    parquet.add_argument("arquivo", type=Path)
    parquet.add_argument("--agravo", required=True)
    parquet.add_argument("--ano", required=True, type=int)
    parquet.add_argument("--status", choices=["final", "preliminar", "desconhecido"], default="desconhecido")
    py = cmd.add_parser("importar-pysus", help="Baixar base pública via PySUS e importar")
    py.add_argument("--agravo", required=True)
    py.add_argument("--ano", required=True, type=int)
    py.add_argument("--source", choices=["catalog", "origin"], default="catalog")
    py.add_argument("--cache-dir", type=Path, help="Cache PySUS alternativo (mesma pasta usada na descoberta)")
    py.add_argument("--status", choices=["final", "preliminar", "desconhecido"], default="desconhecido")
    discovery = cmd.add_parser("descobrir-pysus", help="Descobrir arquivos remotos SINAN sem baixar microdados")
    discovery.add_argument("--agravo", required=True)
    discovery.add_argument("--ano", required=True, type=int)
    discovery.add_argument("--source", choices=["catalog", "origin"], default="catalog")
    discovery.add_argument("--cache-dir", type=Path, help="Cache PySUS alternativo (pasta nova, não apaga o existente)")
    inspector = cmd.add_parser("diagnosticar-pysus", help="Diagnosticar catálogo PySUS sem baixar microdados")
    inspector.add_argument("--agravo", required=True)
    inspector.add_argument("--ano", required=True, type=int)
    inspector.add_argument("--cache-dir", type=Path, help="Usar cache PySUS alternativo")
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
    if getattr(args, "cache_dir", None) is not None:
        # Must be set BEFORE PySUS is imported: its DuckLake cache_dir is
        # initialized at import time, so pysus.set_cache() here is too late.
        os.environ["PYSUS_CACHEPATH"] = str(args.cache_dir.expanduser().resolve())
    if args.comando == "importar-csv":
        r = ingest_csv(args.db, args.arquivo, agravo=args.agravo, ano=args.ano,
                       status=args.status, encoding=args.encoding, delimiter=args.delimiter)
        print(r)
    elif args.comando == "importar-parquet":
        from .local_files import importar_parquet
        try:
            print(importar_parquet(args.db, args.arquivo, agravo=args.agravo,
                                  ano=args.ano, status=args.status))
        except (RuntimeError, ValueError, OSError) as exc:
            parser.exit(2, f"Falha na importação Parquet: {exc}\\n")
    elif args.comando == "importar-pysus":
        try:
            r = ingest_pysus(args.db, agravo=args.agravo, ano=args.ano,
                             status=args.status, source=args.source)
        except (RuntimeError, ValueError, OSError) as exc:
            parser.exit(2, f"Falha na importação: {exc}\n")
        print(r)
    elif args.comando == "descobrir-pysus":
        import json
        from .pysus_gateway import descobrir
        try:
            data = descobrir(args.agravo, args.ano, args.source)
        except (RuntimeError, ValueError, OSError) as exc:
            parser.exit(2, f"Falha na descoberta: {exc}\n")
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif args.comando == "diagnosticar-pysus":
        import json
        from .pysus_gateway import diagnosticar
        try:
            data = diagnosticar(args.agravo, args.ano)
        except (RuntimeError, ValueError, OSError) as exc:
            parser.exit(2, f"Falha no diagnóstico: {exc}\n")
        print(json.dumps(data, ensure_ascii=False, indent=2))
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
