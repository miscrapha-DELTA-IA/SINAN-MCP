from pathlib import Path
import csv
import pytest
from sinan_mcp.core import (
    ingest_csv, catalogo, contar, abandono_tb, project_record, validate_agravo
)


def prepare(tmp_path: Path):
    rows = []
    # Piauí; 30 curas e 20 abandonos entre 50 encerramentos elegíveis
    for i in range(50):
        rows.append({"ID_MN_RESI": "221100", "CS_SEXO": "M" if i % 2 else "F",
                     "CS_RACA": "4", "SITUA_ENCE": "2" if i < 20 else "1",
                     "NM_PACIENT": f"SEGREDO_{i}", "NU_NOTIFIC": str(i)})
    # Contagem abaixo do limite e sem resultado estimável
    for i in range(4):
        rows.append({"ID_MN_RESI": "220770", "CS_SEXO": "M", "CS_RACA": "1", "SITUA_ENCE": "10"})
    file = tmp_path / "tb.csv"
    with file.open("w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["ID_MN_RESI", "CS_SEXO", "CS_RACA", "SITUA_ENCE", "NM_PACIENT", "NU_NOTIFIC"])
        wr.writeheader()
        for r in rows:
            wr.writerow(r)
    db = tmp_path / "safe.sqlite3"
    ingest_csv(db, file, agravo="TUBE", ano=2024, status="preliminar")
    return db


def test_import_projection_and_catalog(tmp_path):
    db = prepare(tmp_path)
    contents = db.read_bytes()
    assert b"SEGREDO" not in contents
    assert b"NM_PACIENT" not in contents
    c = catalogo(db)
    assert c["total_bases"] == 1
    assert c["bases_importadas"][0]["n_registros"] == 54
    assert c["bases_importadas"][0]["status"] == "preliminar"


def test_privacy_count_and_outcome(tmp_path):
    db = prepare(tmp_path)
    result = contar(db, agravo="TUBE", ano_inicio=2024, ano_fim=2024, uf="PI", por="raca_cor")
    groups = {r["categoria"]: r for r in result["dados"]}
    assert groups["4"]["notificacoes"] == 50
    assert groups["1"]["notificacoes"] is None
    assert groups["1"]["suprimido"]
    outcome = abandono_tb(db, uf="PI", ano_inicio=2024, ano_fim=2024, por="raca_cor")
    g = {r["categoria"]: r for r in outcome["dados"]}
    assert g["4"]["n_abandono"] == 20
    assert g["4"]["n_elegiveis"] == 50
    assert g["4"]["proporcao_percentual"] == 40.0
    assert g["1"]["proporcao_percentual"] is None


def test_repeat_no_duplicates(tmp_path):
    db = prepare(tmp_path)
    ingest_csv(db, tmp_path / "tb.csv", agravo="TUBE", ano=2024)
    assert contar(db, agravo="TUBE", por="total")["dados"][0]["notificacoes"] == 54
    assert catalogo(db)["total_bases"] == 1


def test_bad_input(tmp_path):
    db = prepare(tmp_path)
    with pytest.raises(ValueError):
        validate_agravo("TUBE'; DROP TABLE registros;--")
    with pytest.raises(ValueError):
        contar(db, agravo="TUBE", por="NM_PACIENT")
    with pytest.raises(ValueError):
        contar(db, agravo="TUBE", uf="PI", municipio="355030")
    with pytest.raises(ValueError):
        contar(db, agravo="TUBE", por="municipio")


def test_outcome_complementary_suppression(tmp_path):
    db = prepare(tmp_path)
    # 30 curas + 20 abandonos => não suprimido; consulta filtrada por sexo
    r = abandono_tb(db, uf="PI", por="sexo")
    assert all(not c["suprimido"] for c in r["dados"])  # 10 abandonos e 15 curas por sexo
    sexos = {x["categoria"]: x for x in r["dados"]}
    assert sexos["F"]["proporcao_percentual"] == 40.0
    assert sexos["M"]["proporcao_percentual"] == round(14 / 29 * 100, 2)


def test_rest_adapter_local(tmp_path, monkeypatch):
    import json
    import threading
    from http.server import ThreadingHTTPServer
    from urllib.request import Request, urlopen
    from sinan_mcp.rest import Handler
    db = prepare(tmp_path)
    monkeypatch.setenv("SINAN_DB_PATH", str(db))
    monkeypatch.setenv("SINAN_PUBLIC_REAL_DATA", "1")
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{srv.server_port}"
        with urlopen(base + "/health", timeout=2) as r:
            assert json.load(r)["status"] == "ok"
        req = Request(base + "/v1/contagens",
                      data=json.dumps({"agravo": "TUBE", "ano_inicio": 2024, "ano_fim": 2024, "uf": "PI", "por": "raca_cor"}).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=2) as r:
            body = json.load(r)
        assert body["resultado"]["status"] == "nao_divulgavel"
        assert body["resultado"]["dados"] == []
        assert body["proveniencia"]["ano_do_arquivo"] == 2024
        assert "SEGREDO" not in json.dumps(body)
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=2)
