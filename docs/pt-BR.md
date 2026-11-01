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


## Descoberta PySUS corrigida no Windows — v0.3.1 alpha

O PySUS 2.11.7 pode retornar `FileBag` vazio no Windows apesar de o arquivo de catálogo DuckDB conter metadados válidos. O SINAN MCP agora **consulta esses metadados locais diretamente, em modo somente leitura**, quando a descoberta normal vem vazia. A recuperação de `TUBEBR24.parquet` e `DENGBR24.parquet` foi confirmada no Windows do GitHub Actions.

Após atualizar o projeto, execute:

```powershell
git pull origin main
python -m pip install -e ".[ingest,dev]"
python -m sinan_mcp descobrir-pysus --agravo TUBE --ano 2024
python -m sinan_mcp descobrir-pysus --agravo DENG --ano 2024
```

Quando usada a recuperação, o campo `modo_descoberta` deve mostrar `duckdb_local_metadados`. **Isso confirma apenas a descoberta dos nomes dos arquivos, não baixa microdados.**

Para inspecionar versão, cache e os resultados das duas consultas ao PySUS:

```powershell
python -m sinan_mcp diagnosticar-pysus --agravo TUBE --ano 2024
```

Ainda não validamos a importação remota nativa do PySUS no Windows; ela pode continuar falhando. Para importar arquivos Parquet **públicos e obtidos de fonte verificada** já presentes no computador:

```powershell
python -m sinan_mcp importar-parquet .\\TUBEBR24.parquet --agravo TUBE --ano 2024 --status desconhecido
python -m sinan_mcp diagnosticar-base --agravo TUBE --ano 2024
```

O Parquet original e o SQLite contêm informações potencialmente sensíveis. **Não os envie ao GitHub**, nem apresente a medida exploratória de abandono como um indicador oficial do Ministério da Saúde.

