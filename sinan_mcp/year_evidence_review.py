"""Offline cross-check of *locally supplied* data and dictionary bytes.

Reports content integrity only. A copied, modified or counterfeit PDF may
have a perfectly valid SHA-256: without a publisher-signed digest and
independent source attestation it is NOT authentic and NOT applicable to any
year. No network, no MCP exposure, no raw data in output.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlsplit

from .provenance import load_manifest, verify_local_file
from .year_evidence_registry import consultar_evidencia_agravo_ano

MAX_DICTIONARY_BYTES = 30 * 1024 * 1024


def confrontar_documento_e_arquivo_local(
    manifesto: str | Path, arquivo_dados: str | Path,
    pdf_dicionario: str | Path,
) -> dict:
    """Tie a candidate source manifest to a catalogued document URL, not its authenticity."""
    doc = load_manifest(manifesto)
    registry = consultar_evidencia_agravo_ano(doc["agravo"], doc["ano_arquivo"])
    item = registry["evidencia_documental"]
    if item is None:
        raise ValueError("Não há referência documental curada para o agravo e o ano")
    if doc["url_dicionario"] != item["documento_url"]:
        raise ValueError(
            "URL do dicionário no manifesto não corresponde ao documento "
            "oficial exato que consta no catálogo"
        )
    source = verify_local_file(manifesto, arquivo_dados)

    path = Path(pdf_dicionario).expanduser()
    if path.is_symlink() or not path.is_file():
        raise ValueError("PDF local não encontrado ou fornecido por link simbólico")
    expected_name = urlsplit(item["documento_url"]).path.rsplit("/", 1)[-1]
    if path.name != expected_name:
        raise ValueError("Nome do PDF local diverge da referência documental")
    size = path.stat().st_size
    if not 8 <= size <= MAX_DICTIONARY_BYTES:
        raise ValueError("PDF local vazio ou acima do limite permitido")
    digest = hashlib.sha256()
    read = 0
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError("O arquivo do dicionário não apresenta assinatura PDF")
        stream.seek(0)
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            read += len(block)
            if read > size or read > MAX_DICTIONARY_BYTES:
                raise ValueError("PDF local cresceu durante a leitura")
            digest.update(block)
    if read != size:
        raise ValueError("PDF local alterado durante a leitura")
    return {
        "schema_version": "sinan-year-evidence-local-review-v1",
        "agravo": doc["agravo"],
        "ano_do_arquivo_pretendido": doc["ano_arquivo"],
        "estado": "somente_integridade_local_sem_atestacao_da_origem",
        "referencia_documento_url": item["documento_url"],
        "edicao_documental": item["edicao_documental"],
        "checksum_pdf_local_observado": digest.hexdigest(),
        "checksum_dados_locais_observado": source["arquivo_sha256"],
        "checksum_dados_compativel_com_manifesto_local": True,
        "pdf_compativel_com_formato_e_nome_esperados": True,
        "hash_pdf_independentemente_publicado_pelo_orgao": False,
        "conteudo_pdf_comparado_com_original_oficial": False,
        "identidade_fonte_oficial_verificada": False,
        "arquivo_dados_do_ano_autenticado": False,
        "codigo_download_oficial_confirmado": False,
        "sistema_origem_no_ano_confirmado": False,
        "status_consolidacao_documental_confirmado": False,
        "dicionario_compatibilidade_ao_ano_confirmada": False,
        "revisao_epidemiologica_independente": False,
        "revisao_de_privacidade_concluida": False,
        "autoriza_utilizacao_clinica": False,
        "autoriza_publicacao": False,
        "aviso": (
            "A identidade de um PDF não se prova apenas pelo nome, cabeçalho "
            "PDF ou SHA local. O arquivo e manifesto podem ter sido alterados "
            "por qualquer operador. Confirmar bytes, publicação e versões "
            "com fonte primária e parecer independente antes de vincular "
            "um dicionário a um ano, aprovar indicador ou divulgar agregados."
        ),
    }
