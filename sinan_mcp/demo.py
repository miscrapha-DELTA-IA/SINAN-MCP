"""Offline, synthetic-only first-run experience. Never downloads SINAN records."""
from __future__ import annotations

from pathlib import Path
import sqlite3
from .core import _import_rows


def build_demo(db: str | Path) -> dict:
    path = Path(db).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    # An explicit path may point at a real research database: never overwrite it.
    if path.exists() and path.stat().st_size:
        try:
            with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as con:
                rows = con.execute("SELECT COUNT(*) FROM fontes WHERE tipo_fonte <> 'synthetic'").fetchone()[0]
                if rows:
                    raise ValueError("Banco já contém dados não sintéticos; escolha outro --demo-db")
        except sqlite3.Error as exc:
            raise ValueError("Banco existente não é um banco SINAN válido; escolha outro --demo-db") from exc
    # Every example is fictional; no name, address or real identity is generated.
    def records():
        for i in range(120):
            yield {"ID_MN_RESI": "221100", "CS_SEXO": "F" if i % 2 else "M",
                   "CS_RACA": "4" if i < 70 else "1",
                   "SITUA_ENCE": "2" if (i < 70 and i % 3 == 0) or
                                     (i >= 70 and i % 4 == 0) else "1"}
    return _import_rows(path, records(), agravo="TUBE", ano=2024,
                        identificador="DEMO-SINTETICO-SEM-DADOS-REAIS",
                        tipo_fonte="synthetic", status="desconhecido")
