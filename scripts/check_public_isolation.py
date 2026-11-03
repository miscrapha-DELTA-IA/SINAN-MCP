"""CI import-boundary guard: the PUBLIC MCP cannot reach private code.

AST-only, no module execution. This is a targeted defense-in-depth guard,
not a comprehensive security assessment or a proof of noninterference.
Any additional public import must be reviewed explicitly.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

PUBLIC_ENTRY = "public_server"
PUBLIC_ALLOWLIST = frozenset({
    "public_server",
    "catalogue",
    "official_sources",
    "query_planner",
    "semantics",
    "year_evidence_registry",
    "official_annual_resources",
})
FORBIDDEN_EXTERNAL = frozenset({
    "sqlite3", "pysus", "pandas", "pyarrow", "duckdb", "requests",
    "httpx", "subprocess", "socket", "smtplib", "tempfile", "pickle",
    "builtins", "runpy", "ctypes", "pathlib", "io",
})
FORBIDDEN_EXACT_IMPORTS = frozenset({
    "urllib.request", "urllib3", "asyncio.subprocess",
    "importlib.util", "importlib.machinery",
})
PUBLIC_ENV_ALLOWLIST = frozenset({
    "SINAN_PUBLIC_HOST", "RENDER_EXTERNAL_HOSTNAME", "PORT",
})
FORBIDDEN_OS_OPERATIONS = frozenset({
    "system", "popen", "startfile", "spawnl", "spawnle", "spawnlp",
    "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
    "execv", "execve", "execvp", "execvpe",
})
FORBIDDEN_ENV = frozenset({
    "SINAN_DB_PATH", "SINAN_PUBLIC_REAL_DATA",
    "SINAN_ADMIN_TOKEN", "SINAN_SQLITE_PATH",
})


def inspect_source(module: str, source: str) -> tuple[set[str], list[str]]:
    """Return package dependency modules and precise import-policy errors."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set(), [f"{module}: fonte Python invalida"]
    imports: set[str] = set()
    violations: list[str] = []

    def external(name: str):
        if (name == "importlib" or name.split(".")[0] in FORBIDDEN_EXTERNAL
                or any(name == x or name.startswith(x + ".")
                       for x in FORBIDDEN_EXACT_IMPORTS)):
            violations.append(f"{module}: dependencia externa nao permitida ({name})")

    def local(name: str):
        first = name.split(".")[0]
        if first not in PUBLIC_ALLOWLIST or "." in name:
            violations.append(f"{module}: dependencia privada ou nao revista ({name})")
        else:
            imports.add(first)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name == "sinan_mcp":
                    violations.append(f"{module}: import dinamico do pacote raiz")
                elif name.startswith("sinan_mcp."):
                    local(name[len("sinan_mcp."):])
                else:
                    external(name)
                if name == "os" and alias.asname:
                    violations.append(f"{module}: alias de os nao permitido")
        elif isinstance(node, ast.ImportFrom):
            name = node.module or ""
            if any(alias.name == "*" for alias in node.names):
                violations.append(f"{module}: import estrela nao permitido")
            if name == "importlib" and any(
                alias.name != "resources" for alias in node.names
            ):
                violations.append(f"{module}: import dinamico via importlib nao permitido")
            if name == "os" and any(
                alias.name in FORBIDDEN_OS_OPERATIONS for alias in node.names
            ):
                violations.append(f"{module}: operacao de sistema nao permitida")
            if node.level >= 2:
                violations.append(f"{module}: import relativo ascendente")
            elif node.level == 1:
                if name:
                    local(name)
                else:
                    for alias in node.names:
                        local(alias.name)
            elif name == "sinan_mcp":
                for alias in node.names:
                    local(alias.name)
            elif name.startswith("sinan_mcp."):
                local(name[len("sinan_mcp."):])
            else:
                external(name)
            if name == "os" and any(
                alias.name in {"environ", "getenv"} for alias in node.names
            ):
                violations.append(f"{module}: acesso direto a ambiente nao revisto")
        elif isinstance(node, ast.Attribute):
            if (isinstance(node.value, ast.Name)
                    and node.value.id == "os"
                    and node.attr == "environ"):
                violations.append(f"{module}: variavel de ambiente privada usada")
        elif isinstance(node, ast.Subscript):
            target = node.value
            if (isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "os"
                    and target.attr == "environ"
                    and isinstance(node.slice, ast.Constant)
                    and node.slice.value in FORBIDDEN_ENV):
                violations.append(f"{module}: variavel de ambiente privada usada")
        elif isinstance(node, ast.Call):
            f = node.func
            if (isinstance(f, ast.Attribute)
                    and isinstance(f.value, ast.Name)
                    and f.value.id == "os"
                    and f.attr in FORBIDDEN_OS_OPERATIONS):
                violations.append(f"{module}: operacao de sistema nao permitida")
            if isinstance(f, ast.Name) and f.id in {
                "__import__", "eval", "exec", "compile"
            }:
                violations.append(f"{module}: execucao ou import dinamico proibido")
            if (isinstance(f, ast.Attribute)
                    and f.attr == "import_module"
                    and isinstance(f.value, ast.Name)
                    and f.value.id == "importlib"):
                violations.append(f"{module}: importlib.import_module proibido")
            environment_getter = (
                isinstance(f, ast.Attribute)
                and isinstance(f.value, ast.Name)
                and f.value.id == "os"
                and f.attr == "getenv"
            ) or (
                isinstance(f, ast.Attribute)
                and isinstance(f.value, ast.Attribute)
                and isinstance(f.value.value, ast.Name)
                and f.value.value.id == "os"
                and f.value.attr == "environ"
                and f.attr == "get"
            )
            if environment_getter and (
                not node.args or not isinstance(node.args[0], ast.Constant)
                or type(node.args[0].value) is not str
                or node.args[0].value not in PUBLIC_ENV_ALLOWLIST
                or node.keywords
            ):
                violations.append(f"{module}: variavel de ambiente privada usada")
    return imports, violations


def audit_public_import_boundary(root: Path) -> list[str]:
    """Statically traverse all local imports reachable from public_server."""
    root = Path(root)
    seen: set[str] = set()
    pending = [PUBLIC_ENTRY]
    problems: list[str] = []
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        path = root / "sinan_mcp" / (name + ".py")
        if not path.is_file() or path.is_symlink():
            problems.append(f"{name}: modulo publico ausente ou symlink")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            problems.append(f"{name}: falha de leitura de fonte publica")
            continue
        deps, bad = inspect_source(name, content)
        problems.extend(bad)
        pending.extend(sorted(deps - seen))
    return sorted(problems)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    problems = audit_public_import_boundary(root)
    if problems:
        for problem in problems:
            print("PUBLIC MCP ISOLATION FAIL:", problem, file=sys.stderr)
        return 2
    print(
        "PUBLIC MCP ISOLATION OK: no disallowed imports in approved "
        "public metadata dependency graph."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
