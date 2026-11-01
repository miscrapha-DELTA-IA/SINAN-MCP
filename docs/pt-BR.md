# SINAN MCP — início rápido

O SINAN MCP permite consultar **agregados de bases públicas importadas localmente**, por meio do MCP. Não é um serviço oficial do Ministério da Saúde nem traz dados reais incluídos.

## Demonstração inteiramente sintética

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m sinan_mcp demo
.\.venv\Scripts\python.exe -m sinan_mcp --db .\data\sinan-demo.sqlite3 servir
```

No cliente MCP (por exemplo, Claude Desktop), use o executável Python e o arquivo SQLite com **caminhos absolutos**. O programa não mostra uma interface gráfica: espera mensagens MCP do aplicativo cliente.

Pergunta de exemplo: *"Na base sintética TUBE, qual a distribuição por raça/cor no PI no arquivo 2024? Cite a proveniência e as limitações."*

## Proteções e limites

O serviço exige um único ano de arquivo e uma UF, agrupando apenas por `sexo` ou `raca_cor`. Não permite município, SQL livre nem acesso individual. Suprime pequenas contagens, mas **não garante anonimização**. O ano do arquivo pode ser diferente do ano de notificação; contagens não equivalem a taxas de incidência. A medida de abandono disponível é **exploratória**, não um indicador oficial.

Importação real é administrativa e separada das ferramentas dos modelos:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ingest]"
.\.venv\Scripts\python.exe -m sinan_mcp importar-pysus --agravo TUBE --ano 2024 --status desconhecido
```

Consulte dicionários, cobertura e revisão da fonte antes de interpretar números. Não disponibilize esse serviço remotamente com microdados sem revisão especializada de segurança e sigilo.

[README em inglês](../README.md) · [Segurança](../SECURITY.md)

## Etapa 0.3 — descoberta e processamento em lotes

A versão 0.3 adiciona **catálogo de agravos-piloto** (tuberculose e dengue), metodologia e diagnóstico administrativo de completude. O comando abaixo consulta arquivos do PySUS **sem baixar microdados**:

```powershell
.\.venv\Scripts\python.exe -m sinan_mcp descobrir-pysus --agravo TUBE --ano 2024
```

O importador opcional com `.[ingest]` baixa arquivos e processa CSV/Parquet em lotes, sem carregar todo o DataFrame nacional. A integração com fontes reais ainda não foi validada integralmente. Consulte os [critérios epidemiológicos](EPIDEMIOLOGY.md).

**Somente no ambiente administrativo**, diagnostique uma base importada:

```powershell
.\.venv\Scripts\python.exe -m sinan_mcp diagnosticar-base --agravo TUBE --ano 2024
```

O relatório inclui contagens exatas e não é disponibilizado ao LLM.
