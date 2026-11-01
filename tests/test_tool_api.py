"""Security and provenance contract tests; synthetic data only."""
import pytest
from sinan_mcp.demo import build_demo
from sinan_mcp.tool_api import (
    abandono_publico, contagens_publicas, descrever_campos_publicos,
    listar_bases_publicas,
)


@pytest.fixture
def db(tmp_path):
    path = tmp_path / 'synthetic.db'
    build_demo(path)
    return path


def test_demo_and_provenance(db):
    bases = listar_bases_publicas(db)
    assert bases['bases'][0]['tipo_de_fonte'] == 'synthetic'
    assert 'n_registros' not in str(bases)
    assert 'identificador' not in str(bases)
    x = contagens_publicas(db, agravo='TUBE', ano_inicio=2024,
                          ano_fim=2024, uf='PI', por='raca_cor')
    assert x['schema_version'] == '0.2'
    assert x['proveniencia']['tipo_de_fonte'] == 'synthetic'
    assert {r['categoria'] for r in x['resultado']['dados']} == {'1', '4'}
    assert all(not r['suprimido'] for r in x['resultado']['dados'])
    tb = abandono_publico(db, ano_inicio=2024, ano_fim=2024, uf='PI')
    assert tb['tipo'] == 'proporcao_exploratoria_TB'
    assert 'Não é o indicador oficial' in tb['limitacoes'][0]
    assert descrever_campos_publicos()['politica'] == x['politica']


@pytest.mark.parametrize('params', [
    {'ano_inicio': 2024, 'ano_fim': 2025, 'uf': 'PI', 'por': 'raca_cor'},
    {'ano_inicio': 2024, 'ano_fim': 2024, 'uf': None, 'por': 'raca_cor'},
    {'ano_inicio': 2024, 'ano_fim': 2024, 'uf': 'PI', 'por': 'total'},
    {'ano_inicio': 2024, 'ano_fim': 2024, 'uf': 'PI', 'por': 'ano'},
    {'ano_inicio': 2024, 'ano_fim': 2024, 'uf': 'PI', 'por': 'sexo', 'municipio': '221100'},
    {'ano_inicio': 2024, 'ano_fim': 2024, 'uf': 'PI', 'por': 'uf'},
])
def test_disclosure_guard_prevents_differencing_api(db, params):
    with pytest.raises(ValueError):
        contagens_publicas(db, agravo='TUBE', **params)


def test_snapshot_missing_or_wrong_year(db):
    with pytest.raises(ValueError, match='não importada'):
        contagens_publicas(db, agravo='TUBE', ano_inicio=2023,
                          ano_fim=2023, uf='PI')


def test_no_individual_fields_surface(db):
    import json
    for output in [listar_bases_publicas(db),
                   contagens_publicas(db, agravo='TUBE', ano_inicio=2024, ano_fim=2024, uf='PI'),
                   abandono_publico(db, ano_inicio=2024, ano_fim=2024, uf='PI')]:
        text = json.dumps(output)
        for forbidden in ['NM_PACIENT', 'NU_NOTIFIC', 'ID_MN_RESI']:
            assert forbidden not in text


def test_mcp_in_memory_client(db, monkeypatch):
    # Tests a real MCP session when SDK v2 is installed (CI installs it).
    pytest.importorskip('mcp')
    from mcp import Client
    from sinan_mcp.server import mcp
    monkeypatch.setenv('SINAN_DB_PATH', str(db))
    import asyncio

    async def probe():
        async with Client(mcp, raise_exceptions=True) as client:
            definitions = await client.list_tools()
            tools = {t.name for t in definitions.tools}
            assert {'listar_bases', 'descrever_campos', 'contar_notificacoes',
                    'proporcao_abandono_tuberculose', 'listar_agravos',
                    'metodologia_abandono_tuberculose'} <= tools
            output = await client.call_tool('contar_notificacoes', {
                'agravo': 'TUBE', 'ano_inicio': 2024, 'ano_fim': 2024,
                'uf': 'PI', 'por': 'raca_cor'
            })
            assert not output.is_error
            result = output.structured_content
            assert result is not None
            assert result.get('proveniencia', {}).get('ano_do_arquivo') == 2024
            method = await client.call_tool('metodologia_abandono_tuberculose', {})
            assert not method.is_error
            assert method.structured_content['situacao'] == 'NAO_OFICIAL'
    asyncio.run(probe())


def test_demo_refuses_existing_real_database(tmp_path):
    from sinan_mcp.core import ingest_csv
    import csv
    path = tmp_path / 'research.db'
    csv_path = tmp_path / 'data.csv'
    with csv_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['ID_MN_RESI', 'CS_RACA'])
        writer.writeheader()
        writer.writerow({'ID_MN_RESI': '221100', 'CS_RACA': '4'})
    ingest_csv(path, csv_path, agravo='TUBE', ano=2024)
    with pytest.raises(ValueError, match='dados não sintéticos'):
        build_demo(path)


def test_mcp_stdio_subprocess(db):
    pytest.importorskip('mcp')
    from mcp import Client, StdioServerParameters
    import asyncio
    import sys
    params = StdioServerParameters(command=sys.executable,
                                   args=['-m', 'sinan_mcp', '--db', str(db), 'servir'])

    async def probe():
        async with Client(params) as client:
            names = {t.name for t in (await client.list_tools()).tools}
            assert 'contar_notificacoes' in names
            result = await client.call_tool('contar_notificacoes', {
                'agravo': 'TUBE', 'ano_inicio': 2024, 'ano_fim': 2024,
                'uf': 'PI', 'por': 'sexo'})
            assert not result.is_error
            assert result.structured_content['proveniencia']['tipo_de_fonte'] == 'synthetic'
    asyncio.run(probe())
