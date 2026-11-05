# Consolidação técnica e testes MCP de ponta a ponta

**Escopo:** demonstração pública exclusivamente sintética, ambiente local com
base artificial e protocolo MCP. **Não** é auditoria epidemiológica independente,
certificação de segurança, integração com dados ZIKABR24 ou liberação de
estatísticas reais.

## Registro histórico de implantação — 04/11/2026

> **Instantâneo datado.** Os identificadores e estados abaixo foram observados em 04/11/2026 e não devem ser interpretados como a versão ativa neste momento. Consulte o [índice de documentação](../README.md), os deploys do serviço e a [sonda HTTPS pública](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/actions/workflows/public-live-smoke.yml) para evidências mais recentes.

Consulta à **API da Render em 2026-11-04** identificou o serviço
`sinan-mcp-public-preview` na branch `main` com **autoDeploy desativado**.

- **Commit informado naquela consulta:** `678e15523bb13ec2f36778ffe879c479dff2b3bf`
- **Implantação concluída:** 2026-11-02 22:08:27 UTC
- **Origem:** atualização via API, status `live`
- **Serviço:** `https://sinan-mcp-public-preview.onrender.com`
- **Status científico:** apenas referências e dados inteiramente fictícios

O commit implantado pode diferir de `main`. Um teste do GitHub Actions
contra a branch mais recente **não confirma** que o Render executa essa
versão. Da mesma forma, uma implantação no Render não equivale a
homologação ou validação científica. Para revisar o estado mais recente,
confira `Deploys` no painel da Render e registre o SHA exato.

## Contrato único da demonstração pública

O arquivo [`public-mcp-contract-v1.json`](../public-mcp-contract-v1.json)
documenta o conjunto de **10 ferramentas públicas**, a origem sintética,
as rotas e os recursos proibidos. O inventário é verificado contra
os decoradores Python do servidor, a CI e o verificador HTTPS.
Se uma ferramenta for adicionada, removida ou renomeada, é necessário
rever explicitamente o contrato antes de aceitar uma mudança.

`scripts/check_public_contract.py` é uma checagem estática de segurança:
- compara nomes de ferramentas anotadas no código com o manifesto;
- verifica que o manifesto declara inexistência de dados e consultas SQL reais;
- verifica a presença da rota de saúde, entrypoint isolado e
  `autoDeploy: false` no `render.yaml`;
- recusa importações diretas perigosas no entrypoint público;
- impede que o guia de implantação volte a apresentar sete ferramentas.

**Não é uma auditoria de dependências transitivas nem substitui revisão
de ameaças, observabilidade, controle de abuso ou análise institucional.**

## Fluxos executados pela CI

1. **MCP cliente ↔ servidor público, no mesmo processo:** lista as
   10 ferramentas, invoca as operações válidas, confirma proveniência
   fictícia e recusa agravos, anos, UF, município, dimensões e
   ferramentas administrativas não permitidos.
2. **CLI como subprocesso ↔ SQLite sintético ↔ MCP local:** gera um
   banco temporário fictício por meio de `sinan_mcp demo`, inicia o
   protocolo MCP local em memória e testa consulta ao material sintético.
   Confirma que um banco não relacionado não é criado ou sobrescrito.
3. **Proteção contra configuração hostil:** ativa variáveis de ambiente
   com caminhos fictícios e a chave de dados reais para assegurar que
   o servidor *público* as ignore.
4. **Testes gerais:** `pytest -q` em Windows e Ubuntu, Python 3.11
   e 3.12.

Esses testes usam o protocolo por meio do cliente MCP do SDK, mas
**não verificam rede/TLS real**; a etapa remota permanece separada.

## Executar em Windows PowerShell 5.1 — checkout isolado e seguro

**Não reutilize** a pasta `SINAN-MCP-ZIKA-2024` para testar a `main`:
o checkout de Zika pode ter branches empilhadas e nenhuma branch
`main` local. Nesse cenário, `git switch main` falha e
`git pull --ff-only origin main` tenta atualizar a branch de Zika,
que pode divergir. Os scripts novos então não aparecem no diretório
atual, embora já estejam publicados no GitHub.

Use uma **segunda cópia limpa**, em outra pasta. O exemplo recusa
um destino já existente e não altera sua pesquisa:

```powershell
$dest = Join-Path $env:USERPROFILE "Downloads\SINAN-MCP-E2E"

if (Test-Path -LiteralPath $dest) {
    throw "Pasta de testes ja existe. Escolha outro destino sem apagar arquivos."
}

git clone --branch main --single-branch "https://github.com/miscrapha-DELTA-IA/SINAN-MCP.git" $dest
if ($LASTEXITCODE -ne 0) { throw "Falha ao clonar o repositorio." }

Set-Location -LiteralPath $dest
git branch --show-current
git log -1 --format="%h %s"

py -3.11 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Falha ao criar ambiente Python." }

$python = Join-Path $dest ".venv\Scripts\python.exe"
& $python -m pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependencias." }

& $python scripts/check_public_contract.py
if ($LASTEXITCODE -ne 0) { throw "Contrato publico nao validado." }

& $python -m pytest -q tests/test_mcp_end_to_end_contract.py
if ($LASTEXITCODE -ne 0) { throw "Falha no teste MCP end-to-end." }

& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Falha na suite completa." }
```

O primeiro comando `git branch --show-current` deve imprimir `main`.
Os arquivos `scripts/check_public_contract.py` e
`tests/test_mcp_end_to_end_contract.py` devem existir. Os testes
usam apenas um SQLite temporário com registros fictícios. A pasta
original de Zika é preservada e nenhuma mudança é enviada ao Render.

## Teste HTTPS remoto (somente leitura)

Este teste **não roda automaticamente em cada PR**: usa uma
instância externa já implantada e pode estar fria ou indisponível.

```powershell
$env:SINAN_PUBLIC_SMOKE_URL = "https://sinan-mcp-public-preview.onrender.com"
py -3.11 scripts/probe_public_https.py
Remove-Item Env:SINAN_PUBLIC_SMOKE_URL
```

O script invoca `/health`, o protocolo MCP via HTTPS,
`tools/list`, uma contagem artificial de 120 registros,
referências de múltiplos agravos, solicitações inválidas e
a rejeição de origem HTTP não permitida.


### Registro do teste HTTPS ampliado — 2026-11-04

**Resultado informado pelo operador no PowerShell:** `PUBLIC HTTPS MCP SMOKE SUCCESS`,
após execução de `scripts/probe_public_https.py` atualizado contra
`https://sinan-mcp-public-preview.onrender.com`.

O log apresentado registrou:

- `PASS HTTPS /health: synthetic-only`
- `PASS MCP initialize`
- `PASS MCP tools/list: 10 read-only reference/demo tools`
- `PASS MCP tool metadata: synthetic-only, no admin or real data`
- `PASS MCP listar_bases: no real datasets`
- `PASS MCP contar_notificacoes: 120 explicitly fictional records`
- `PASS MCP catalogue: multi-disease references, zero real data`
- `PASS MCP source links: official navigation metadata only`
- `PASS MCP rejected invalid/administrative calls`
- `PASS MCP rejects unapproved Origin`
- `PUBLIC HTTPS MCP SMOKE SUCCESS`

**Rastreabilidade:** o arquivo `scripts/probe_public_https.py` da `main`
na data do registro usou o contrato versionado
`docs/public-mcp-contract-v1.json`. A Render informou como implantação
ativa `678e15523bb13ec2f36778ffe879c479dff2b3bf`; a publicação
automática continua desativada. O resultado foi **reportado pelo operador**,
não é um laudo de auditoria externa nem prova de paridade entre a
`main` e o binário implantado.

**Interpretação:** as verificações remotas planejadas do contrato
público passaram na execução informada. A execução local de Windows foi
posteriormente comprovada pelos resultados apresentados abaixo. O serviço
público segue sem autorização para consultas reais ou publicação de
indicadores clínicos.

### Registro do teste local no Windows — 2026-11-04

O operador executou a suíte na **cópia isolada** do repositório,
`SINAN-MCP-E2E`, utilizando o interpretador do ambiente virtual
`.venv\\Scripts\\python.exe` e informou os seguintes resultados:

| Comando | Resultado comunicado |
|---|---|
| `scripts/check_public_contract.py` | `PUBLIC CONTRACT PASS: 10 MCP tools, synthetic-only; no deployment` |
| `pytest -q tests/test_mcp_end_to_end_contract.py` | **3 aprovados**, em 3,39 s |
| `pytest -q` | **102 aprovados, seis ignorados (skipped)**, em 13,20 s |
| `scripts/probe_public_https.py` | `PUBLIC HTTPS MCP SMOKE SUCCESS`, incluindo rejeição de chamadas inválidas e de origem HTTP não autorizada |

**Conclusão restrita:** as verificações funcionais previstas para a fase
de consolidação técnica foram aprovadas nas execuções compartilhadas.
Não houve erros relatados. Os seis testes ignorados **não** são tratados
como aprovados; as dependências opcionais ausentes foram identificadas no
log posterior, conforme a seção abaixo. O registro consiste em evidência informada pelo
operador, não em atestado independente nem em uma medição de
confiabilidade contínua. O resultado também não demonstra equivalência
entre o código da branch `main` e a versão implantada no Render.

**Permanecem fora do escopo:** revisão científica de dicionários,
homologação de dados por agravo/ano, auditoria de segurança externa,
validação de privacidade e aprovação institucional de publicação.
Qualquer atualização futura do Render continua sujeita aos critérios
abaixo, sem alteração automática do serviço.

## Cobertura opcional de importação — seis skips identificados

O comando `pytest -q -rs` executado pelo operador em 2026-11-04
relatou **102 testes aprovados e seis ignorados**. A causa é a ausência
de dependências opcionais no ambiente `.[dev]`, não um teste falhando:

| Importação ausente | Quantidade ignorada | Localizações indicadas pelo pytest |
|---|---:|---|
| `duckdb` | 3 | `test_catalog_import.py:43`; `test_ingest_pysus.py:233` e `:255` |
| `pyarrow` | 2 | `test_catalog_import.py:66`; `test_ingest_pysus.py:116` |
| `pysus` | 1 | `test_catalog_import.py:104` |
| **Total** | **6** | Nenhum desses cenários foi executado nessa suíte |

O `pyproject.toml` separa `.[dev]` (testes/MCP) de
`.[ingest]` (PySUS/PyArrow e bibliotecas de importação). `duckdb`
não está declarado nos grupos atuais; pode ser adicionado explicitamente
ao **ambiente isolado de testes**, sem mudar o conjunto de dependências
mínimas do servidor público.

No checkout dedicado `SINAN-MCP-E2E`, rode:

```powershell
$dest = Join-Path $env:USERPROFILE "Downloads\SINAN-MCP-E2E"
$python = Join-Path $dest ".venv\Scripts\python.exe"
Set-Location -LiteralPath $dest

& $python -m pip install -e ".[dev,ingest]" duckdb
if ($LASTEXITCODE -ne 0) { throw "Falha na instalacao opcional." }

& $python -m pip check
if ($LASTEXITCODE -ne 0) { throw "Dependencias inconsistentes." }

$oldCache = $env:PYSUS_CACHEPATH
$cache = Join-Path $dest "data\pysus-test-cache"
New-Item -ItemType Directory -Force -Path $cache | Out-Null
$env:PYSUS_CACHEPATH = $cache

try {
    & $python -m pytest -q -rs
    if ($LASTEXITCODE -ne 0) { throw "Suite opcional nao passou." }
}
finally {
    if ($null -eq $oldCache) {
        Remove-Item Env:PYSUS_CACHEPATH -ErrorAction SilentlyContinue
    }
    else {
        $env:PYSUS_CACHEPATH = $oldCache
    }
}
```

Os testes dessa suíte usam dados artificiais e simulações, mas instalar
bibliotecas opcionais **não concede permissão** para carregar microdados
reais. Não execute comandos de importação administrativa nesta etapa.
Registre os resultados novos, incluindo eventuais `skips` ou erros
de dependência. A aprovação da CI não implica automaticamente que
cada teste de importação opcional tenha sido executado no Windows local.

## Verificação posterior com dependências opcionais — 2026-11-04

**Resultado final comunicado pelo operador no PowerShell 5.1**, em
`C:\Users\rapha\Downloads\SINAN-MCP-E2E`, após instalar as
dependências opcionais `.[dev,ingest]` e `duckdb`:

| Verificação | Evidência apresentada |
|---|---|
| Integridade das dependências | `pip check`: `No broken requirements found.` |
| Preparação | `PYSUS_CACHEPATH` definido temporariamente em `data\pysus-test-cache` |
| Suíte completa | `pytest -q -rs`: **108 passed in 20.97s** |
| Testes ignorados | **0** |
| Falhas relatadas | **0** |

A execução posterior resolve os **seis skips do ambiente `.[dev]`**
documentados acima. O resultado anterior de 102 aprovados / 6
ignorados foi preservado como histórico da configuração mínima. O aviso
de atualização do `pip` não é um erro de dependência.

**Marco técnico alcançado:** verificação funcional planejada do MCP
sintético aprovada na CI e no Windows local, com cobertura das seis
rotas opcionais anteriormente ignoradas e teste HTTPS remoto ampliado
com sucesso informado pelo operador. Trata-se de **testes funcionais
com dados e simulações artificiais**, não de medição de cobertura
de código, ensaio de carga, auditoria externa de segurança ou validação
científica de dados SINAN reais. A implantação no Render continua com
SHA próprio, diferente da `main`, sem atualização automática.

## Critérios mínimos antes de uma atualização no Render

- [ ] Conferir SHA do commit a implantar e suas revisões
- [ ] CI Linux/Windows e contrato público concluídos com sucesso
- [ ] Garantir que o serviço continue isolado, sem DB/volume/credenciais
- [ ] Aprovar explicitamente a implantação manual
- [ ] Reexecutar o teste HTTPS contra o serviço realmente implantado
- [ ] Registrar SHA, horário, resultado do smoke e possíveis divergências
- [ ] Definir plano de reversão e acompanhar logs/erros sem dados sensíveis

**Este procedimento não faz deploy, não altera o serviço Render e não publica
dados SINAN reais.**
