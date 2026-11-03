"""Private, bounded extraction of provisional DBF identifiers from a local PDF.

For the catalogued SINAN Online 3.0 Dengue/Chikungunya document ONLY:
select capitalized words in its rightmost DBF table column. This is a
layout-specific *candidate extraction*, not a clinical codebook parser.
It never reads patient files; all extracted identifiers require page-by-page
human comparison and independent evidence that the document applies in 2024.

Not exposed through public MCP, HTTP, or ingestion/release pipelines.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .local_schema_review import (
    _prepare_template_dict,
    _local_pdf_hash,
    REGEX_FIELD,
    MAX_FIELDS,
    WARN,
    validate_candidate,
)

# Geometry of the rightmost DBF table column, established visually using the
# official 27-page SINAN Online v3.0 PDF. Other PDFs MUST have new reviewed
# extraction profiles instead of silently reusing these coordinates.
PDF_DOCUMENT_URL = (
    "https://portalsinan.saude.gov.br/images/documentos/Agravos/"
    "Dengue/DIC_DADOS_ONLINE.pdf"
)
SUPPORTED = {"DENG", "CHIK"}
ANCHORS = frozenset({"ID_AGRAVO", "DT_INVEST", "ID_OCUPA_N"})
MAX_PAGES = 40
MAX_WORDS_PAGE = 12000
MAX_CANDIDATE_WORDS = 2500
MIN_START_RATIO = 0.845
MAX_END_RATIO = 0.998
MIN_TOP_RATIO = 0.06
MAX_BOTTOM_RATIO = 0.90
EXCLUDED = frozenset({
    "DBF", "SINAN", "ONLINE", "REVISADO", "DENGUE",
    "CHIKUNGUNYA", "DADOS", "CAMPO", "ANO", "VERSAO",
})

# Human-reviewed, page-specific false positives in the rightmost text region
# of the 2015 official PDF. Page 14 has a standalone "A" in the continued
# explanatory paragraph on bairros; it is NOT a DBF column identifier.
# Do not generalize this exception to other documents or pages.
REVIEWED_FALSE_POSITIVES = frozenset({("A", 14)})


def _scan_official_pdf_draft(pdf_path: str | Path) -> tuple[list[dict], dict]:
    try:
        import pymupdf as fitz
    except ImportError:
        raise RuntimeError(
            "Extração PDF opcional ausente: pip install -e '.[pdfaudit]'"
        ) from None

    p = Path(pdf_path).expanduser()
    if not p.is_file() or p.is_symlink():
        raise ValueError("PDF local não foi localizado")
    # Confirm the recorded file name and a PDF header before invoking parser.
    _local_pdf_hash(p, expected_url=PDF_DOCUMENT_URL)

    try:
        with fitz.open(str(p), filetype="pdf") as pdf:
            if pdf.needs_pass or not 2 <= pdf.page_count <= MAX_PAGES:
                raise ValueError("PDF cifrado ou com número de páginas inesperado")
            candidates: dict[str, int] = {}
            n_ambiguous = 0
            n_repeated = 0
            n_reviewed_false_positive = 0
            n_words = 0
            for page_idx in range(1, pdf.page_count):
                page = pdf.load_page(page_idx)
                if not 300 < page.rect.width < 1600:
                    raise ValueError("Dimensões de página fora do perfil de extração")
                words = page.get_text("words", sort=True)
                if len(words) > MAX_WORDS_PAGE:
                    raise ValueError("Quantidade de tokens excessiva no PDF")
                for word in words:
                    left, top, right, bottom, token = word[:5]
                    if (left < MIN_START_RATIO * page.rect.width
                            or right > MAX_END_RATIO * page.rect.width
                            or top < MIN_TOP_RATIO * page.rect.height
                            or bottom > MAX_BOTTOM_RATIO * page.rect.height):
                        continue
                    token = token.strip(" ,.;:\t\r\n")
                    if (token, page_idx + 1) in REVIEWED_FALSE_POSITIVES:
                        n_reviewed_false_positive += 1
                        continue
                    if token in EXCLUDED:
                        continue
                    if REGEX_FIELD.fullmatch(token):
                        n_words += 1
                        if n_words > MAX_CANDIDATE_WORDS:
                            raise ValueError("PDF contém tokens suspeitos em excesso")
                        if token in candidates:
                            n_repeated += 1
                        else:
                            candidates[token] = page_idx + 1
                    elif "_" in token:
                        # DBF-looking but accent/case/length invalid. Never
                        # silently transliterate an official field name.
                        n_ambiguous += 1
    except ValueError:
        raise
    except Exception:
        # PDF parsers can include source bytes in exception strings.
        raise ValueError("PDF não pôde ser processado com perfil controlado") from None

    if not ANCHORS <= candidates.keys():
        raise ValueError(
            "Ancoragem falhou: o extrator não reconheceu o padrão DBF "
            "deste PDF. Exige revisão manual do layout, sem criar candidato."
        )
    if not 3 <= len(candidates) <= MAX_FIELDS:
        raise ValueError("Quantia extraída fora do limite de revisão")
    names = [
        {"name": name, "pdf_page_1_based": page}
        for name, page in sorted(candidates.items(), key=lambda a: (a[1], a[0]))
    ]
    return names, {
        
        "quantidade_palavras_ambiguidade_ou_acento": n_ambiguous,
        "ocorrencias_de_nome_repetido_no_pdf": n_repeated,
        "falsos_positivos_revisados_excluidos": n_reviewed_false_positive,
        "campos_ancora_localizados": len(ANCHORS),
    }


def gerar_rascunho_pdf_dbf_local(
    resource_id: str, pdf_path: str | Path, destino: str | Path,
) -> dict:
    """Generate a private unreviewed candidate; never assert 2024 validation."""
    basic = _prepare_template_dict(resource_id, pdf_path)
    if basic["agravo"] not in SUPPORTED or basic["dictionary_url"] != PDF_DOCUMENT_URL:
        raise ValueError("Somente o perfil PDF Dengue/Chikungunya está curado")
    fields, diagnostics = _scan_official_pdf_draft(pdf_path)
    basic["campos_dbf"] = fields
    basic["cobertura"] = "excerto_parcial"
    basic["situacao_transcricao"] = "manual_nao_revisada"
    validate_candidate(basic)

    target = Path(destino).expanduser()
    if (target.is_symlink() or target.suffix.lower() != ".json"
            or not target.parent.is_dir() or target.parent.is_symlink()):
        raise ValueError("Destino privado JSON inválido")
    fd = os.open(str(target), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(basic, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    except BaseException:
        try:
            target.unlink()
        except OSError:
            pass
        raise
    return {
        "schema_version": "sinan-private-pdf-dbf-extraction-summary-v1",
        "agravo": basic["agravo"],
        "ano_rotulado_no_portal": basic["ano_rotulado_no_portal"],
        "resource_id": resource_id,
        "pdf_sha256_local": basic["pdf_sha256_local_observado"],
        "campos_candidatos_extraidos": len(fields),
        "campos_ancora_localizados": diagnostics["campos_ancora_localizados"],
        "nomes_ambiguos_nao_normalizados": diagnostics[
            "quantidade_palavras_ambiguidade_ou_acento"
        ],
        "nomes_repetidos_no_pdf": diagnostics[
            "ocorrencias_de_nome_repetido_no_pdf"
        ],
        "falsos_positivos_revisados_excluidos": diagnostics[
            "falsos_positivos_revisados_excluidos"
        ],
        "cobertura_declarada": "excerto_parcial",
        "transcricao_verificada_independentemente": False,
        "codigo_de_agravo_e_ano_validado": False,
        "dicionario_aplicavel_2024_confirmado": False,
        "dados_reais_lidos": False,
        "publicacao_autorizada": False,
        "aviso": (
            "Campos CANDIDATOS lidos da coluna DBF do PDF local de 2015. "
            "Revisar página por página inclusive nomes com acento e anomalias. "
            + WARN
        ),
    }
