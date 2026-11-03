"""Administrative offline crosswalk: 2024-era Dengue PDF vs 2015 DBF PDF vs CSV ZIP.

NO access to patient rows; CSV first header line only. Never exposed over MCP.
The SHA here is from the user-supplied PDF, NOT an official signed checksum.
Other PDF editions require a separately reviewed profile.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import zipfile

from .local_distribution_review import conferir_zip_recurso_local
from .local_schema_review import _header_csv, _resource, load_candidate

PDF_BASENAME = "dic_dados_dengue.pdf"
OBSERVED_PDF_SHA256 = "d15122f38b32c4b3caf58cca7e717065b24c888771ecad8e7a3ed02e0efd16a1"
RESOURCE_ID = "4cf2f7b8-9920-41b5-817a-1ffc13e0690c"
EXPECTED_PAGES = 22
EXPECTED_ROWS = 121
EXPECTED_UNIQUE_NAMES = 120
FIELD = re.compile(r"[a-z][a-z0-9_]{0,31}\Z")
PDF_ROW = re.compile(r"[0-9]{1,3}\Z")
MAX_PDF_BYTES = 40 * 1024 * 1024
MAX_CELL_CHARS = 4096


def _pdf_local_hash(path: str | Path) -> str:
    p = Path(path).expanduser()
    if (p.is_symlink() or not p.is_file() or p.name != PDF_BASENAME
            or not 8 <= p.stat().st_size <= MAX_PDF_BYTES):
        raise ValueError("PDF não corresponde à referência documental curada")
    digest = hashlib.sha256()
    with p.open("rb") as f:
        if f.read(5) != b"%PDF-":
            raise ValueError("Cabeçalho PDF inválido")
        f.seek(0)
        n = 0
        for block in iter(lambda: f.read(1024 * 1024), b""):
            n += len(block)
            if n > MAX_PDF_BYTES:
                raise ValueError("PDF excede tamanho máximo")
            digest.update(block)
    if p.stat().st_size != n:
        raise ValueError("PDF mudou durante leitura")
    return digest.hexdigest()


def _table_rows(pdf) -> list[dict]:
    """Extract only numbered field/type/name cells by geometry, never clinical values."""
    try:
        import pymupdf
    except ImportError:
        raise RuntimeError("PyMuPDF opcional não instalado") from None
    rows = []
    for page_idx, page in enumerate(pdf, 1):
        tables = page.find_tables()
        for table in tables.tables:
            if table.col_count != 7:
                continue
            for r in table.rows:
                if len(r.cells) != 7 or any(r.cells[k] is None for k in (0, 1, 2, 3)):
                    continue
                cells = [
                    page.get_textbox(pymupdf.Rect(cell)).strip()
                    if cell is not None else ""
                    for cell in r.cells[:4]
                ]
                if any(len(s) > MAX_CELL_CHARS for s in cells):
                    raise ValueError("Célula de tabela maior que limite")
                if not PDF_ROW.fullmatch(cells[0]):
                    continue
                seq = int(cells[0])
                field = cells[2].replace("\n", "").replace(" ", "").strip()
                datatype = cells[3].replace("\n", "").replace(" ", "").strip()
                if not FIELD.fullmatch(field):
                    raise ValueError("Nome de coluna na tabela fora do perfil PDF")
                if not 1 <= seq <= EXPECTED_ROWS:
                    raise ValueError("Numeração de tabela fora do perfil")
                rows.append({
                    "seq": seq, "pdf_page_1_based": page_idx,
                    "name": field, "type_as_printed": datatype,
                    "label_as_printed": " ".join(cells[1].split())[:180],
                })
                if len(rows) > EXPECTED_ROWS:
                    raise ValueError("Excesso de entradas no PDF")
    return sorted(rows, key=lambda r: r["seq"])


def examinar_pdf_dengue_local(pdf_path: str | Path) -> dict:
    """Pin this exact shared 22-page PDF; fail closed for any other edition."""
    digest = _pdf_local_hash(pdf_path)
    if digest != OBSERVED_PDF_SHA256:
        raise ValueError("Hash do PDF não coincide com esta edição documental")
    try:
        import pymupdf
    except ImportError:
        raise RuntimeError("Instale o extra opcional pdfaudit") from None
    try:
        with pymupdf.open(str(pdf_path), filetype="pdf") as doc:
            if doc.needs_pass or len(doc) != EXPECTED_PAGES:
                raise ValueError("Número de páginas ou cifragem fora do perfil")
            rows = _table_rows(doc)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Não foi possível extrair as tabelas do PDF") from None

    if (len(rows) != EXPECTED_ROWS
            or [r["seq"] for r in rows] != list(range(1, EXPECTED_ROWS+1))):
        raise ValueError("Não foi possível recuperar as 121 linhas de tabela")
    names = {r["name"].upper() for r in rows}
    if len(names) != EXPECTED_UNIQUE_NAMES:
        raise ValueError("Quantidade de nomes distintos inesperada")
    duplicate_rows = [r for r in rows if r["name"] == "coufinf"]
    if [(r["seq"], r["pdf_page_1_based"]) for r in duplicate_rows] != [(64, 10), (67, 11)]:
        raise ValueError("Duplicação documental não corresponde ao perfil revisado")
    malformed = [r for r in rows if r["type_as_printed"] == "char()1"]
    if [r["seq"] for r in malformed] != [115, 116]:
        raise ValueError("Inconsistências de tipo não correspondem ao perfil")
    return {
        "pdf_sha256_local": digest,
        "linhas_documentadas": EXPECTED_ROWS,
        "nomes_documentais_distintos": len(names),
        "nomes_documentais": names,
        "duplicacoes": [
            {"name": "coufinf", "seq": r["seq"], "pagina": r["pdf_page_1_based"]}
            for r in duplicate_rows
        ],
        "tipos_malformados": [
            {"name": r["name"], "seq": r["seq"], "pagina": r["pdf_page_1_based"],
             "tipo_literal": r["type_as_printed"]}
            for r in malformed
        ],
    }


def _only_documented_crosswalk(
    doc_names: set[str], old_names: set[str], observed_names: set[str],
) -> dict:
    """No unknown CSV header names in return value."""
    return {
        "nome_comum_pdf_atual_csv": len(doc_names & observed_names),
        "nomes_pdf_atual_ausentes_csv": sorted(doc_names - observed_names),
        "quantidade_csv_fora_pdf_atual": len(observed_names - doc_names),
        "nome_comum_pdf2015_pdf_atual": len(old_names & doc_names),
        "nomes_pdf2015_ausentes_pdf_atual": sorted(old_names - doc_names),
        "nomes_pdf_atual_ausentes_pdf2015": sorted(doc_names - old_names),
    }


def confrontar_dengue_dicionarios_local(
    pdf_atual: str | Path, contrato_2015: str | Path,
    zip_2024: str | Path, destino: str | Path,
) -> dict:
    """Crosswalk an operator's private 2015 candidate and 2024 CSV ZIP HEADER."""
    pdf = examinar_pdf_dengue_local(pdf_atual)
    old = load_candidate(contrato_2015)
    if old["resource_id"] != RESOURCE_ID or old["format"] != "CSV":
        raise ValueError("Candidato de 2015 não é DENG/2024 CSV")
    inspected = conferir_zip_recurso_local(RESOURCE_ID, zip_2024)
    meta = _resource(RESOURCE_ID)
    archive_path = Path(zip_2024).expanduser()
    before = archive_path.stat()
    try:
        with zipfile.ZipFile(archive_path, "r") as arc:
            members = arc.infolist()
            if len(members) != 1 or members[0].filename != meta["archive_filename"][:-4]:
                raise ValueError("Entrada do ZIP não corresponde ao recurso curado")
            with arc.open(members[0], "r") as member:
                # Bounded 128 KiB FIRST CSV LINE ONLY: never reaches patient data.
                actual = _header_csv(member, old)
    except (OSError, zipfile.BadZipFile, EOFError):
        raise ValueError("Erro de leitura da estrutura do ZIP") from None
    after = archive_path.stat()
    if after.st_size != before.st_size or after.st_mtime_ns != before.st_mtime_ns:
        raise ValueError("Arquivo ZIP alterado durante inspeção")
    documentary = _only_documented_crosswalk(
        pdf["nomes_documentais"],
        {f["name"] for f in old["campos_dbf"]}, actual,
    )
    report = {
        "schema_version": "sinan-private-dengue-crosswalk-candidate-v1",
        "resource_id": RESOURCE_ID,
        "agravo": "DENG",
        "ano_rotulado_no_portal": 2024,
        "pdf_atual_sha256_local": pdf["pdf_sha256_local"],
        "zip_sha256_local": inspected["arquivo_pacote_sha256_local"],
        "pdf2015_sha256_local": old["pdf_sha256_local_observado"],
        "n_campos_csv": len(actual),
        "n_entradas_pdf_atual": pdf["linhas_documentadas"],
        "n_nomes_unicos_pdf_atual": pdf["nomes_documentais_distintos"],
        "n_nomes_pdf2015_candidato": len(old["campos_dbf"]),
        **documentary,
        "duplicacoes_no_pdf_atual": pdf["duplicacoes"],
        "tipos_inconsistentes_no_pdf_atual": pdf["tipos_malformados"],
        "linhas_de_pacientes_lidas": 0,
        "campos_csv_desconhecidos_incluidos_no_parecer": False,
        "sha256_oficial_autenticado": False,
        "dicionario_aplicavel_a_exportacao_2024_validado": False,
        "transcricao_revisada_independentemente": False,
        "status_revisao": "PENDENTE",
        "autorizacao_analise_real": False,
        "publicacao_autorizada": False,
        "aviso": (
            "Compara NOMES de campos somente. Documentos de versões distintas "
            "podem usar semânticas, tipos e domínios incompatíveis. 121 entradas "
            "de PDF != 121 colunas verificadas; duplicatas documentais bloqueiam "
            "qualquer declaração de completude. Requer revisão epidemiológica "
            "independente e de privacidade."
        ),
    }
    out = Path(destino).expanduser()
    if (out.is_symlink() or out.suffix.lower() != ".json"
            or not out.parent.is_dir() or out.parent.is_symlink()):
        raise ValueError("Destino de parecer privado inválido")
    fd = os.open(str(out), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except BaseException:
        try:
            out.unlink()
        except OSError:
            pass
        raise
    # CLI response never lists unknown header names nor other patient values.
    return {
        "total_pdf_atual": pdf["linhas_documentadas"],
        "unicos_pdf_atual": pdf["nomes_documentais_distintos"],
        "csv_observados": len(actual),
        "comuns_pdf_atual_csv": documentary["nome_comum_pdf_atual_csv"],
        "ausentes_csv_do_pdf_atual": len(documentary["nomes_pdf_atual_ausentes_csv"]),
        "adicionais_csv_fora_pdf_atual": documentary["quantidade_csv_fora_pdf_atual"],
        "duplicacoes_pdf_atual": len(pdf["duplicacoes"]) - 1,
        "tipos_malformados_pdf_atual": len(pdf["tipos_malformados"]),
        "revisao": "PENDENTE",
        "publicacao_autorizada": False,
    }
