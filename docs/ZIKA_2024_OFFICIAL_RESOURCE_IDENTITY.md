# ZIKA/2024 — identidade documental das distribuições oficiais

**Escopo: subetapa documental da identidade de recursos. Não é auditoria dos
bytes nem validação de layout, série temporal, coorte ou indicador.**

## Páginas oficiais consultadas na curadoria de 03/11/2026

O Portal de Dados Abertos do SUS (Ministério da Saúde) mantém duas páginas
de recursos rotulados `Zika Vírus - 2024`:

| Referência oficial | UUID do recurso | Formato | Estado da página |
|---|---|---|---|
| [ZIKABR24.json.zip](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus/resource/264978ca-f795-4940-b5d3-ebc21e7d1c7c) | `264978ca-f795-4940-b5d3-ebc21e7d1c7c` | JSON | active |
| [ZIKABR24.parquet.zip](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus/resource/41bfda2a-5826-4ef9-8913-497247e6c9ce) | `41bfda2a-5826-4ef9-8913-497247e6c9ce` | Parquet | active |

Ambos exibem o mesmo **Package Id**
`4557ba96-7d52-4a56-bd6f-f99a5af09f77`.
A pasta de distribuição indicada para cada formato corresponde ao
caminho S3 já curado na allowlist anual do MCP.

**Precisão temporal:** as datas de atualização apresentadas pelo portal
são mutáveis e variam entre recursos e momentos de consulta. Não foram
transformadas em data de consolidação, corte epidemiológico, início de série,
versão imutável, nem em checksum. A expressão "active" é a situação
administrativa do recurso no **catálogo**, não o estado clínico dos casos.

O snapshot `sinan_mcp/zika_resource_identity.py` contém esses campos
estáveis e compara, de modo **offline**, cada UUID/formato/URL com
`official_annual_resources.json` carregado com validação rígida.
Erros de conjunto, formato, UUID duplicado, URL ou campos de aprovação
inesperados resultam em falha fechada.

## Contexto epidemiológico publicado no portal — sem validação do ZIP

A [página oficial do conjunto Sinan/Vírus Zika](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus)
informa que os casos são notificados no **SINAN Net** e que suspeitos devem
ser investigados/encerrados em até **60 dias**. Apresenta como casos
prováveis os casos suspeitos notificados, exceto descartados. Essas são
afirmações do **texto do portal**, não a análise de registros do arquivo
2024; a aplicação operacional dessas regras não foi testada.

A mesma página descreve que séries históricas são produzidas de bases
**congeladas em data específica para cada ano** e observa diferenças
potenciais em relação aos dados da CGARB. Contudo, a **data de corte do
recurso específico ZIKABR24 não é fornecida na descrição**. A data de
atualização do cadastro do recurso não substitui a data epidemiológica
de congelamento. O texto ainda informa particularidade do Espírito
Santo desde 2020 (e-SUS Vigilância; fontes distintas para dengue,
chikungunya e Zika), a ser examinada antes de comparações interestaduais.

Há ainda na lista oficial um item denominado **"Dicionário de dados -
Zika Vírus"**, com atualização exibida **14/07/2025**. O item é uma
evidência documental **mais específica** que o PDF genérico de
Notificação Individual encontrado no Portal SINAN. Entretanto, este
levantamento não recuperou o **UUID/URL exata e o conteúdo auditável do
PDF desse item**. Logo, **não** incrementa a contagem dos 12 dicionários
específicos já curados nem confirma edição aplicável a ZIKA/2024.

O módulo offline `sinan_mcp/zika_portal_context.py` mantém
separados: (1) fatos textuais publicados pelo portal; (2) referência
a um documento ainda não inspecionado; e (3) estados de arquivo
específico, autenticidade, corte e layout **desconhecidos**. Não existe
ingestão de dados, nem autorização de publicação.

## Resultado operacional

```powershell
py -3.11 -m sinan_mcp confrontar-identidade-zika-2024
py -3.11 -m sinan_mcp planejar-confronto-documental-2024 --agravo ZIKA
# Esse comando agora exibe SINAN Net, dicionário listado e corte desconhecido
py -3.11 -m pytest -q tests/test_zika_resource_identity.py
```

A matriz de revisão pode agora informar **UUID/formato documentados**
na etapa `identidade_do_recurso`, mas o **tópico permanece PENDENTE**:
não foram confirmados os bytes, checksum, origem de transferência,
data de corte, caráter preliminar/final, edição do dicionário,
esquema de colunas ou cobertura epidemiológica.

O comando não faz **reconsulta online em sua execução**; ele coteja
evidências públicas registradas no código durante a curadoria.
Por isso não se deve afirmar que a simples execução demonstra
disponibilidade em tempo real da URL.

## SIFA/2024 — referência secundária, não homologada como recurso oficial

O [índice independente Quantilica/ALPACA](https://quantilica.com/alpaca/dados/sinan-sifa)
lista o caminho `/dissemin/publicos/SINAN/DADOS/PRELIM/SIFABR24.dbc`
como candidato de um arquivo preliminar de 2024. Esse site se declara
**independente do DATASUS**: não é uma confirmação primária verificável
de um recurso ou de seu checksum. O
[guia oficial de acesso do Ministério da Saúde](https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/svsa/agravos-de-notificacoes/agravos-de-notificacoes)
orienta usar o portal de transferência de arquivos com fonte SINAN,
modalidade DADOS, tipo de agravo, ano e UF.

**Consequência:** SIFA permanece com **0 distribuições anuais
primariamente catalogadas**, até conferência do recurso específico
na interface ou índice oficial de transferência; o caminho de terceiro
não deve ser importado como fonte autenticada. Também não comprova
o sistema de origem, os campos ou as regras de divulgação.

**Invariantes preservadas:** 14 aliases, 12 dicionários históricos
específicos, 5 distribuições anuais de fontes oficiais catalogadas,
0 indicadores homologados, 0 arquivos clínicos acessados, nenhuma
alteração do servidor MCP público.
