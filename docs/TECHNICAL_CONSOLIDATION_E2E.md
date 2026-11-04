# Consolidação técnica e testes MCP de ponta a ponta

**Escopo:** demonstração pública exclusivamente sintética, ambiente local com
base artificial e protocolo MCP. **Não** é auditoria epidemiológica independente,
certificação de segurança, integração com dados ZIKABR24 ou liberação de
estatísticas reais.

## Estado confirmado da implantação

Consulta à **API da Render em 2026-11-04** identificou o serviço
`sinan-mcp-public-preview` na branch `main` com **autoDeploy desativado**.

- **Commit atualmente informado pela Render:** `678e15523bb13ec2f36778ffe879c479dff2b3bf`
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

O arquivo [`public-mcp-contract-v1.json`](public-mcp-contract-v1.json)
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

## Executar em Windows PowerShell 5.1

```powershell
cd "$env:USERPROFILE\Downloads\SINAN-MCP-ZIKA-2024"
git fetch origin test/mcp-public-local-e2e-baseline
git switch test/mcp-public-local-e2e-baseline

py -3.11 -m pip install -e ".[dev]"
py -3.11 scripts/check_public_contract.py
py -3.11 -m pytest -q tests/test_mcp_end_to_end_contract.py
py -3.11 -m pytest -q
```

A branch acima é independente dos PRs científicos Zika e não realiza
merge, publicação ou acesso a dados reais. Caso haja alterações locais
não salvas, preserve-as antes de trocar de branch.

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

Só registre **teste remoto aprovado** após executar o script com sucesso.
A antiga verificação de HTTPS passou para uma versão anterior do Render;
não constitui prova automática da versão implantada hoje.

## Critérios mínimos antes de uma atualização no Render

- [ ] Conferir SHA do commit a implantar e suas revisões
- [ ] CI Linux/Windows e contrato público concluídos com sucesso
- [ ] Garantir que o serviço continue isolado, sem DB/volume/credenciais
- [ ] Aprovar explicitamente a implantação manual
- [ ] Reexecutar o teste HTTPS contra o serviço realmente implantado
- [ ] Registrar SHA, horário, resultado do smoke e possíveis divergências
- [ ] Definir plano de reversão e acompanhar logs/erros sem dados sensíveis

**Este PR não faz deploy, não altera o serviço Render e não publica
dados SINAN reais.**
