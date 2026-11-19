"""Metadata-only DATASUS SINAN/TUBE edition discovery.

This does not download DBC, access PySUS Parquet or approve data releases.
Missing/unreachable FTP entries are never interpreted as a final release.
"""
from __future__ import annotations

from ftplib import FTP, all_errors
from typing import Any

HOST = "ftp.datasus.gov.br"
ROOT = "/dissemin/publicos/SINAN/DADOS"
DIRECTORIES = ("FINAIS", "PRELIM")


def _listing(ftp: FTP, year: int, kind: str) -> dict[str, Any]:
    filename = f"TUBEBR{year % 100:02d}.dbc"
    directory = f"{ROOT}/{kind}"
    ftp.cwd(directory)
    names = ftp.nlst()
    found = filename.lower() in {name.rsplit("/", 1)[-1].lower() for name in names}
    if not found:
        return {"encontrado": False, "caminho": None}
    metadata: dict[str, Any] = {
        "encontrado": True,
        "caminho": f"{directory}/{filename}",
        "tamanho_bytes": None,
        "modificado_utc": None,
    }
    try:
        ftp.voidcmd("TYPE I")
        metadata["tamanho_bytes"] = ftp.size(filename)
    except all_errors:
        pass
    try:
        reply = ftp.sendcmd("MDTM " + filename)
        if reply.startswith("213 ") and len(reply.strip()) == 18:
            metadata["modificado_utc"] = reply[4:].strip()
    except all_errors:
        pass
    return metadata


def inspect_tb_edition(year: int, *, ftp_factory=FTP) -> dict[str, Any]:
    """Inspect official FTP metadata only; never returns or reads microdata."""
    if type(year) is not int or not 2001 <= year <= 2099:
        raise ValueError("Ano de TUBE fora do intervalo 2001–2099")
    evidence: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for kind in DIRECTORIES:
        ftp = None
        try:
            ftp = ftp_factory()
            ftp.connect(HOST, 21, timeout=12)
            ftp.login()
            evidence[kind] = _listing(ftp, year, kind)
        except all_errors as exc:
            errors[kind] = type(exc).__name__
            evidence[kind] = {"encontrado": None, "caminho": None}
        finally:
            if ftp is not None:
                try:
                    ftp.close()
                except all_errors:
                    pass
    final, prelim = evidence["FINAIS"]["encontrado"], evidence["PRELIM"]["encontrado"]
    if final is True and prelim is False:
        status = "arquivo_em_finais_observado"
    elif prelim is True and final is False:
        status = "arquivo_em_prelim_observado"
    elif final is True and prelim is True:
        status = "duplicidade_entre_diretorios"
    else:
        status = "desconhecido"
    return {
        "agravo": "TUBE",
        "ano_do_arquivo": year,
        "servidor": HOST,
        "pastas": evidence,
        "erros_de_consulta": errors,
        "situacao_catalogo": status,
        "equivalencia_pysus_dbc_verificada": False,
        "status_final_homologado": False,
        "publicacao_autorizada": False,
        "observacao": (
            "Diretório, tamanho e MDTM são metadados mutáveis. "
            "Exige checksum oficial do DBC, comparacao reprodutivel "
            "do conteúdo transformado e revisoes científica e de privacidade."
        ),
    }
