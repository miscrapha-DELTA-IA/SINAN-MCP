"""Protocol-level E2E smoke tests: public (synthetic-only) and private *synthetic* demo.

No sockets, remote services, real SINAN files, or production credentials.
These tests exercise an MCP Client -> MCPServer protocol round trip and a
subprocess CLI -> local SQLite fixture -> MCP Client round trip.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys

from mcp import Client

from sinan_mcp import public_server, server as local_server

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "docs" / "public-mcp-contract-v1.json").read_text(encoding="utf-8")
)


async def _call(client, name, arguments=None):
    return await asyncio.wait_for(
        client.call_tool(name, {} if arguments is None else arguments),
        timeout=15,
    )


async def _public_roundtrip():
    async with Client(public_server.mcp, raise_exceptions=False) as client:
        available = (await asyncio.wait_for(client.list_tools(), timeout=15)).tools
        names = {tool.name for tool in available}
        assert names == set(CONTRACT["public_tools"])
        assert not any(
            name.startswith(tuple(CONTRACT["blocked_tool_prefixes"]))
            for name in names
        )

        for name, kwargs in [
            ("sobre_o_servidor", {}),
            ("listar_bases", {}),
            ("listar_agravos", {}),
            ("listar_fontes_oficiais", {}),
            ("pesquisar_agravos", {"termo": "tuberculose", "limite": 5}),
            ("descrever_agravo", {"codigo_interno": "TUBE"}),
            ("descrever_campos", {}),
            ("metodologia_abandono_tuberculose", {}),
        ]:
            response = await _call(client, name, kwargs)
            assert response.is_error is False, (name, response)
            assert isinstance(response.structured_content, dict), name

        metadata = (await _call(client, "sobre_o_servidor")).structured_content
        assert metadata["dados_reais_disponiveis"] is False
        assert metadata["acesso_microdados"] is False
        assert metadata["ferramentas_de_escrita"] is False
        assert metadata["modalidade"] == "publica_somente_leitura_sintetica"

        bases = (await _call(client, "listar_bases")).structured_content
        assert bases["dados_reais_disponiveis"] is False
        assert len(bases["bases"]) == 1
        assert bases["bases"][0]["tipo_de_fonte"] == "synthetic"

        counts = await _call(client, "contar_notificacoes", {
            "agravo": "TUBE", "ano_inicio": 2024,
            "ano_fim": 2024, "uf": "PI", "por": "raca_cor",
        })
        assert counts.is_error is False
        rows = counts.structured_content["resultado"]["dados"]
        assert sum(r["notificacoes_ficticias"] for r in rows) == CONTRACT["fixture"]["rows"]
        assert counts.structured_content["proveniencia"]["fonte"] == CONTRACT["fixture"]["provenance"]
        assert "SINTÉTICO" in counts.structured_content["aviso"]

        outcomes = await _call(client, "proporcao_abandono_tuberculose", {
            "ano_inicio": 2024, "ano_fim": 2024, "uf": "PI", "por": "sexo",
        })
        assert outcomes.is_error is False
        assert outcomes.structured_content["proveniencia"]["fonte"] == CONTRACT["fixture"]["provenance"]
        assert "SINTÉTICO" in outcomes.structured_content["aviso"]

        invalid = [
            ("contar_notificacoes", {
                "agravo": "DENG", "ano_inicio": 2024,
                "ano_fim": 2024, "uf": "PI",
            }),
            ("contar_notificacoes", {
                "agravo": "TUBE", "ano_inicio": 2023,
                "ano_fim": 2023, "uf": "PI",
            }),
            ("contar_notificacoes", {
                "agravo": "TUBE", "ano_inicio": 2024,
                "ano_fim": 2024, "uf": "RJ",
            }),
            ("contar_notificacoes", {
                "agravo": "TUBE", "ano_inicio": 2024,
                "ano_fim": 2024, "uf": "PI", "municipio": "221100",
            }),
            ("contar_notificacoes", {
                "agravo": "TUBE", "ano_inicio": 2024,
                "ano_fim": 2024, "uf": "PI", "por": "municipio",
            }),
            ("proporcao_abandono_tuberculose", {
                "ano_inicio": 2024, "ano_fim": 2025,
                "uf": "PI", "por": "sexo",
            }),
            ("importar-pysus", {}),
        ]
        for name, kwargs in invalid:
            rejected = await _call(client, name, kwargs)
            assert rejected.is_error is True, (
                "Unsafe query unexpectedly succeeded", name, kwargs
            )


def test_public_mcp_client_end_to_end_no_real_data(monkeypatch, tmp_path):
    # Even an intentionally poisoned ambient environment cannot add data.
    nonexistent = tmp_path / "sensitive-do-not-create.sqlite3"
    monkeypatch.setenv("SINAN_DB_PATH", str(nonexistent))
    monkeypatch.setenv("SINAN_PUBLIC_REAL_DATA", "1")
    asyncio.run(_public_roundtrip())
    assert not nonexistent.exists()


def test_local_synthetic_demo_cli_to_mcp_roundtrip(monkeypatch, tmp_path):
    demo_db = tmp_path / "demo.sqlite3"
    protected = tmp_path / "clinical-do-not-create.sqlite3"
    cmd = [
        sys.executable, "-m", "sinan_mcp", "--db", str(protected),
        "demo", "--demo-db", str(demo_db),
    ]
    env = os.environ.copy()
    env.pop("SINAN_PUBLIC_REAL_DATA", None)
    env.pop("SINAN_DB_PATH", None)
    cli = subprocess.run(
        cmd, cwd=tmp_path, env=env, capture_output=True, text=True,
        timeout=45,
    )
    assert cli.returncode == 0, cli.stderr
    assert demo_db.is_file()
    assert "100% SINTÉTICOS" in cli.stdout
    assert not protected.exists()

    monkeypatch.setenv("SINAN_DB_PATH", str(demo_db))
    monkeypatch.delenv("SINAN_PUBLIC_REAL_DATA", raising=False)

    async def check_private_demo():
        async with Client(local_server.mcp, raise_exceptions=False) as client:
            names = {
                x.name for x in
                (await asyncio.wait_for(client.list_tools(), timeout=15)).tools
            }
            assert {"listar_bases", "contar_notificacoes",
                    "proporcao_abandono_tuberculose"}.issubset(names)
            bases = await _call(client, "listar_bases")
            assert bases.is_error is False
            assert any(b["tipo_de_fonte"] == "synthetic"
                       for b in bases.structured_content["bases"])
            result = await _call(client, "contar_notificacoes", {
                "agravo": "TUBE", "ano_inicio": 2024, "ano_fim": 2024,
                "uf": "PI", "por": "raca_cor",
            })
            assert result.is_error is False, result
            assert result.structured_content["proveniencia"]["tipo_de_fonte"] == "synthetic"

    asyncio.run(check_private_demo())
    assert not protected.exists()


def test_demo_cli_preserves_non_synthetic_unrecognized_file(tmp_path):
    target = tmp_path / "do-not-overwrite.sqlite3"
    original = b"private database placeholder - do not modify"
    target.write_bytes(original)
    runner = subprocess.run(
        [
            sys.executable, "-m", "sinan_mcp", "--db",
            str(tmp_path / "unrelated.sqlite3"), "demo",
            "--demo-db", str(target),
        ],
        cwd=tmp_path, capture_output=True, text=True, timeout=45,
    )
    assert runner.returncode != 0
    assert target.read_bytes() == original
    assert not (tmp_path / "unrelated.sqlite3").exists()
