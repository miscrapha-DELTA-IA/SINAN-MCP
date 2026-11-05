"""Read-only HTTPS smoke test for the intentionally fictional public MCP.

Runs from CI, never requests real surveillance data.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CONTRACT = json.loads(
    (Path(__file__).resolve().parents[1] / "docs" / "public-mcp-contract-v1.json")
    .read_text(encoding="utf-8")
)
BASE = os.environ.get("SINAN_PUBLIC_SMOKE_URL", "").rstrip("/")
if not BASE.startswith("https://") or not BASE.endswith(".onrender.com"):
    raise SystemExit("SINAN_PUBLIC_SMOKE_URL must be an explicit approved HTTPS Render hostname")


def request(path: str, payload=None, *, origin=None):
    headers = {"Accept": "application/json, text/event-stream"}
    if payload is not None:
        headers.update({
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2025-11-25",
        })
    if origin is not None:
        headers["Origin"] = origin
    req = Request(
        BASE + path, headers=headers, method="POST" if payload else "GET",
        data=json.dumps(payload).encode("utf-8") if payload else None,
    )
    with urlopen(req, timeout=30) as response:
        if response.status != 200:
            raise AssertionError(f"Expected 200, got {response.status}")
        raw = response.read(100_000)
        return json.loads(raw)


def rpc(method: str, params: dict, *, origin=None):
    return request("/mcp", {
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params,
    }, origin=origin)


def tool(name: str, arguments: dict):
    result = rpc("tools/call", {"name": name, "arguments": arguments})
    if "error" in result:
        raise AssertionError(f"MCP error on tool {name}: {result['error'].get('code')}")
    obj = result["result"].get("structuredContent")
    if obj is None:
        blocks = result["result"].get("content", [])
        obj = json.loads(next(v["text"] for v in blocks if v.get("type") == "text"))
    return obj


def main():
    last = None
    for _ in range(50):
        try:
            health = request("/health")
            assert health["status"] == "ok"
            assert health["deployment"] == "synthetic-only"
            print("PASS HTTPS /health: synthetic-only")
            break
        except (AssertionError, URLError, TimeoutError, ValueError) as exc:
            last = type(exc).__name__
            time.sleep(5)
    else:
        raise AssertionError("Public endpoint did not become healthy: " + str(last))

    # Verify the *deployed* privacy policy, not only the source repository.
    # These are read-only GETs; never echo request bodies or log personal data.
    for path in ("/privacidade", "/privacy"):
        req = Request(BASE + path, headers={"Accept": "text/html"}, method="GET")
        with urlopen(req, timeout=30) as response:
            assert response.status == 200, "Public privacy route is not HTTP 200"
            assert response.headers.get("Content-Type", "").startswith("text/html"), (
                "Public privacy route lacks HTML content type"
            )
            assert response.headers.get("X-Content-Type-Options") == "nosniff"
            assert response.headers.get("Cache-Control") == "no-store"
            assert "default-src 'none'" in response.headers.get("Content-Security-Policy", "")
            html = response.read(100_000).decode("utf-8")
        assert '<html lang="pt-BR">' in html
        assert "Raphael Múcio Teixeira Cabral de Pina Bulhões Di Giorgio" in html
        assert "miscrapha@gmail.com" in html
        assert "Política de Privacidade" in html
        assert "7 dias" in html and "ANPD" in html
        assert "[PENDENTE" not in html
        assert "Minuta em validação" not in html
        assert "<script" not in html.lower()
    print("PASS HTTPS privacy policy: 2 public routes, LGPD owner/contact and restrictive headers")

    # These pages are the four HTTPS metadata fields in the future directory.
    # Test actual Render routes with read-only requests, without echoing response data.
    listing_pages = {
        "/sobre": "Catálogo documental e simulações epidemiológicas",
        "/about": "Catálogo documental e simulações epidemiológicas",
        "/suporte": "Suporte e contato",
        "/support": "Suporte e contato",
        "/termos": "Termos de Uso",
        "/terms": "Termos de Uso",
    }
    for path, heading in listing_pages.items():
        req = Request(BASE + path, headers={"Accept": "text/html"}, method="GET")
        with urlopen(req, timeout=30) as response:
            assert response.status == 200, ("Listing page HTTP error", path)
            assert response.headers.get("Content-Type", "").startswith("text/html"), path
            assert response.headers.get("X-Content-Type-Options") == "nosniff", path
            assert response.headers.get("Cache-Control") == "no-store", path
            assert "default-src 'none'" in response.headers.get("Content-Security-Policy", ""), path
            page = response.read(100_000).decode("utf-8")
        assert '<html lang="pt-BR">' in page, path
        assert heading in page, path
        assert "Raphael Múcio Teixeira Cabral de Pina Bulhões Di Giorgio" in page, path
        assert "miscrapha@gmail.com" in page, path
        for link in ("/sobre", "/suporte", "/privacidade", "/termos"):
            assert BASE + link in page, (path, link)
        assert "<script" not in page.lower(), path
        assert "<form" not in page.lower(), path
        assert "[PENDENTE" not in page, path
    print("PASS HTTPS listing pages: 6 product/support/terms routes, owner and security headers")

    init = rpc("initialize", {
        "protocolVersion": "2025-11-25",
        "capabilities": {},
        "clientInfo": {"name": "public-smoke", "version": "1"},
    })
    assert init["result"]["serverInfo"]["name"].startswith("SINAN MCP")
    print("PASS MCP initialize")

    tools = rpc("tools/list", {})["result"]["tools"]
    names = {t["name"] for t in tools}
    assert names == set(CONTRACT["public_tools"]), (
        "Public MCP tool inventory differs from versioned synthetic contract",
        sorted(names),
    )
    print("PASS MCP tools/list: 10 read-only reference/demo tools")

    # Do not rely on SDK defaults: inspect actual JSON of the public HTTPS MCP.
    # These are safety *hints*, not substitutes for code isolation or auth.
    expected_annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }
    for item in tools:
        annotations = item.get("annotations")
        assert isinstance(annotations, dict), (
            "Missing public MCP safety annotations", item["name"]
        )
        for key, expected in expected_annotations.items():
            assert annotations.get(key) is expected, (
                "Incorrect public MCP safety annotation", item["name"], key
            )
    print("PASS MCP tools/list safety annotations: 10 explicit read-only, non-destructive, closed-world tools")

    server = tool("sobre_o_servidor", {})
    assert server["dados_reais_disponiveis"] is False
    assert server["acesso_microdados"] is False
    assert server["ferramentas_de_escrita"] is False
    assert server["modalidade"] == "publica_somente_leitura_sintetica"
    print("PASS MCP tool metadata: synthetic-only, no admin or real data")

    bases = tool("listar_bases", {})
    assert bases["dados_reais_disponiveis"] is False
    assert all(b["tipo_de_fonte"] == "synthetic" for b in bases["bases"])
    print("PASS MCP listar_bases: no real datasets")

    counts = tool("contar_notificacoes", {
        "agravo": "TUBE", "ano_inicio": 2024, "ano_fim": 2024,
        "uf": "PI", "por": "raca_cor",
    })
    assert counts["proveniencia"]["fonte"] == "synthetic-in-code/v1"
    assert "SINTÉTICO" in counts["aviso"]
    assert sum(x["notificacoes_ficticias"] for x in counts["resultado"]["dados"]) == 120
    print("PASS MCP contar_notificacoes: 120 explicitly fictional records")

    found = tool("pesquisar_agravos", {"termo": "hanseniase"})
    assert found["total_no_indice_curado"] >= 1
    assert any(x["codigo_interno"] == "HANS" for x in found["resultados"])
    assert all(x["dados_reais_disponiveis_no_mcp_publico"] is False
               for x in found["resultados"])
    print("PASS MCP catalogue: multi-disease references, zero real data")

    sources = tool("listar_fontes_oficiais", {})
    assert sources["natureza"] == "somente_metadados_de_navegacao"
    assert all(f["possui_valores_importados_neste_mcp"] is False
               for f in sources["fontes"])
    print("PASS MCP source links: official navigation metadata only")

    # Verify the deployed, versioned curation contract without visiting remote
    # sources, fetching documents or looking up any real SINAN records.
    doc_contract = CONTRACT["documentary_catalog"]
    audit = sources["auditoria_documental"]
    assert audit["schema_version"] == doc_contract["registry_schema"]
    assert audit["data_da_curadoria"] == doc_contract["curated_date"]
    assert audit["agravos_com_pagina_institucional"] == 14
    assert audit["referencias_de_paginas_institucionais"] == 17
    assert audit["dicionarios_anuais_confrontados"] == 0
    assert audit["arquivos_de_microdados_importados"] == 0
    assert audit["indicadores_epidemiologicos_homologados"] == 0
    assert audit["verificacao_ao_vivo_em_requisicoes_mcp"] is False

    doc = tool("descrever_agravo", {"codigo_interno": "ZIKA"})
    refs = doc["evidencia_por_agravo"]["referencias"]
    assert len(refs) == 2
    assert any(x["url"] == "https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus"
               for x in refs)
    assert all(x["arquivo_baixado_e_validado"] is False for x in refs)
    assert all(x["conteudo_integral_auditado"] is False for x in refs)
    assert [step["realizado"] for step in doc["checklist_pesquisa_antes_de_calcular"]] == [
        True, False, False, False, False,
    ]
    synonym = tool("pesquisar_agravos", {"termo": "escorpiao"})
    assert synonym["resultados"][0]["codigo_interno"] == "ANIM"
    assert synonym["resultados"][0]["arquivo_real_importado"] is False
    typo = tool("pesquisar_agravos", {"termo": "tuberculoze"})
    assert typo["resultados"] == []
    assert any(x["codigo_interno"] == "TUBE" and x["tipo"] == "sugestao_nao_resultado"
               for x in typo["sugestoes_de_grafia"])
    print("PASS MCP documentary provenance: 14 themes, 17 official pages, no real data, dated links, typo suggestions")

    for invalid in [
        ("contar_notificacoes", {
            "agravo": "DENG", "ano_inicio": 2024, "ano_fim": 2024,
            "uf": "PI", "por": "raca_cor",
        }),
        ("contar_notificacoes", {
            "agravo": "TUBE", "ano_inicio": 2024, "ano_fim": 2024,
            "uf": "PI", "municipio": "221100", "por": "sexo",
        }),
        ("importar-pysus", {}),
    ]:
        rejected = rpc("tools/call", {
            "name": invalid[0], "arguments": invalid[1],
        })
        assert ("error" in rejected or
                rejected.get("result", {}).get("isError") is True), (
                    "Unsafe tool call was not rejected", invalid[0]
                )
    print("PASS MCP rejected invalid/administrative calls")

    try:
        rpc("tools/list", {}, origin="https://evil.example.org")
    except HTTPError as exc:
        assert exc.code == 403, f"Unexpected Origin response: {exc.code}"
        print("PASS MCP rejects unapproved Origin")
    else:
        raise AssertionError("Unapproved Origin was accepted")

    print("PUBLIC HTTPS MCP SMOKE SUCCESS")


if __name__ == "__main__":
    main()
