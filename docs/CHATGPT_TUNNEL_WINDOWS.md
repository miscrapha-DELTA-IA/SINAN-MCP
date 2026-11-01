# ChatGPT connector — OpenAI Secure MCP Tunnel on Windows

**Audience:** operators connecting a *synthetic* SINAN MCP to ChatGPT. The actual SQLite database stays local but aggregate tool responses may be delivered to the connected ChatGPT workspace. This tunnel alone does not guarantee anonymity.

## Prerequisites

- A provisioned `tunnel_id` in the correct OpenAI Platform organization, and a **runtime** API key with Tunnels Read + Use; do not use an admin key or paste the runtime key into a conversation.
- Python 3.11+, `pip install -e ".[ingest,dev]"` in the Git clone, and a synthetic `data/sinan-demo.sqlite3` created with `py -3.11 -m sinan_mcp demo`.
- The full Windows AMD64 `tunnel-client.exe` from the [official OpenAI release](https://github.com/openai/tunnel-client/releases/latest).

## Configure in PowerShell 5.1

Open a PowerShell terminal in the repository:

```powershell
cd C:\Users\rapha\Downloads\SINAN-MCP-GitHub
py -3.11 -m sinan_mcp demo

$tc = Get-ChildItem "$HOME\Downloads\tunnel-client" -Filter tunnel-client.exe -Recurse -File |
  Select-Object -First 1 -ExpandProperty FullName
if (-not $tc) { throw "tunnel-client.exe nao encontrado" }

$python = (& py -3.11 -c "import sys; print(sys.executable)").Trim() -replace '\\', '/'
$db = (Resolve-Path ".\data\sinan-demo.sqlite3").Path -replace '\\', '/'
$mcpCommand = "$python -m sinan_mcp --db $db servir"

$tunnelId = Read-Host "tunnel_id"
$secret = Read-Host "Chave runtime da OpenAI" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
  $env:CONTROL_PLANE_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
  Remove-Variable secret -ErrorAction SilentlyContinue
}

# Only create if the profile does not exist already:
& $tc init --sample sample_mcp_stdio_local --profile sinan-local --tunnel-id $tunnelId --mcp-command $mcpCommand

& $tc doctor --profile sinan-local --explain
```

Use **forward slashes** for Python/database paths: backslashes may be stripped during stdio command parsing on Windows. If the profile already exists, do not rerun `init` without intending to modify it. A successful doctor prints `RESULT ok`; this proves profile configuration, not live connectivity.

```powershell
& $tc run --profile sinan-local
```

Keep the terminal open. In another PowerShell session check local readiness:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/readyz |
  Select-Object StatusCode
```

A 200 response indicates local readiness, not necessarily that ChatGPT has installed the plugin or completed a live tool call.

## ChatGPT

With the client running, go to ChatGPT connectors/plugins and create a custom MCP server choosing **Tunnel** as connection type, selecting the provisioned tunnel. Configure a descriptive name, e.g., "SINAN MCP — synthetic pilot". Test `listar_bases` and `listar_agravos` through the actual connector. Ensure `listar_bases` reports **synthetic**, not an imported real snapshot.

For now, the `sinan-local` profile must continue pointing to `sinan-demo.sqlite3`. Do not repoint it at `sinan.sqlite3` or set `SINAN_PUBLIC_REAL_DATA=1` without the privacy review documented in [SECURITY.md](../SECURITY.md). The new gate deliberately blocks real-data numeric MCP/REST calls by default.

## Diagnostics

- `mcp-command preflight failed`: check that Python exists; convert paths to forward slashes.
- `profile_load FAIL`: `init` did not create a readable profile; stop and fix the preflight error.
- `control_plane_api_key malformed`: check that a complete, valid runtime key is being entered; do not post it in logs.
- `doctor RESULT ok` but plugin cannot find tools: confirm `run` is still active, the ChatGPT connector references the correct tunnel and its permissions are correct; check `/readyz` and the local tunnel-client UI.
- If a query says `Dados reais bloqueados`, this is the intended safe default for a non-synthetic database. No bypass is enabled automatically.

Official guide: [OpenAI Tunnel Client — onboarding](https://github.com/openai/tunnel-client/blob/main/docs/onboarding.md).
