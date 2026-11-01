"""Núcleo isolado do protocolo MCP: ingestão controlada e consultas agregadas.

Nenhuma função neste módulo disponibiliza registros individuais para o cliente.
Os dados são locais, não há endpoints de saúde pública que recebam consultas.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

UF_CODIGOS = dict(zip(
    ["11", "12", "13", "14", "15", "16", "17", "21", "22", "23", "24", "25", "26", "27", "28", "29", "31", "32", "33", "35", "41", "42", "43", "50", "51", "52", "53"],
    ["RO", "AC", "AM", "RR", "PA", "AP", "TO", "MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA", "MG", "ES", "RJ", "SP", "PR", "SC", "RS", "MS", "MT", "GO", "DF"]
))
UF_SIGLAS = frozenset(UF_CODIGOS.values())
AGRAVOS = {
    "TUBE": "Tuberculose", "DENG": "Dengue", "CHIK": "Chikungunya",
    "ZIKA": "Zika", "HANS": "Hanseníase", "SIFA": "Sífilis adquirida",
    "SIFC": "Sífilis congênita", "HEPA": "Hepatites virais",
    "MENI": "Meningite", "VIOL": "Violência interpessoal/autoprovocada",
    "LEIV": "Leishmaniose visceral", "LTAN": "Leishmaniose tegumentar",
    "ANIM": "Acidentes com animais peçonhentos", "COQU": "Coqueluche",
}
CAMPOS = {
    "ano": "Ano da base/arquivo importado, NÃO necessariamente ano de diagnóstico ou de notificação.",
    "uf": "UF de residência inferida pelo código do município de residência (quando disponível).",
    "municipio": "Código do município de residência (IBGE, seis dígitos) presente na base.",
    "sexo": "CS_SEXO; M, F, I ou ausente. Não inferir identidade de gênero.",
    "raca_cor": "CS_RACA; 1 Branca, 2 Preta, 3 Amarela, 4 Parda, 5 Indígena, 9 Ignorado.",
    "situacao_encerramento": "SITUA_ENCE (apenas TB neste MVP): 1 Cura; 2 Abandono; 10 Abandono primário. Confirmar dicionário por ano.",
}
GROUP_COLS = {"ano": "r.ano", "uf": "r.uf", "municipio": "r.municipio", "sexo": "r.sexo", "raca_cor": "r.raca_cor", "total": "'total'"}


def db_connect(path: str | Path) -> sqlite3.Connection:
    dbpath = Path(path).expanduser()
    dbpath.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(dbpath), timeout=30)
    con.row_factory = sqlite3.Row
    con.executescript("""
    PRAGMA busy_timeout=30000;
    CREATE TABLE IF NOT EXISTS fontes (
        chave TEXT PRIMARY KEY, agravo TEXT NOT NULL, ano INTEGER NOT NULL,
        tipo_fonte TEXT NOT NULL, identificador TEXT NOT NULL,
        status TEXT NOT NULL, sha256 TEXT,
        atualizado_em TEXT NOT NULL, n_registros INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS registros (
        chave TEXT NOT NULL, agravo TEXT NOT NULL, ano INTEGER NOT NULL,
        uf TEXT, municipio TEXT, sexo TEXT, raca_cor TEXT, situacao_encerramento TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_sinan_filtro ON registros (agravo, ano, uf, municipio);
    CREATE INDEX IF NOT EXISTS idx_sinan_tube ON registros (agravo, ano, situacao_encerramento);
    """)
    return con


def db_connect_readonly(path: str | Path) -> sqlite3.Connection:
    """Never create, alter or initialize a database during a public query.

    Unlike db_connect(), this connection is query-only and fails closed when
    an administrator has not initialized a local SQLite database.
    """
    dbpath = Path(path).expanduser().resolve()
    if not dbpath.is_file():
        raise ValueError("Banco não inicializado. Importe uma base local pela CLI.")
    con = sqlite3.connect(dbpath.as_uri() + "?mode=ro", uri=True, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    con.execute("PRAGMA busy_timeout=15000")
    return con


def _str(value: Any) -> str | None:
    if value is None:
        return None
    # pandas NaN / NA podem gerar exceções em comparação
    s = str(value).strip()
    if not s or s.upper() in {"NAN", "NONE", "NULL", "<NA>", "NA"}:
        return None
    return s


def _code(value: Any) -> str | None:
    s = _str(value)
    if s is not None and re.fullmatch(r"\d+\.0", s):
        return s[:-2]
    return s


def _first(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and _str(row[key]) is not None:
            return row[key]
    return None


def project_record(raw: Mapping[str, Any], agravo: str, ano: int) -> tuple:
    """Projeção estrita: descarta nomes, endereços, números de notificação etc."""
    row = {str(k).upper().strip(): v for k, v in raw.items() if k is not None}
    mun = _code(_first(row, "ID_MN_RESI", "MUNIC_RES", "MUNICIPIO_RESIDENCIA"))
    if mun and re.fullmatch(r"\d{6,7}", mun):
        if len(mun) == 7:
            mun = mun[:6]  # adaptar código IBGE de sete dígitos ao padrão SINAN de seis
    else:
        mun = None
    coduf = mun[:2] if mun else _code(_first(row, "ID_UF"))
    uf = UF_CODIGOS.get(coduf or "")
    if uf is None:
        sigla = _str(_first(row, "UF_RESIDENCIA"))
        uf = sigla.upper() if sigla and sigla.upper() in UF_SIGLAS else None
    sexo = _str(_first(row, "CS_SEXO"))
    sexo = sexo.upper() if sexo and sexo.upper() in {"M", "F", "I"} else None
    raca = _code(_first(row, "CS_RACA"))
    raca = raca if raca in {"1", "2", "3", "4", "5", "9"} else None
    situacao = _code(_first(row, "SITUA_ENCE")) if agravo == "TUBE" else None
    if situacao and not re.fullmatch(r"\d{1,3}", situacao):
        situacao = None
    return (agravo, ano, uf, mun, sexo, raca, situacao)


def validate_agravo(agravo: str) -> str:
    a = agravo.strip().upper()
    if not re.fullmatch(r"[A-Z]{4}", a):
        raise ValueError("Código de agravo inválido: use quatro letras, ex.: TUBE ou DENG")
    return a


def _import_rows(db_path: str | Path, rows: Iterable[Mapping[str, Any]], *,
                 agravo: str, ano: int, identificador: str, tipo_fonte: str,
                 status: str, sha256: str | None = None) -> dict:
    agravo = validate_agravo(agravo)
    if not 1980 <= ano <= 2100:
        raise ValueError("Ano fora do intervalo permitido")
    if status not in {"final", "preliminar", "desconhecido"}:
        raise ValueError("status deve ser final, preliminar ou desconhecido")
    chave = hashlib.sha256(f"{agravo}|{ano}|{tipo_fonte}|{identificador}".encode()).hexdigest()
    n = 0
    con = db_connect(db_path)
    try:
        with con:
            # Somente um snapshot ativo por agravo/ano: evita contagem dupla
            # quando a mesma base é carregada via CSV e depois via PySUS.
            con.execute("DELETE FROM registros WHERE chave IN (SELECT chave FROM fontes WHERE agravo = ? AND ano = ?)", (agravo, ano))
            con.execute("DELETE FROM fontes WHERE agravo = ? AND ano = ?", (agravo, ano))
            batch = []
            for row in rows:
                # Refuse unexpected schemas, preserving existing snapshots.
                if n == 0 and not batch:
                    fields = {str(key).strip().upper() for key in row}
                    expected = {"ID_MN_RESI", "MUNIC_RES", "CS_SEXO", "CS_RACA", "SITUA_ENCE"}
                    if not fields.intersection(expected):
                        raise ValueError("Esquema do SINAN não reconhecido: faltam colunas básicas de residência ou demografia")
                batch.append((chave, *project_record(row, agravo, ano)))
                if len(batch) == 2000:
                    con.executemany("INSERT INTO registros VALUES (?,?,?,?,?,?,?,?)", batch)
                    n += len(batch)
                    batch.clear()
            if batch:
                con.executemany("INSERT INTO registros VALUES (?,?,?,?,?,?,?,?)", batch)
                n += len(batch)
            if n == 0:
                raise ValueError("Fonte sem registros; snapshot anterior foi preservado")
            con.execute("INSERT INTO fontes VALUES (?,?,?,?,?,?,?,?,?)", (
                chave, agravo, ano, tipo_fonte, identificador, status, sha256,
                datetime.now(timezone.utc).isoformat(), n))
    finally:
        con.close()
    return {"agravo": agravo, "ano_base": ano, "registros_importados": n,
            "status": status, "origem": identificador, "sha256": sha256,
            "aviso": "Projeção sem identificadores diretos. NÃO comprova anonimização irreversível."}


def ingest_csv(db_path: str | Path, arquivo: str | Path, *, agravo: str, ano: int,
               status: str = "desconhecido", encoding: str = "utf-8-sig", delimiter: str = "auto") -> dict:
    p = Path(arquivo).expanduser().resolve(strict=True)
    if p.suffix.lower() != ".csv":
        raise ValueError("A ingestão local aceita CSV; use --pysus para DBC/Parquet")
    sha = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    def rows():
        with p.open("r", encoding=encoding, newline="") as f:
            if delimiter == "auto":
                sample = f.read(8192)
                f.seek(0)
                try:
                    delim = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
                except csv.Error:
                    delim = ","
            else:
                if delimiter not in {",", ";", "\t", "|"}:
                    raise ValueError("Delimitador deve ser vírgula, ponto e vírgula, tab ou pipe")
                delim = delimiter
            reader = csv.DictReader(f, delimiter=delim)
            if not reader.fieldnames:
                raise ValueError("CSV não contém cabeçalho")
            names = {x.upper().strip() for x in reader.fieldnames if x is not None}
            if not names.intersection({"ID_MN_RESI", "CS_SEXO", "CS_RACA", "SITUA_ENCE"}):
                raise ValueError("CSV sem colunas esperadas do SINAN. Confira o dicionário do agravo")
            yield from reader
    return _import_rows(db_path, rows(), agravo=agravo, ano=ano,
                        identificador=p.name, tipo_fonte="csv-local", status=status, sha256=sha.hexdigest())


def ingest_pysus(db_path: str | Path, *, agravo: str, ano: int,
                 status: str = "desconhecido", source: str = "catalog") -> dict:
    """Admin-only wrapper over the PySUS FileBag streaming importer.

    The MCP tool surface cannot invoke this function. PySUS is optional.
    """
    from .pysus_gateway import importar
    return importar(db_path, agravo=agravo, ano=ano, source=source, status=status)


def diagnosticar_base(db_path: str | Path, agravo: str, ano: int) -> dict:
    """LOCAL administrative diagnostic. Never exposed to an LLM or REST.

    Counts and missingness can be disclosure-sensitive and must stay local.
    """
    agravo = validate_agravo(agravo)
    con = db_connect(db_path)
    try:
        base = con.execute("SELECT tipo_fonte, status, atualizado_em FROM fontes WHERE agravo=? AND ano=?", (agravo, ano)).fetchone()
        if base is None:
            raise ValueError(f"Base {agravo}/{ano} não importada")
        stats = con.execute("""SELECT COUNT(*) n,
            SUM(CASE WHEN uf IS NULL THEN 1 ELSE 0 END) sem_uf,
            SUM(CASE WHEN municipio IS NULL THEN 1 ELSE 0 END) sem_municipio,
            SUM(CASE WHEN sexo IS NULL OR sexo = 'I' THEN 1 ELSE 0 END) sexo_ausente_ignorado,
            SUM(CASE WHEN raca_cor IS NULL OR raca_cor = '9' THEN 1 ELSE 0 END) raca_ausente_ignorada,
            SUM(CASE WHEN situacao_encerramento IS NULL THEN 1 ELSE 0 END) encerramento_ausente
            FROM registros WHERE agravo=? AND ano=?""", (agravo, ano)).fetchone()
        n = stats["n"]
        def pct(value):
            return round((value or 0) * 100.0 / n, 2) if n else None
        return {"agravo": agravo, "ano_do_arquivo": ano,
                "fonte": dict(base), "n_registros_administrativo": n,
                "completude": {key: {"ausentes_ou_ignorados": stats[key], "percentual": pct(stats[key])}
                               for key in ["sem_uf", "sem_municipio", "sexo_ausente_ignorado", "raca_ausente_ignorada", "encerramento_ausente"]
                               if agravo == "TUBE" or key != "encerramento_ausente"},
                "limites": "Relatório administrativo sensível; não publicar em API/LLM. O ano é do arquivo, não de notificação."}
    finally:
        con.close()


def _filters(agravo: str, ano_inicio: int | None, ano_fim: int | None,
             uf: str | None, municipio: str | None) -> tuple[str, list[Any]]:
    agravo = validate_agravo(agravo)
    clauses = ["r.agravo = ?"]
    params: list[Any] = [agravo]
    if ano_inicio is not None:
        if not 1980 <= ano_inicio <= 2100:
            raise ValueError("ano_inicio fora do intervalo")
        clauses.append("r.ano >= ?")
        params.append(ano_inicio)
    if ano_fim is not None:
        if not 1980 <= ano_fim <= 2100:
            raise ValueError("ano_fim fora do intervalo")
        clauses.append("r.ano <= ?")
        params.append(ano_fim)
    if ano_inicio is not None and ano_fim is not None and ano_inicio > ano_fim:
        raise ValueError("ano_inicio posterior a ano_fim")
    if uf is not None:
        uf = uf.strip().upper()
        if uf not in UF_SIGLAS:
            raise ValueError("UF inválida")
        clauses.append("r.uf = ?")
        params.append(uf)
    if municipio is not None:
        municipio = municipio.strip()
        if not re.fullmatch(r"\d{6}", municipio):
            raise ValueError("Município deve ser código IBGE SINAN com seis dígitos")
        clauses.append("r.municipio = ?")
        params.append(municipio)
        if uf and UF_CODIGOS.get(municipio[:2]) != uf:
            raise ValueError("UF e município incompatíveis")
    return " AND ".join(clauses), params


def catalogo(db_path: str | Path) -> dict:
    con = db_connect_readonly(db_path)
    try:
        rows = con.execute("SELECT agravo, ano, tipo_fonte, status, identificador, sha256, atualizado_em, n_registros FROM fontes ORDER BY agravo, ano DESC").fetchall()
        return {"bases_importadas": [dict(row) for row in rows], "total_bases": len(rows),
                "origens_oficiais": ["https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/svsa/agravos-de-notificacoes/agravos-de-notificacoes",
                                      "https://pysus.readthedocs.io/en/latest/"],
                "observacao": "Bases não são atualizadas em tempo real. O ano representa o arquivo importado."}
    finally:
        con.close()


def contar(db_path: str | Path, *, agravo: str, ano_inicio: int | None = None,
           ano_fim: int | None = None, uf: str | None = None, municipio: str | None = None,
           por: str = "ano", limiar: int = 10) -> dict:
    if por not in GROUP_COLS:
        raise ValueError("por deve ser ano, uf, municipio, sexo, raca_cor ou total")
    if por == "municipio" and uf is None:
        raise ValueError("Para agregar por município, informe UF para limitar a consulta")
    if not 10 <= limiar <= 100:
        raise ValueError("limiar entre 10 e 100")
    where, params = _filters(agravo, ano_inicio, ano_fim, uf, municipio)
    col = GROUP_COLS[por]
    con = db_connect_readonly(db_path)
    try:
        rows = con.execute(f"SELECT {col} AS categoria, COUNT(*) AS n FROM registros r WHERE {where} GROUP BY {col} ORDER BY categoria LIMIT 201", params).fetchall()
        if len(rows) > 200:
            raise ValueError("Mais de 200 categorias; restrinja os anos, a UF ou o município")
        return {"agravo": agravo.upper(), "agrupar_por": por, "filtros": {"ano_inicio": ano_inicio, "ano_fim": ano_fim, "uf": uf, "municipio": municipio},
                "dados": [{"categoria": row["categoria"] if row["categoria"] is not None else "ignorado/ausente",
                           "notificacoes": row["n"] if row["n"] >= limiar else None,
                           "suprimido": row["n"] < limiar} for row in rows],
                "limiar_minimo": limiar,
                "definicao": "Contagem de registros das bases importadas; não necessariamente casos únicos ou incidência.",
                "privacidade": "Contagens abaixo do limiar são ocultadas. Essa proteção isolada não garante anonimização contra ataques por diferença."}
    finally:
        con.close()


def abandono_tb(db_path: str | Path, *, ano_inicio: int | None = None,
                 ano_fim: int | None = None, uf: str | None = None,
                 municipio: str | None = None, por: str = "raca_cor", limiar: int = 10) -> dict:
    if por not in {"ano", "uf", "sexo", "raca_cor", "total"}:
        raise ValueError("por deve ser ano, uf, sexo, raca_cor ou total")
    if not 10 <= limiar <= 100:
        raise ValueError("limiar entre 10 e 100")
    where, params = _filters("TUBE", ano_inicio, ano_fim, uf, municipio)
    col = GROUP_COLS[por]
    con = db_connect_readonly(db_path)
    try:
        rows = con.execute(f"""SELECT {col} AS categoria,
                   COUNT(*) AS n,
                   SUM(CASE WHEN r.situacao_encerramento IN ('2','10') THEN 1 ELSE 0 END) AS aband
                   FROM registros r WHERE {where} AND r.situacao_encerramento IN ('1','2','10')
                   GROUP BY {col} ORDER BY categoria LIMIT 201""", params).fetchall()
        if len(rows) > 200:
            raise ValueError("Muitas categorias; restrinja os filtros")
        result = []
        for row in rows:
            n, a = row["n"], row["aband"] or 0
            proteger = n < limiar or a < limiar or n - a < limiar
            result.append({"categoria": row["categoria"] if row["categoria"] is not None else "ignorado/ausente",
                           "n_elegiveis": None if proteger else n,
                           "n_abandono": None if proteger else a,
                           "proporcao_percentual": None if proteger else round(a / n * 100, 2),
                           "suprimido": proteger})
        return {"indicador": "Proporção exploratória de desfechos de abandono (não é indicador oficial do MS)",
                "filtros": {"ano_inicio": ano_inicio, "ano_fim": ano_fim, "uf": uf, "municipio": municipio},
                "agrupar_por": por, "dados": result,
                "numerador": "SITUA_ENCE ∈ {2 (abandono), 10 (abandono primário)}",
                "denominador": "Registros com SITUA_ENCE ∈ {1 (cura), 2 (abandono), 10 (abandono primário)}",
                "restricoes": "Sem deduplicação longitudinal; excluir casos sem encerramento válido. A elegibilidade e as codificações devem ser verificadas no dicionário específico de cada ano. Não confundir com taxa oficial de abandono, incidência ou risco individual.",
                "privacidade": f"Suprime grupos se denominador < {limiar}, numerador < {limiar} ou complemento < {limiar}. Não é garantia de anonimização."}
    finally:
        con.close()


def dicionario() -> dict:
    return {"agravos_exemplos": AGRAVOS, "variaveis_expostas": CAMPOS,
            "orientacao": "Consultar dicionários originais do SINAN por agravo/versão, em especial SITUA_ENCE e possíveis mudanças de codificação.",
            "documentacao": "https://portalsinan.saude.gov.br/tuberculose",
            "politica": "Somente agregações; nenhuma ferramenta de consulta individual, SQL arbitrário ou acesso direto a microdados."}
