"""Offline PySUS adapter tests using fakes; no remote health data downloaded."""
from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

import pytest
from sinan_mcp import pysus_gateway as g
from sinan_mcp.core import catalogo, contar, diagnosticar_base, ingest_csv, ingest_pysus
from sinan_mcp.catalogue import listar_agravos, metodologia_tuberculose


class FileBag:
    def __init__(self, paths, local=None):
        self.paths = paths
        self.local = local
    def __iter__(self):
        return iter([SimpleNamespace(path=x) for x in self.paths])
    def download(self):
        if self.local is None:
            raise AssertionError('remote download not configured')
        return FileBag(self.local)


def test_discover_does_not_download(monkeypatch):
    args = []
    def fake_sinan(**kwargs):
        args.append(kwargs)
        return FileBag(['folder/TUBEBR24.parquet'])
    monkeypatch.setattr(g, '_pysus', lambda: SimpleNamespace(sinan=fake_sinan))
    result = g.descobrir('tube', 2024, source='origin')
    assert result['nomes_arquivos'] == ['TUBEBR24.parquet']
    assert result['download_realizado'] is False
    assert args[0] == {'disease':'TUBE','year':2024,'source':'origin','download':False,'as_dataframe':False}


def test_download_streamed_csv_with_fingerprint(tmp_path, monkeypatch):
    file = tmp_path / 'DENG24.csv'
    with file.open('w', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=['CS_RACA', 'CS_SEXO', 'ID_MN_RESI', 'NM_PACIENT'])
        writer.writeheader()
        for i in range(30):
            writer.writerow({'CS_RACA': '4','CS_SEXO':'F','ID_MN_RESI':'221100','NM_PACIENT': 'FICTICIO'})
    monkeypatch.setattr(g, '_pysus', lambda: SimpleNamespace(sinan=lambda **_: FileBag(['DENG24.csv'], [file])))
    db = tmp_path / 'data.sqlite3'
    result = ingest_pysus(db, agravo='DENG', ano=2024, status='preliminar')
    assert result['registros_importados'] == 30
    assert len(result['sha256']) == 64
    assert catalogo(db)['bases_importadas'][0]['tipo_fonte'] == 'pysus-catalog'
    assert contar(db, agravo='DENG', ano_inicio=2024, ano_fim=2024, uf='PI', por='raca_cor')['dados'][0]['notificacoes'] == 30
    assert b'FICTICIO' not in db.read_bytes()


def test_empty_or_invalid_import_cannot_destroy_snapshot(tmp_path):
    db = tmp_path / 'research.db'
    file = tmp_path / 'good.csv'
    file.write_text('CS_RACA,ID_MN_RESI\n4,221100\n', encoding='utf8')
    ingest_csv(db, file, agravo='TUBE', ano=2024)
    good = catalogo(db)['bases_importadas'][0]['n_registros']
    file.write_text('CS_RACA,ID_MN_RESI\n', encoding='utf8')
    with pytest.raises(ValueError, match='sem registros'):
        ingest_csv(db, file, agravo='TUBE', ano=2024)
    assert catalogo(db)['bases_importadas'][0]['n_registros'] == good
    file.write_text('NOME,IDADE\nAlice,35\n', encoding='utf8')
    with pytest.raises(ValueError, match='sem colunas esperadas'):
        ingest_csv(db, file, agravo='TUBE', ano=2024)
    assert catalogo(db)['bases_importadas'][0]['n_registros'] == good


def test_quality_report_admin_only(tmp_path):
    db = tmp_path / 'data.db'
    src = tmp_path / 'data.csv'
    src.write_text('CS_RACA,CS_SEXO,ID_MN_RESI,SITUA_ENCE\n9,I,221100,1\n4,F,221100,2\n', encoding='utf8')
    ingest_csv(db, src, agravo='TUBE', ano=2024)
    diagnostic = diagnosticar_base(db, 'TUBE', 2024)
    assert diagnostic['n_registros_administrativo'] == 2
    assert diagnostic['completude']['raca_ausente_ignorada']['percentual'] == 50
    assert diagnostic['completude']['sexo_ausente_ignorado']['ausentes_ou_ignorados'] == 1
    with pytest.raises(ValueError, match='não importada'):
        diagnosticar_base(db, 'DENG', 2024)


def test_refuse_unexpected_download_format(tmp_path, monkeypatch):
    src = tmp_path/'file.dbc'
    src.write_bytes(b'demo')
    monkeypatch.setattr(g, '_pysus', lambda: SimpleNamespace(sinan=lambda **_: FileBag(['file.dbc'], [src])))
    with pytest.raises(ValueError, match='não suportado'):
        ingest_pysus(tmp_path/'db.sqlite3', agravo='TUBE', ano=2024)


def test_missing_filebag_or_wrong_year(monkeypatch):
    monkeypatch.setattr(g, '_pysus', lambda: SimpleNamespace(sinan=lambda **_: FileBag([])))
    result = g.descobrir('TUBE', 2024)
    assert result['status'] == 'nao_confirmado'
    assert [x['status'] for x in result['tentativas']] == ['catalogo_vazio', 'catalogo_vazio']
    with pytest.raises(ValueError, match='Ano deve ser inteiro'):
        g.descobrir('TUBE', True)
    with pytest.raises(ValueError, match='source deve ser'):
        g.descobrir('TUBE', 2024, source='evil')


def test_curated_catalogue_explicitly_non_official():
    catalogue = listar_agravos()['agravos_piloto']
    assert {'TUBE','DENG'} <= set(catalogue)
    assert metodologia_tuberculose()['situacao'] == 'NAO_OFICIAL'


def test_download_streamed_parquet(tmp_path, monkeypatch):
    pa = pytest.importorskip('pyarrow')
    pq = pytest.importorskip('pyarrow.parquet')
    src = tmp_path / 'TUBEBR24.parquet'
    pq.write_table(pa.table({'ID_MN_RESI': ['221100'] * 64,
                             'CS_RACA': ['4'] * 64,
                             'CS_SEXO': ['F'] * 64,
                             'SITUA_ENCE': ['2'] * 64,
                             'NM_PACIENT': ['FICTICIO'] * 64}), src)
    monkeypatch.setattr(g, '_pysus', lambda: SimpleNamespace(sinan=lambda **_: FileBag(['TUBEBR24.parquet'], [src])))
    db = tmp_path/'data.db'
    result = ingest_pysus(db, agravo='TUBE', ano=2024)
    assert result['registros_importados'] == 64
    assert b'FICTICIO' not in db.read_bytes()


def test_discovery_auto_fallback_to_origin(monkeypatch):
    sources = []
    def fake_sinan(**kw):
        sources.append(kw['source'])
        return FileBag(['origin/TUBEBR24.parquet']) if kw['source'] == 'origin' else FileBag([])
    monkeypatch.setattr(g, '_pysus', lambda: SimpleNamespace(sinan=fake_sinan))
    result = g.descobrir('TUBE', 2024)
    assert sources == ['catalog', 'origin']
    assert result['status'] == 'encontrado'
    assert result['origem'] == 'pysus.ftp/origin'
    assert result['tentativas'][0]['status'] == 'catalogo_vazio'
    assert result['download_realizado'] is False


def test_discovery_empty_origin_not_misreported_as_missing_dataset(monkeypatch):
    monkeypatch.setattr(g, '_pysus', lambda: SimpleNamespace(sinan=lambda **kw: FileBag([])))
    result = g.descobrir('DENG', 2024, source='origin')
    assert result['status'] == 'nao_confirmado'
    assert result['tentativas'][0]['status'] == 'catalogo_vazio'
    assert 'NÃO significa ausência' in result['aviso']


def test_discovery_source_error_then_fallback(monkeypatch):
    def fake_sinan(**kwargs):
        if kwargs['source'] == 'catalog':
            raise TimeoutError('private connection details must not leak')
        return FileBag(['DENGBR24.parquet'])
    monkeypatch.setattr(g, '_pysus', lambda: SimpleNamespace(sinan=fake_sinan))
    result = g.descobrir('DENG', 2024)
    assert result['status'] == 'encontrado'
    assert result['tentativas'][0]['erro_tipo'] == 'TimeoutError'
    assert 'private connection details' not in str(result)


def test_create_isolated_cache_without_touching_existing(tmp_path, monkeypatch):
    import os
    from sinan_mcp.pysus_diagnostics import create_isolated_cache
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('PYSUS_CACHEPATH', raising=False)
    isolated = create_isolated_cache()
    assert isolated.is_dir()
    assert isolated.parent.name == 'data'
    assert os.environ['PYSUS_CACHEPATH'] == str(isolated.resolve())
    assert create_isolated_cache() != isolated


def test_discovery_code_explains_common_catalog_index(monkeypatch):
    monkeypatch.setattr(g, '_pysus', lambda: SimpleNamespace(sinan=lambda **_: FileBag([])))
    out = g.descobrir('TUBE', 2024)
    assert out['status'] == 'nao_confirmado'
    assert out['download_realizado'] is False
    assert 'NÃO significa ausência' in out['aviso']


def test_direct_catalog_query_returns_only_ftp_metadata(tmp_path, monkeypatch):
    duckdb = pytest.importorskip("duckdb")
    from sinan_mcp.catalog_fallback import lookup_local, lookup_after_pysus
    cache = tmp_path / "ducklake"
    cache.mkdir()
    db = cache / "catalog_sinan.duckdb"
    with duckdb.connect(str(db)) as con:
        con.execute("CREATE SCHEMA pysus")
        con.execute("CREATE TABLE pysus.dataset_groups (id INTEGER, name VARCHAR)")
        con.execute("CREATE TABLE pysus.files (path VARCHAR, group_id INTEGER, year INTEGER)")
        con.execute("INSERT INTO pysus.dataset_groups VALUES (1, 'TUBE'), (2, 'DENG')")
        con.execute("""INSERT INTO pysus.files VALUES
            ('public/data/ftp/sinan/TUBE/2024/_/BR/TUBEBR24.parquet', 1, 2024),
            ('public/data/ftp/sinan/DENG/2024/_/BR/DENGBR24.parquet', 2, 2024),
            ('public/data/dadosgov/sinan/TUBE/2024/TUBEOTHER.parquet', 1, 2024)""")
    monkeypatch.setenv("PYSUS_CACHEPATH", str(tmp_path))
    assert lookup_local("TUBE", 2024) == ["TUBEBR24.parquet"]
    assert lookup_local("DENG", 2024) == ["DENGBR24.parquet"]
    assert lookup_local("TUBE", 2023) == []
    assert lookup_after_pysus("TUBE", 2024) == ["TUBEBR24.parquet"]


def test_discovery_falls_back_to_catalog_sql(tmp_path, monkeypatch):
    duckdb = pytest.importorskip("duckdb")
    root = tmp_path / "ducklake"
    root.mkdir()
    with duckdb.connect(str(root / "catalog_sinan.duckdb")) as con:
        con.execute("CREATE SCHEMA pysus")
        con.execute("CREATE TABLE pysus.dataset_groups (id INTEGER, name VARCHAR)")
        con.execute("CREATE TABLE pysus.files (path VARCHAR, group_id INTEGER, year INTEGER)")
        con.execute("INSERT INTO pysus.dataset_groups VALUES (1,'TUBE')")
        con.execute("INSERT INTO pysus.files VALUES ('public/data/ftp/sinan/TUBE/2024/_/BR/TUBEBR24.parquet',1,2024)")
    monkeypatch.setenv("PYSUS_CACHEPATH", str(tmp_path))
    monkeypatch.setattr(g, "_pysus", lambda: SimpleNamespace(sinan=lambda **kwargs: FileBag([])))
    result = g.descobrir("TUBE", 2024)
    assert result["status"] == "encontrado"
    assert result["origem"] == "ducklake_sql_local/ftp-mirror"
    assert result["nomes_arquivos"] == ["TUBEBR24.parquet"]
    assert result["download_realizado"] is False
