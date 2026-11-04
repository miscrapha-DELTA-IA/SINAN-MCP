"""Offline reviewer handoff made ONLY from public curated Zika PDF metadata.

The generated Markdown contains a 37-field worksheet, seven unresolved
documentary caveats and source-page links. It neither reads the private
operator checklist nor declares a human signature, approval or annual
ZIKABR24 compatibility.
"""
from __future__ import annotations

import os
from pathlib import Path

from .zika_pdf_37_field_curation import carregar_transcricao_zika_pdf

SCHEMA = "sinan-zika-public-documentary-reviewer-handoff-v1"
MAX_MD_BYTES = 36_000


def _cell(value: object) -> str:
    """Bound and escape authored documentary text for safe Markdown cells."""
    if not isinstance(value, str) or len(value) > 500:
        raise ValueError("Celula do dossie documental invalida")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("Caracter de controle em fonte documental")
    return (value.replace("\\", "\\\\")
            .replace("|", "\\|")
            .replace("[", "\\[")
            .replace("]", "\\]"))


def montar_roteiro_revisor_zika() -> str:
    """No network, patients, private notes, PDFs or external review status."""
    source = carregar_transcricao_zika_pdf()
    assert source["documentary_fields_transcribed"] == 37
    assert len(source["issues_requiring_independent_review"]) == 7
    url = source["source_pdf"]
    flagged = {i["campo"] for i in source["issues_requiring_independent_review"]}
    pages = {f["campo"]: f["pagina_pdf"] for f in source["documentary_field_rows"]}
    chunks = [
        "# Roteiro para segunda conferência independente — Dicionário Zika",
        "",
        "**RASCUNHO DOCUMENTAL PARA CONFERÊNCIA HUMANA, NÃO É PARECER ASSINADO.**",
        "",
        "O material reproduz exclusivamente a transcrição candidata de um",
        "PDF público. **Não inclui notas do operador nem dados clínicos**.",
        "Não é evidência de que os arquivos `ZIKABR24` usem esses 37 campos.",
        "",
        f"Fonte pública: [PDF Zika do Ministério da Saúde]({url}) (8 páginas).",
        f"Página do recurso oficial: {source['source_resource_page']}",
        "Identificador SHA-256 **do catálogo versionado**, não do PDF oficial:",
        f"`{source['local_catalog_sha256_not_official_pdf_hash']}`",
        "",
        "## Instruções ao revisor",
        "",
        "Conferir no documento original, por página, o nome, tipo,",
        "descrição, domínio e regras condicionais de cada campo. Preencher",
        "as colunas de decisão e nota com base na evidência **efetivamente**",
        "inspecionada. Campos ambíguos devem continuar como pendentes.",
        "As caixas vazias e os espaços em branco não indicam aprovação.",
        "Este roteiro não autentica a identidade, qualificação ou assinatura",
        "do avaliador. Formalização e custódia são responsabilidades externas.",
        "",
        "## Checklist de 37 campos — todos NÃO CONFERIDOS nesta emissão",
        "",
        "| Nº | Página do PDF | Campo | Tipo do PDF | Descrição resumida | Ressalva? | Conferência humana | Nota / correção |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for row in source["documentary_field_rows"]:
        name = row["campo"]
        page = row["pagina_pdf"]
        page_link = f"[{page}]({url}#page={page})"
        chunks.append(
            "| {seq} | {page} | `{name}` | `{kind}` | {desc} | {flagged} | [ ] | __________ |".format(
                seq=row["seq"],
                page=page_link,
                name=_cell(name),
                kind=_cell(row["tipo_documental"]),
                desc=_cell(row["significado_resumido"]),
                flagged="Sim" if name in flagged else "Não",
            )
        )
    chunks.extend([
        "",
        "## Sete ressalvas documentais a tratar separadamente",
        "",
        "| Campo | Página do PDF | Ressalva da transcrição candidata | Análise externa / decisão |",
        "|---|---|---|---|",
    ])
    for issue in source["issues_requiring_independent_review"]:
        name = issue["campo"]
        page = pages[name]
        chunks.append(
            f"| `{_cell(name)}` | [{page}]({url}#page={page}) | "
            f"{_cell(issue['motivo'])} | __________ |"
        )
    chunks.extend([
        "",
        "## Registro externo — preencher exclusivamente após conferência",
        "",
        "- Identificação do avaliador e vínculo institucional: __________________",
        "- Data e edição do PDF efetivamente conferido: __________________",
        "- Hash calculado localmente do PDF (não equivale a hash oficial): __________________",
        "- Declaração de independência, método e limitações: __________________",
        "- Correções propostas e páginas correspondentes: __________________",
        "- Divergências ainda não resolvidas: __________________",
        "- Parecer externo assinado, se houver: **arquivo separado**, sujeito",
        "  a verificação institucional independente. Nenhuma assinatura é criada",
        "  ou validada por este roteiro.",
        "",
        "## Proibições e pendências científicas",
        "",
        "O PDF descreve um dicionário histórico do Sinan Net, **não** valida",
        "o cabeçalho da distribuição ZIKA/2024 ou a sua data de corte.",
        "Não usar como contrato de importação, critério de exclusão, cálculo",
        "epidemiológico ou autorização de publicação. As sete ressalvas e",
        "os dez tópicos científicos do projeto continuam pendentes",
        "até que haja avaliação independente e decisões institucionais.",
        "",
        "**Campos reais de ZIKABR24 lidos: 0. Indicadores homologados: 0.**",
        "**Revisão independente autenticada: NÃO. Publicação autorizada: NÃO.**",
        "",
    ])
    result = "\n".join(chunks)
    if len(result.encode("utf-8")) > MAX_MD_BYTES:
        raise ValueError("Dossie excede tamanho esperado")
    return result


def preparar_roteiro_revisor_zika(saida: str | Path) -> dict:
    """Write ONLY a new .md file outside Git; do not open any private files."""
    out = Path(saida).expanduser()
    if (out.suffix.lower() != ".md" or out.is_symlink()
            or not out.parent.is_dir() or out.parent.is_symlink()):
        raise ValueError("Destino do roteiro Markdown invalido")
    folder = out.parent.resolve()
    if any((part / ".git").exists() for part in (folder, *folder.parents)):
        raise ValueError("Roteiro de revisao nao pode ser criado dentro do Git")
    raw = montar_roteiro_revisor_zika().encode("utf-8")
    fd = os.open(str(out), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
    except BaseException:
        try:
            out.unlink()
        except OSError:
            pass
        raise
    return {
        "schema_version": SCHEMA,
        "roteiro_criado": True,
        "campos_publicos_para_conferencia": 37,
        "ressalvas_publicas_para_conferencia": 7,
        "notas_privadas_lidas": False,
        "pdf_baixado_ou_inspecionado_pelo_comando": False,
        "campos_reais_zikabr24_lidos": 0,
        "parecer_independente_autenticado": False,
        "indicadores_homologados": 0,
        "publicacao_autorizada": False,
    }
