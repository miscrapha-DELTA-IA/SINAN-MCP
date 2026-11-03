"""Offline and metadata-only roadmap readiness inventory for ANY referenced agravo/year.

This tool intentionally NEVER approves a publication or authenticates a
reviewer's identity. It cannot read a SINAN file, query SQLite, download a
resource, create a release, or change the public MCP surface.

Every human declaration remains untrusted: a document's SHA-256 only
binds the reviewer's local bytes. Even a fully marked checklist must be
examined by actual qualified people through institutional processes.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from .official_sources import CONDITIONS
from .official_annual_resources import _index

SCHEMA = "sinan-private-roadmap-readiness-v1"
MAX_BYTES = 32_768
SHA = re.compile(r"[0-9a-f]{64}\Z")
DATE = re.compile(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")
ALIASES = frozenset(row[0] for row in CONDITIONS)
STATES = frozenset({
    "PENDENTE",
    "EVIDENCIA_LOCAL_NAO_VALIDADA",
    "PARECER_EXTERNO_DECLARADO_NAO_AUTENTICADO",
})
GATES = {
    "fonte_agravo_ano": "ID da distribuicao, origem autenticada, estado do arquivo, data de corte",
    "dicionario_esquema": "Dicionario aplicavel, nomes, tipos, dominios e transformacoes",
    "qualidade_coorte": "Duplicacoes, completude, definicao de coorte e janelas temporais",
    "indicador_denominador": "Numerador, denominador e reconciliacao com tabulacao oficial",
    "privacidade_composicao": "Reidentificacao, supressao e combinacao de releases",
    "juridico_institucional": "Base legal, etica, autoridade e pareceres independentes",
    "infraestrutura_acesso": "OIDC/OAuth, autorizacao, limites, retencao, revogacao e auditoria",
}


def _strict_json_pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError("Manifesto tem chaves JSON duplicadas")
        result[k] = v
    return result


def _scope(agravo: str, ano: int, resource_id: str | None = None) -> dict:
    if not isinstance(agravo, str) or agravo not in ALIASES:
        raise ValueError("Alias de agravo nao consta no indice de referencia")
    if type(ano) is not int or not 1980 <= ano <= 2100:
        raise ValueError("Ano do arquivo invalido")
    if resource_id is not None:
        if not isinstance(resource_id, str):
            raise ValueError("Identificador de recurso deve ser texto")
        _, rows = _index()
        if not any(r["resource_id"] == resource_id
                   and r["agravo_alias_interno"] == agravo
                   and r["ano_rotulado_no_portal"] == ano
                   for r in rows):
            raise ValueError("Recurso anual nao corresponde a agravo e ano")
    return {"agravo": agravo, "ano_do_arquivo": ano, "resource_id": resource_id}


def preparar_checklist_local(
    agravo: str, ano: int, destino: str | Path, resource_id: str | None = None,
) -> dict:
    """Create new owner-private manifest with all gates pending."""
    scope = _scope(agravo, ano, resource_id)
    doc = {
        "schema_version": SCHEMA,
        "scope": scope,
        "criado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gates": {
            gate: {"situacao": "PENDENTE", "evidencia_sha256_local": None}
            for gate in GATES
        },
        "revisao_institucional_independente": "PENDENTE",
        "publicacao_autorizada": False,
    }
    validate_checklist(doc)
    out = Path(destino).expanduser()
    if (out.is_symlink() or out.suffix.lower() != ".json"
            or not out.parent.is_dir() or out.parent.is_symlink()):
        raise ValueError("Destino local JSON inadequado")
    fd = os.open(str(out), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(doc, file, ensure_ascii=False, indent=2)
            file.write("\n")
    except BaseException:
        try:
            out.unlink()
        except OSError:
            pass
        raise
    return avaliar_checklist(doc)


def validate_checklist(value: object) -> dict:
    """Reject extra keys, hidden approvals, unpinned evidence or unknown axes."""
    if (not isinstance(value, dict)
            or set(value) != {
                "schema_version", "scope", "criado_utc", "gates",
                "revisao_institucional_independente", "publicacao_autorizada",
            }
            or value["schema_version"] != SCHEMA
            or value["revisao_institucional_independente"] != "PENDENTE"
            or value["publicacao_autorizada"] is not False):
        raise ValueError("Checklist invalido ou tentando conferir autorizacao")
    scope = value["scope"]
    if not isinstance(scope, dict) or set(scope) != {
        "agravo", "ano_do_arquivo", "resource_id"
    } or scope != _scope(
        scope["agravo"], scope["ano_do_arquivo"], scope["resource_id"]
    ):
        raise ValueError("Escopo de checklist invalido")
    when = value["criado_utc"]
    if not isinstance(when, str) or not DATE.fullmatch(when):
        raise ValueError("Data de criacao UTC invalida")
    try:
        datetime.strptime(when, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError("Data UTC fora de calendario") from None
    gates = value["gates"]
    if not isinstance(gates, dict) or set(gates) != set(GATES):
        raise ValueError("Gate ausente ou desconhecido")
    for key in GATES:
        entry = gates[key]
        if not isinstance(entry, dict) or set(entry) != {
            "situacao", "evidencia_sha256_local"
        }:
            raise ValueError("Formato de gate invalido")
        if not isinstance(entry["situacao"], str) or entry["situacao"] not in STATES:
            raise ValueError("Gate com situacao desconhecida")
        sha = entry["evidencia_sha256_local"]
        if entry["situacao"] == "PENDENTE":
            if sha is not None:
                raise ValueError("Gate pendente nao pode alegar evidencia")
        elif not isinstance(sha, str) or not SHA.fullmatch(sha):
            raise ValueError("Gate declarado sem hash documental de evidencia")
    return value


def load_checklist(path: str | Path) -> dict:
    p = Path(path).expanduser()
    if p.is_symlink() or not p.is_file() or not 2 <= p.stat().st_size <= MAX_BYTES:
        raise ValueError("Checklist local ausente ou acima do limite")
    try:
        with p.open("r", encoding="utf-8") as file:
            value = json.load(file, object_pairs_hook=_strict_json_pairs)
    except (ValueError, UnicodeError):
        raise ValueError("Manifesto JSON local invalido") from None
    return validate_checklist(value)


def avaliar_checklist(value: object) -> dict:
    """Safe readiness counts. NEVER turns asserted evidence into certification."""
    value = validate_checklist(value)
    gates = value["gates"]
    p = sorted(k for k in GATES if gates[k]["situacao"] == "PENDENTE")
    local = sum(gates[k]["situacao"] == "EVIDENCIA_LOCAL_NAO_VALIDADA" for k in GATES)
    declared = sum(
        gates[k]["situacao"] == "PARECER_EXTERNO_DECLARADO_NAO_AUTENTICADO"
        for k in GATES
    )
    return {
        "schema_version": "sinan-readiness-diagnostic-v1",
        "agravo": value["scope"]["agravo"],
        "ano_do_arquivo": value["scope"]["ano_do_arquivo"],
        "total_frentes": len(GATES),
        "pendencias_sem_evidencia": p,
        "n_frentes_pendentes": len(p),
        "n_frentes_com_evidencia_local_nao_validada": local,
        "n_frentes_com_parecer_declarado_nao_autenticado": declared,
        "revisor_externo_autenticado_pelo_sistema": False,
        "revisao_epidemiologica_concluida": False,
        "conformidade_lgpd_certificada": False,
        "acesso_remoto_com_dados_reais_autorizado": False,
        "publicacao_autorizada": False,
        "status": "BLOQUEADO_PARA_USO_REAL_E_PUBLICACAO",
        "aviso": (
            "Checklist operacional privado baseado em declaracoes locais. "
            "SHA-256 nao autentica origem oficial nem identidade do revisor. "
            "Mesmo sem pendencias declaradas, nao libera dados reais. "
            "Exige revisao externa, condicoes institucionais, privacidade, "
            "seguranca e aprovacao explicita fora deste programa."
        ),
    }


def diagnosticar_checklist_local(path: str | Path) -> dict:
    return avaliar_checklist(load_checklist(path))
