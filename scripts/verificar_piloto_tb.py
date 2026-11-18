"""Verify the pinned private TB pilot through the local stdio MCP entry point."""
import argparse
import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from sinan_mcp.tb_pilot import SHA256, SOURCE_TYPE


async def verify(db: Path) -> None:
    params = StdioServerParameters(command=sys.executable,
                                   args=["-m", "sinan_mcp", "--db", str(db.resolve()), "servir"],
                                   env={"SINAN_PUBLIC_REAL_DATA": "1"})
    async with Client(params, read_timeout_seconds=30, raise_exceptions=True) as client:
        bases = (await client.call_tool("listar_bases", {})).structured_content["bases"]
        if not any(b["tipo_de_fonte"] == SOURCE_TYPE and b["ano_do_arquivo"] == 2024
                   and b["agravo"] == "TUBE" for b in bases):
            raise ValueError("Snapshot TUBE 2024 ausente")
        reply = await client.call_tool("contar_notificacoes", {
            "agravo": "TUBE", "uf": "PI", "ano_inicio": 2024, "ano_fim": 2024, "por": "sexo",
        })
        payload = reply.structured_content
        if payload["proveniencia"]["fingerprint_sha256"] != SHA256:
            raise ValueError("A resposta corresponde a outro snapshot")
        result = payload["resultado"]
        if result.get("status") == "nao_divulgavel" and result["dados"] == []:
            print("MCP stdio OK. Consulta TUBE/2024, PI, sexo: partição suprimida.")
        elif result["dados"]:
            print("MCP stdio OK. Consulta TUBE/2024, PI, sexo: agregado retornado.")
        else:
            raise ValueError("Resposta inesperada para o snapshot")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path)
    asyncio.run(verify(parser.parse_args().db))
