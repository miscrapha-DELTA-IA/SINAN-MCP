"""Read only DBF header metadata for four approved TUBE/2019 fields.

The DBC is verified against the pinned local SHA-256 first. The converted DBF
stays inside a temporary, gitignored private directory. No rows, values or
categories are read, printed, uploaded or added to Git.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from .tb2019_parity import FIELDS, verify_local_dbc
from .tb2019_private_import import PRIVATE_ROOT

MAX_DBF_BYTES = 512 * 1024 * 1024


def inspect_header(root: Path | str | None = None) -> dict:
    root = (Path(root) if root is not None else PRIVATE_ROOT).resolve()
    dbc = verify_local_dbc(root)
    try:
        import pyreaddbc
        from dbfread import DBF
    except ImportError as exc:
        raise RuntimeError("Conversores locais ausentes: instalar pyreaddbc e dbfread") from None

    converter = getattr(pyreaddbc, "dbc2dbf", None)
    if not callable(converter):
        raise RuntimeError("API pyreaddbc.dbc2dbf indisponivel")

    with TemporaryDirectory(prefix="header-only-", dir=str(root)) as tmp:
        dbf = Path(tmp) / "TUBEBR19.header-audit.dbf"
        converter(str(dbc), str(dbf))
        if not dbf.is_file() or not 0 < dbf.stat().st_size <= MAX_DBF_BYTES:
            raise RuntimeError("DBC nao produziu DBF valido nos limites locais")
        # Opening DBF parses metadata; never iterate over any records.
        meta = DBF(str(dbf), encoding="iso-8859-1",
                   char_decode_errors="replace", load=False)
        names = {str(field.name).upper(): field for field in meta.fields}
        if len(names) != len(meta.fields) or not all(key in names for key in FIELDS):
            raise ValueError("Layout DBF nao contem as quatro variaveis")
        safe = {}
        for key in FIELDS:
            field = names[key]
            typ = str(field.type)
            length = int(field.length)
            if typ not in {"C", "N", "F", "L", "D", "I", "Y", "T", "B", "M", "0"} or not 0 < length <= 128:
                raise ValueError("Formato inesperado no cabecalho DBF")
            safe[key] = {"tipo_dbf": typ, "largura_bytes": length}

    return {
        "stage": "TUBE2019_DBF_FIELD_HEADER_INSPECTED_NOT_HOMOLOGATED",
        "ano_do_arquivo": 2019,
        "campos": safe,
        "campo_situacao_10_cabe_em_largura": safe["SITUA_ENCE"]["largura_bytes"] >= 2,
        "linhas_lidas": False,
        "microdados_exibidos": False,
        "compatibilidade_temporal_do_dicionario_verificada": False,
        "revisao_cientifica_independente": False,
        "publicacao_autorizada": False,
    }
