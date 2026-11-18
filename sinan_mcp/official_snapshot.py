"""Local-only, fail-closed capture of the observed DATASUS TUBE/2019 DBC.

The official FTP server is not cryptographically authenticated; the locally
computed SHA-256 pins the received bytes, not their authenticity. Never make
this file or its contents available through public MCP or Git.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from ftplib import FTP
from pathlib import Path
from typing import Callable

from .source_edition import HOST, ROOT, inspect_tb_edition

YEAR = 2019
NAME = "TUBEBR19.dbc"
DIR = f"{ROOT}/FINAIS"
# Observed by local metadata-only FTP on 2026-11-18; NOT an official checksum.
OBSERVED_SIZE = 5_289_464
OBSERVED_MDTM = "20251015195757"
MAX_BYTES = 20 * 1024 * 1024


def _mdtm(ftp: FTP, name: str) -> str | None:
    reply = ftp.sendcmd("MDTM " + name)
    return reply[4:].strip() if reply.startswith("213 ") and len(reply.strip()) == 18 else None


def capture_tb_2019(*, root: Path | str = "./data/private/tb2019",
                    ftp_factory: Callable[[], FTP] = FTP) -> dict:
    """Fetch only a pinned edition into gitignored data/, then hash locally."""
    root = Path(root).resolve()
    data_dir = Path("./data").resolve()
    if not root.is_relative_to(data_dir):
        raise ValueError("Destino deve permanecer dentro de ./data/ (ignorado pelo Git).")

    discovery = inspect_tb_edition(YEAR, ftp_factory=ftp_factory)
    item = discovery["pastas"]["FINAIS"]
    if (discovery["situacao_catalogo"] != "arquivo_em_finais_observado"
            or item.get("tamanho_bytes") != OBSERVED_SIZE
            or item.get("modificado_utc") != OBSERVED_MDTM):
        raise RuntimeError("A fonte oficial nao corresponde aos metadados fixados; download recusado.")

    root.mkdir(parents=True, exist_ok=True)
    destination = root / NAME
    manifest = root / "TUBEBR19.manifest.json"
    staging = root / "TUBEBR19.dbc.partial"
    if any(p.exists() for p in (destination, manifest, staging)):
        raise FileExistsError("Snapshot local ja existe; nao sobrescrever. Verifique data/private/tb2019/.")

    ftp = None
    digest = hashlib.sha256()
    total = 0
    try:
        ftp = ftp_factory()
        ftp.connect(HOST, 21, timeout=20)
        ftp.login()
        ftp.cwd(DIR)
        ftp.voidcmd("TYPE I")
        if ftp.size(NAME) != OBSERVED_SIZE or _mdtm(ftp, NAME) != OBSERVED_MDTM:
            raise RuntimeError("O arquivo mudou entre a descoberta e a transferencia; recusado.")

        with staging.open("xb") as stream:
            def consume(chunk: bytes) -> None:
                nonlocal total
                total += len(chunk)
                if total > MAX_BYTES or total > OBSERVED_SIZE:
                    raise ValueError("Transferencia excedeu o limite declarado.")
                stream.write(chunk)
                digest.update(chunk)
            ftp.retrbinary("RETR " + NAME, consume, blocksize=64 * 1024)
        if total != OBSERVED_SIZE:
            raise ValueError("Transferencia incompleta; arquivo descartado.")
        staging.rename(destination)
        record = {
            "stage": "OFFICIAL_FTP_FILE_RECEIVED_NOT_HOMOLOGATED",
            "agravo": "TUBE", "ano_do_arquivo": YEAR,
            "servidor": HOST, "ftp_path": DIR + "/" + NAME,
            "bytes_observados": total, "sha256_recebido": digest.hexdigest(),
            "mdtm_servidor": OBSERVED_MDTM,
            "capturado_em_utc": datetime.now(timezone.utc).isoformat(),
            "origem_criptograficamente_autenticada": False,
            "equivalencia_com_parquet_pysus": False,
            "status_final_homologado": False,
            "publicacao_autorizada": False,
            "aviso": "Hash calculado localmente de dados recebidos via FTP sem TLS; nao e checksum oficial e nao prova equivalencia com o PySUS."
        }
        with manifest.open("x", encoding="utf-8") as out:
            json.dump(record, out, ensure_ascii=False, indent=2)
            out.write("\n")
        return record
    except BaseException:
        staging.unlink(missing_ok=True)
        # Do not leave an undocumented raw snapshot if the manifest failed.
        if not manifest.exists():
            destination.unlink(missing_ok=True)
        raise
    finally:
        if ftp is not None:
            try:
                ftp.close()
            except OSError:
                pass
