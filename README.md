# SINAN MCP — protótipo de pesquisa (v0.1.0)

**Servidor MCP de código aberto para consultas epidemiológicas agregadas sobre microdados públicos do SINAN/DATASUS**, independente do fornecedor do LLM. O MCP permite conectar a clientes compatíveis, como Claude Desktop, Cursor e outros hosts. Para LLMs sem cliente MCP, será necessário desenvolver um adaptador.

> **Estado:** protótipo local. Código fornecido com testes unitários usando dados *sintéticos*. Não acompanha microdados do SINAN nem acesso a sistemas internos. NÃO é uma integração em tempo real, serviço homologado pelo Ministério da Saúde, mecanismo completo de anonimização nem indicador epidemiológico validado.

## Ferramentas

- `listar_bases`: fonte, status final/preliminar, ano do arquivo, data de importação.
- `descrever_campos`: mini-dicionário, links e advertências.
- `contar_notificacoes`: registros agregados por ano, UF, município, sexo ou raça/cor, com supressão de células pequenas.
- `proporcao_abandono_tuberculose`: indicador exploratório explicitamente definido, com proteção adicional para numerador/complemento.

**Sem SQL arbitrário, consultas individuais, identificadores diretos ou ferramentas de escrita disponibilizadas ao LLM.** Os arquivos originais ficam fora da biblioteca de dados exposta; o SQLite guarda apenas projeções aprovadas. Mesmo assim combinações de atributos podem representar informação sensível: não publicar externamente sem análise de risco, controles contra inferência e revisão institucional.

## Instalação (Python 3.11 ou superior)

No Windows PowerShell, na pasta do projeto:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e "."
```

Para habilitar downloads com PySUS:

```powershell
pip install -e ".[ingest]"
```

## Teste rápido com dados simulados

```powershell
python .\examples\gerar_demo.py
python -m sinan_mcp importar-csv .\examples\sinan_tube_SINTETICO.csv --agravo TUBE --ano 2024 --status desconhecido
python -m sinan_mcp servir --rest --port 8001
```

Essa base é **inteiramente sintética**. Não use seus valores em pesquisa, artigo ou relatório epidemiológico. Antes de carregar uma base real, remova o SQLite de demonstração em `data/sinan.sqlite3` ou use outro caminho `--db`.

## Carregar dados públicos

Baixe os dados **somente de fontes oficiais ou de espelhos identificados**, documentando o estado final/preliminar e o ano. O Ministério da Saúde disponibiliza microdados por agravo/ano; os dicionários são essenciais.

**Método A — PySUS (rede, opção recomendada):**

```powershell
python -m sinan_mcp importar-pysus --agravo TUBE --ano 2024 --source catalog --status preliminar
```

`--source catalog` usa a via de catálogo/espelho padrão do PySUS e pode não ser idêntica à origem em determinado instante. Com `--source origin`, solicita à fonte original. O rótulo `--status` deve ser definido após checar a classificação no portal, pois não é detectado automaticamente. Disponibilidade, versões e campos variam por ano e agravo.

**Método B — CSV local** (convertido previamente de DBC/DBF ou obtido do portal):

```powershell
python -m sinan_mcp importar-csv .\dados_publicos\TUBEBR24.csv --agravo TUBE --ano 2024 --status preliminar
```

Aceita CSV com cabeçalhos do SINAN, separados por vírgula ou `;`, em UTF-8 por padrão. Para Latin-1, use `--encoding latin-1`. A importação substitui qualquer snapshot anterior do **mesmo agravo e ano**, mesmo que a origem seja outra (por exemplo, CSV seguido de PySUS), evitando somar a mesma base duas vezes. A coluna `ano` no banco é **ano do arquivo importado** e não deve ser interpretada automaticamente como ano de notificação/diagnóstico.

A ingestão preserva somente: agravo, ano do arquivo, UF e município de residência quando presentes, sexo, raça/cor, situação de encerramento da TB. Qualquer nome, endereço, documento, identificador de notificação etc. **é descartado na projeção**. Ausência de município de residência não é substituída por município de notificação.

## Iniciar o MCP

**Local/stdio** (Claude Desktop, Cursor e outros hosts compatíveis):

```powershell
python -m sinan_mcp servir
```

A aparência de terminal parado é normal: o processo está aguardando a comunicação MCP. Configure seu host conforme [`examples/claude_desktop_windows.json`](examples/claude_desktop_windows.json), com caminho absoluto do Python do venv e do SQLite (cada host tem seu formato).

**Streamable HTTP MCP local**:

```powershell
python -m sinan_mcp servir --http --port 8000
```

Endpoint: `http://127.0.0.1:8000/mcp`.

**REST local (para sistemas que não suportam MCP):**

```powershell
python -m sinan_mcp servir --rest --port 8001
```

Endpoints JSON: `GET /health`, `GET /v1/bases`, `GET /v1/campos`, `POST /v1/contagens`, `POST /v1/tb/abandono`. Exemplo de corpo para `POST /v1/contagens`:

```json
{"agravo":"TUBE","ano_inicio":2024,"ano_fim":2024,"uf":"PI","por":"raca_cor"}
```

O adaptador REST permite a criação de *function tools* para LLMs sem cliente MCP. **Isso não significa conexão automática a qualquer plataforma**: o aplicativo/host precisa configurar uma integração com o endpoint. Não encaminhe dados pessoais ou privados.

Para implantação pública, use autenticação OAuth/controle de identidade, gateway, TLS, auditoria, isolamento de banco, rate limits e revisão de segurança. Este projeto **deliberadamente não permite bind em 0.0.0.0** pela CLI, pois ainda não implementa autenticação MCP remota.

## Exemplo de interação

> **Pergunta:** Qual a distribuição por raça/cor das notificações de tuberculose no Piauí em 2024?
>
> **Tool:** `contar_notificacoes(agravo="TUBE", ano_inicio=2024, ano_fim=2024, uf="PI", por="raca_cor")`
>
> **Saída:** valores da base local carregada, com grupos pequenos suprimidos. **O projeto não contém dados reais pré-carregados.**

> **Pergunta:** Qual a proporção exploratória de abandono entre encerramentos selecionados?
>
> **Tool:** `proporcao_abandono_tuberculose(ano_inicio=2024, ano_fim=2024, uf="PI", por="raca_cor")`

Fórmula exploratória: abandono `(SITUA_ENCE 2 + 10) / (SITUA_ENCE 1 + 2 + 10)`, apenas nas bases importadas. **Não corresponde necessariamente ao indicador oficial do MS**; verifique critérios de inclusão, descarte de duplicatas, mudanças de códigos, definição de coorte e maturação dos encerramentos. `10` representa abandono primário em versões documentadas do dicionário, mas deve ser confirmado no período analisado.

## Limitações / plano para produção

1. Verificar dicionários e harmonizar versões do SINAN por agravo/ano; automatizar esquemas aprovados de mapeamento.
2. Distinguir séries por ano de notificação, diagnóstico e encerramento, de acordo com a pergunta.
3. Desduplicação apropriada por agravo e construção de coortes; metodologias epidemiológicas homologadas.
4. Implementar controle formal de privacidade (ataques por diferença, limitação de consultas, agregações aprovadas; eventual privacidade diferencial) antes de acesso público.
5. Evoluir o REST local para OpenAPI documentado, autenticação e observabilidade; criar adaptadores próprios dos provedores sem MCP nativo.
6. Expansão controlada a outros agravos e séries espaciais/temporais com códigos IBGE validados.

## Fontes

- Ministério da Saúde — [Dados sobre agravos de notificações](https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/svsa/agravos-de-notificacoes/agravos-de-notificacoes)
- SINAN — [Página de tuberculose, fichas e dicionários](https://portalsinan.saude.gov.br/tuberculose)
- PySUS — [Documentação](https://pysus.readthedocs.io/en/latest/)
- MCP SDK Python v2 — [Documentação](https://py.sdk.modelcontextprotocol.io/)

Licença do código: MIT. **Não há redistribuição de microdados neste pacote.**
