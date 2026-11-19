"""Metadata-only regression; no remote FTP network and no health records."""
from ftplib import error_perm

import pytest

from sinan_mcp.source_edition import inspect_tb_edition


class FakeFTP:
    def __init__(self, listing, *, fails=None):
        self.listing = listing
        self.fails = fails or set()
        self.dir = ""

    def connect(self, host, port, timeout):
        assert host == "ftp.datasus.gov.br" and port == 21 and timeout <= 15

    def login(self):
        pass

    def cwd(self, directory):
        self.dir = directory.rsplit("/", 1)[-1]
        if self.dir in self.fails:
            raise error_perm("550 unavailable")

    def nlst(self):
        return self.listing.get(self.dir, [])

    def voidcmd(self, cmd):
        assert cmd == "TYPE I"

    def size(self, name):
        return 1234

    def sendcmd(self, cmd):
        return "213 20260507160800"

    def close(self):
        pass


def factory(listing, *, fails=None):
    return lambda: FakeFTP(listing, fails=fails)


def test_2019_appears_in_finais_but_never_approved():
    x = inspect_tb_edition(2019, ftp_factory=factory({"FINAIS": ["TUBEBR19.dbc"], "PRELIM": []}))
    assert x["situacao_catalogo"] == "arquivo_em_finais_observado"
    assert x["pastas"]["FINAIS"]["tamanho_bytes"] == 1234
    assert x["pastas"]["FINAIS"]["modificado_utc"] == "20260507160800"
    assert x["status_final_homologado"] is False
    assert x["publicacao_autorizada"] is False


def test_2024_prelim_only_never_approved():
    x = inspect_tb_edition(2024, ftp_factory=factory({"FINAIS": [], "PRELIM": ["TUBEBR24.dbc"]}))
    assert x["situacao_catalogo"] == "arquivo_em_prelim_observado"
    assert x["status_final_homologado"] is False


def test_network_failure_is_unknown_not_false_negative():
    x = inspect_tb_edition(2019, ftp_factory=factory({"PRELIM": []}, fails={"FINAIS"}))
    assert x["situacao_catalogo"] == "desconhecido"
    assert x["pastas"]["FINAIS"]["encontrado"] is None
    assert x["erros_de_consulta"]["FINAIS"] == "error_perm"


def test_discrepant_directories_not_final():
    x = inspect_tb_edition(2019, ftp_factory=factory({"FINAIS": ["TUBEBR19.dbc"], "PRELIM": ["TUBEBR19.dbc"]}))
    assert x["situacao_catalogo"] == "duplicidade_entre_diretorios"
    assert x["publicacao_autorizada"] is False


@pytest.mark.parametrize("bad", [None, True, 2000, 2100, "2019"])
def test_invalid_years_rejected(bad):
    with pytest.raises(ValueError):
        inspect_tb_edition(bad, ftp_factory=factory({}))

def test_documented_module_entrypoint_has_help_without_network():
    """Catch sys.path errors when invoked from a fresh checkout."""
    import subprocess
    import sys
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[1]
    cp = subprocess.run(
        [sys.executable, "-m", "scripts.auditar_edicao_tb", "--help"],
        cwd=repository_root,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert cp.returncode == 0, cp.stderr
    assert "--anos" in cp.stdout
