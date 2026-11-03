# Registro de recursos anuais no Portal de Dados Abertos do SUS

## Estado do levantamento de 03/11/2026

Esta camada complementa o catálogo de **documentos de dicionários** por
agravo/ano e resolve uma etapa distinta: identificar o **recurso de distribuição
com nome, formato, UUID e página oficial**. Um recurso listado no portal do
Ministério da Saúde NÃO significa que o arquivo de bytes foi obtido,
autenticado ou que um dicionário específico tenha sido validado.

| Agravo | Ano rotulado | Recurso e ID oficial | Formato | Binário e layout validados |
|---|---|---|---|---|
| DENG | 2024 | [DENGBR24.csv.zip](https://dadosabertos.saude.gov.br/dataset/arboviroses-dengue/resource/4cf2f7b8-9920-41b5-817a-1ffc13e0690c) — 4cf2f7b8-9920-41b5-817a-1ffc13e0690c | CSV compactado | NÃO |
| DENG | 2024 | [DENGBR24.json.zip](https://dadosabertos.saude.gov.br/dataset/arboviroses-dengue/resource/28975ef7-da35-498e-b179-cfbde2150f90) — 28975ef7-da35-498e-b179-cfbde2150f90 | JSON compactado | NÃO |
| CHIK | 2024 | [CHIKBR24.json.zip](https://dadosabertos.saude.gov.br/dataset/arboviroses-febre-de-chikungunya/resource/74c005e0-e1b8-4db0-997d-8c80b2d37f8a) — 74c005e0-e1b8-4db0-997d-8c80b2d37f8a | JSON compactado | NÃO |
| TUBE | 2024 | Referência anual exata ainda não identificada por fonte primária equivalente nesta rodada | — | NÃO |

Atenção: **as URLs reais de distribuição estão no catálogo JSON**;
o usuário deve conferir primeiro a página do recurso. Nenhum dado foi
baixado para construir este registro, e a presença de uma URL não é
autorização para publicar microdados ou seus agregados.

As páginas oficiais dos conjuntos
[Sinan/Dengue](https://dadosabertos.saude.gov.br/dataset/arboviroses-dengue)
e [Sinan/Febre de Chikungunya](https://dadosabertos.saude.gov.br/dataset/arboviroses-febre-de-chikungunya)
declaram atualização periódica e alertam para possíveis diferenças
frente à CGARB. O material informa que os arquivos históricos podem
ser congelados em datas de corte próprias; uma atualização do portal
em 2026 NÃO significa que o arquivo chamado 2024 contenha apenas
dados definitivos, completos ou idênticos a uma extração anterior.
O portal menciona diferenças na alimentação de arboviroses para o
Espírito Santo desde 2020 (e-SUS Vigilância em Saúde), ponto que exige
revisão de cobertura e do sistema de origem.

O [Ministério da Saúde](https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/svsa/agravos-de-notificacoes/agravos-de-notificacoes)
também disponibiliza caminho de descoberta dos arquivos de disseminação
SINAN do DATASUS com fonte, modalidade, ano e UF. O registro de recursos
CKAN/S3 não equivale à identificação de um DBC no FTP DATASUS, nem a uma
prova de equivalência entre espelhos.

## Software e fronteiras

- Arquivo imutável versionado: sinan_mcp/registry/official_annual_resources.json.
- Carregador sem rede: sinan_mcp/official_annual_resources.py, com paths
  HTTPS permitidos e derivados de IDs da fonte oficial. Não aceita
  URL ou arquivo do usuário como entrada pública.
- Ferramentas MCP somente de metadados:
  consultar_recursos_oficiais_ano e listar_recursos_oficiais_anuais.
  Não acessam PySUS, SQLite, rede, dataframes ou arquivos individuais.
- O planejador multiagravo distingue duas camadas:
  evidencia_documental_agravo_ano (referência do dicionário) e
  recursos_de_distribuicao_ano (distribuições publicadas).
  **Nenhuma camada marca aplicabilidade do dicionário como verdadeira.**
- Verificador local: sinan_mcp/local_distribution_review.py, que exige
  ID curado, nome e ZIP íntegros do ponto de vista estrutural, hash
  local SHA-256, apenas uma entrada de CSV/JSON no pacote, sem symlink,
  extração, descompressão ou retorno de linhas. Não valida o conteúdo
  clínico, autenticidade do provedor, checksum oficial ou consolidação.
  É deliberadamente separado do processo público MCP.

## Windows PowerShell 5.1

No clone atualizado para esta branch:

    py -3.11 -m pip install -e ".[dev]"
    py -3.11 -m sinan_mcp listar-distribuicoes-oficiais
    py -3.11 -m sinan_mcp consultar-distribuicao-ano --agravo DENG --ano 2024
    py -3.11 -m sinan_mcp consultar-distribuicao-ano --agravo TUBE --ano 2024
    py -3.11 -m pytest -q tests/test_official_annual_resources.py

A inspeção opcional não baixa dados e só pode ser feita em um ZIP já
existente legitimamente no disco do pesquisador:

    py -3.11 -m sinan_mcp conferir-zip-distribuicao .\data\DENGBR24.csv.zip --resource-id 4cf2f7b8-9920-41b5-817a-1ffc13e0690c

A ferramenta não extrai nem retorna registros. O SHA-256 do ZIP
é **observado pelo operador localmente**, e não um checksum assinado
pelo Ministério da Saúde. Um arquivo forjado pode ter nome, formato
e SHA-256 calculado localmente sem corresponder ao original publicado.
Não envie relatórios privados, arquivos clínicos ou capturas do conteúdo
a issues, chats de IA, CI ou servidores públicos.

## Porta de saída para validação científica

O registro aceita em separado três estados verificáveis:

1. **Recurso catalogado** — este PR: página governamental, ID, ano
   rotulado, nome e formato identificados.
2. **Arquivo obtido com origem e versão autenticadas** — PENDENTE:
   download autorizado, metadados de versão, hash fornecido ou
   autenticado pela fonte independente, documentação de data de corte
   e sistema de origem; validação que os arquivos baixados
   correspondem aos recursos catalogados.
3. **Dicionário, coorte e indicador cientificamente validados** —
   PENDENTE: comparar colunas e códigos com a edição realmente
   aplicável àquele arquivo, avaliar qualidade/deduplicação,
   limites de desagregação, definições de caso, população e
   compatibilidade da série. Exige parecer epidemiológico
   documentado e processo auditável de revisão de divulgação.

O CSV/JSON do portal não é automaticamente compatível com o modelo
mínimo SQLite do SINAN MCP. Não executar ingestão sem verificar
codificação, semântica e transformações, mesmo com um arquivo ZIP
cujo nome coincida. Os contratos TUBE_2024_EXAMPLE e
DENG_2024_EXAMPLE permanecem **sintéticos e não oficiais**.

A revisão antes de publicação de qualquer dado real segue separada,
exige parecer independente e NÃO pode ser substituída por um teste
de software ou pela edição de uma flag no registro JSON.
