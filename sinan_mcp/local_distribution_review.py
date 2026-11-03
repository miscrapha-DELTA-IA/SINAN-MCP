"""Administrative offline ZIP file inspection for an exact curated official resource.

Requires an already obtained ZIP on a controlled local machine. Never
downloads, extracts, decompresses or opens rows/patient records. A locally
observed SHA-256 is not a published or digitally signed official checksum.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import stat
import zipfile

from .official_annual_resources import _index

MAX_ARCHIVE_BYTES = 3 * 1024**3
MAX_UNCOMPRESSED_BYTES = 10 * 1024**3
MAX_RATIO = 1000


def conferir_zip_recurso_local(resource_id: str, arquivo: str | Path) -> dict:
    """Bounded, conservative ZIP central-directory inspection, no data extraction."""
    if not isinstance(resource_id, str):
        raise ValueError("Informe um ID UUID curado")
    _, items = _index()
    record = next((i for i in items if i["resource_id"] == resource_id), None)
    if record is None:
        raise ValueError("ID de recurso ausente do registro oficial curado")
    p = Path(arquivo).expanduser()
    if p.is_symlink() or not p.is_file():
        raise ValueError("Arquivo local ausente ou link simbólico")
    size = p.stat().st_size
    if not 22 <= size <= MAX_ARCHIVE_BYTES:
        raise ValueError("ZIP local vazio, incompleto ou acima do limite")
    if p.name != record["archive_filename"]:
        raise ValueError("Nome do ZIP difere do recurso anual publicado")

    digest = hashlib.sha256()
    total = 0
    with p.open("rb") as stream:
        if stream.read(4) != b"PK\x03\x04":
            raise ValueError("Assinatura inicial ZIP não reconhecida")
        stream.seek(0)
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            total += len(block)
            if total > size or total > MAX_ARCHIVE_BYTES:
                raise ValueError("Arquivo alterado durante leitura")
            digest.update(block)
    if total != size or p.stat().st_size != size:
        raise ValueError("Arquivo alterado durante leitura")

    try:
        with zipfile.ZipFile(p, mode="r", allowZip64=True) as z:
            members = z.infolist()
            if len(members) != 1:
                raise ValueError("ZIP deve conter um único recurso e nenhum anexo")
            only = members[0]
            expected = record["archive_filename"][:-4]
            if (only.filename != expected or only.is_dir()
                    or only.flag_bits & 0x1
                    or only.compress_type not in (
                        zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED
                    )):
                raise ValueError("Entrada ZIP desconhecida, criptografada ou insegura")
            if stat.S_IFMT((only.external_attr >> 16) & 0xFFFF) == stat.S_IFLNK:
                raise ValueError("ZIP com link simbólico bloqueado")
            if (only.file_size < 1 or only.file_size > MAX_UNCOMPRESSED_BYTES
                    or only.compress_size < 1
                    or only.file_size > MAX_RATIO * only.compress_size):
                raise ValueError("ZIP excede limites contra descompactação excessiva")
    except (zipfile.BadZipFile, zipfile.LargeZipFile, EOFError, OSError):
        raise ValueError("ZIP local inválido ou com metadados corrompidos") from None

    return {
        "schema_version": "sinan-local-official-resource-zip-inspection-v1",
        "resource_id": record["resource_id"],
        "agravo": record["agravo_alias_interno"],
        "ano_rotulado_no_portal": record["ano_rotulado_no_portal"],
        "formato_declarado": record["distribution_format"],
        "arquivo_pacote_sha256_local": digest.hexdigest(),
        "arquivo_pacote_bytes_local": size,
        "arquivo_zip_estrutura_compativel_com_nome_registrado": True,
        "arquivos_extraidos": 0,
        "conteudo_clinico_lido": False,
        "origem_dos_bytes_autenticada": False,
        "checksum_oficial_disponivel_para_comparacao": False,
        "dicionario_aplicavel_validado": False,
        "status_preliminar_final_confirmado": False,
        "liberado_para_analise_epidemiologica": False,
        "publicacao_autorizada": False,
        "aviso": (
            "Cabeçalho, diretório ZIP, nome e SHA-256 local conferidos. "
            "Qualquer operador pode produzir outro ZIP com os mesmos nomes. "
            "O resultado NÃO comprova download do órgão, integridade "
            "oficial, identidade de pacientes, dicionário ou indicador. "
            "Nenhum conteúdo de registros foi descompactado."
        ),
    }
