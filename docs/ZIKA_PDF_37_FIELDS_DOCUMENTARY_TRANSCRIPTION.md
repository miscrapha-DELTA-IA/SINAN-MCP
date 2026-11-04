# ZIKA — transcrição documental candidata dos 37 campos do PDF

**Natureza da evidência:** o dicionário público específico de Zika contém
37 campos numerados em 8 páginas. Esta tabela é uma **transcrição
documental candidata** conferida visualmente com as páginas do PDF;
ainda exige uma segunda revisão independente. Os grupos analíticos,
descritores curtos e indicadores de domínio são rótulos auxiliares
desta curadoria, não nomes oficiais de variáveis nem homologação de
significado epidemiológico para uma exportação.

**Fonte primária:**
[Portal de Dados Abertos do SUS — recurso de Zika](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus/resource/58038262-c745-46ea-979b-8727eb08ec5c) e
[PDF oficial `dic_dados_zika.pdf`](https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/dic_dados_zika.pdf).

**Limites:** nenhuma distribuição `ZIKABR24.json.zip` ou
`ZIKABR24.parquet.zip` foi aberta; não há confronto de colunas,
tipos, domínios, versão aplicável a 2024, data exata de corte, condição
de caso, regras de deduplicação, integridade binária do PDF com hash
oficial, parecer epidemiológico nem permissão para publicar.

## Inventário de campos conforme as páginas visíveis

| Seq. | Identificador do PDF | Tipo no PDF | Página | Síntese documental | Domínio (resumo de curadoria) |
|---:|---|---|---:|---|---|
| 1 | `tp_not` | `char(1)` | 1 | Tipo de notificação | `categorias_listadas` |
| 2 | `id_agravo` | `char(5)` | 1 | Código do agravo notificado | `tabela_agravos_cid10` |
| 3 | `dt_notific` | `date(8)` | 1 | Data da notificação | `data_dd_mm_aaaa` |
| 4 | `sem_not` | `char(6)` | 1 | Semana epidemiológica da notificação | `semana_epidemiologica_aaaass` |
| 5 | `nu_ano` | `char(4)` | 1 | Ano da notificação | `ano_aaaa` |
| 6 | `sg_uf_not` | `char(2)` | 2 | UF da unidade notificadora | `tabela_ibge` |
| 7 | `id_municip` | `char(6)` | 2 | Município da unidade notificadora | `tabela_ibge` |
| 8 | `id_regiona` | `char(8)` | 2 | Regional de saúde da notificação | `tabela_regional_sistema` |
| 9 | `id_unidade` | `char(7)` | 2 | Unidade notificadora | `tabela_cnes` |
| 10 | `dt_sin_pri` | `date(8)` | 2 | Data de primeiros sintomas ou diagnóstico | `data_dd_mm_aaaa` |
| 11 | `sem_pri` | `char(6)` | 2 | Semana epidemiológica de primeiros sintomas | `semana_epidemiologica_aaaass` |
| 12 | `ano_nasc` | `char(4)` | 2 | Ano de nascimento | `ano_aaaa` |
| 13 | `nu_idade_n` | `num(4)` | 3 | Idade com unidade de medida codificada | `idade_codificada_unidade_primeiro_digito` |
| 14 | `cs_sexo` | `char(1)` | 3 | Sexo informado | `categorias_listadas` |
| 15 | `cs_gestant` | `char(1)` | 3 | Gestação e trimestre | `categorias_listadas` |
| 16 | `cs_raca` | `char(1)` | 4 | Raça/cor autodeclarada | `categorias_listadas` |
| 17 | `cs_escol_n` | `char(2)` | 4 | Escolaridade | `codigos_heterogeneos_revisao` |
| 18 | `sg_uf` | `char(2)` | 4 | UF de residência | `tabela_ibge` |
| 19 | `id_mn_resi` | `char(6)` | 5 | Município de residência | `tabela_ibge` |
| 20 | `id_rg_resi` | `char(8)` | 5 | Regional de saúde de residência | `tabela_regional_sistema` |
| 21 | `id_pais` | `char(4)` | 5 | País de residência | `tabela_paises` |
| 22 | `nduplic_n` | `char(1)` | 5 | Marcador de não listar ou não contar duplicidade | `codigos_ambiguidade_pagina` |
| 23 | `in_vincula` | `char(6)` | 5 | Vinculação de notificações | `categorias_listadas` |
| 24 | `dt_invest` | `date(8)` | 5 | Início da investigação | `data_dd_mm_aaaa` |
| 25 | `id_ocupa_n` | `char(6)` | 5 | Ocupação ou ramo de atividade | `tabela_ocupacoes` |
| 26 | `classi_fin` | `char(2)` | 6 | Classificação final após investigação | `categorias_listadas` |
| 27 | `criterio` | `char(2)` | 6 | Critério de confirmação ou descarte | `categorias_listadas` |
| 28 | `tpautocto` | `char(1)` | 6 | Autoctonia em relação à residência | `categorias_listadas` |
| 29 | `coufinf` | `char(2)` | 6 | UF provável da infecção | `tabela_ibge` |
| 30 | `copaisinf` | `char(4)` | 7 | País provável da infecção | `tabela_paises` |
| 31 | `comuninf` | `char(6)` | 7 | Município provável da infecção | `tabela_ibge` |
| 32 | `doenca_tra` | `char(1)` | 7 | Relação da doença com o trabalho | `categorias_listadas` |
| 33 | `evolucao` | `char(1)` | 8 | Evolução do caso | `categorias_listadas` |
| 34 | `dt_obito` | `date(8)` | 8 | Data do óbito | `data_dd_mm_aaaa` |
| 35 | `dt_encerra` | `date(8)` | 8 | Data do encerramento | `data_dd_mm_aaaa` |
| 36 | `dt_digita` | `date(8)` | 8 | Data de primeira digitação | `data_dd_mm_aaaa` |
| 37 | `tp_sistema` | `char(1)` | 8 | Sistema de origem do registro | `categorias_listadas` |

<small>Nota: os domínios resumidos não constituem um dicionário de codificação
homologado. Quando uma célula remete a tabela externa (IBGE, CNES,
CID-10, ocupações ou países), seus códigos não foram transcritos nem
validados aqui. Nos campos categóricos, as listas do JSON são apenas
códigos **visíveis** no PDF, e não uma garantia de exaustividade de
domínios presentes no arquivo exportado.</small>

## Ressalvas documentais ainda pendentes

- **`nu_idade_n`:** O primeiro digito codifica unidade (hora/dia/mes/ano); nao representar como anos sem conversao revisada.
- **`nduplic_n`:** Celula de categorias no PDF apresenta linha de duplicidade sem numero legivel; caracteristicas mencionam 1 e 2. Recusar mapa automatico de codigos.
- **`in_vincula`:** Tipo documental char(6) apesar das categorias visiveis 0/1; nao alterar largura por inferencia.
- **`cs_escol_n`:** Formas de codigo com um e dois digitos, alem de ignorado/branco; nao assumir padrao unico.
- **`id_rg_resi`:** Caracteristica textual se refere a municipio de notificacao na linha de regional de residencia; requer revisao de origem.
- **`tp_sistema`:** Dicionario lista Sinan Net/Online, mas nao certifica qual gerou cada registro de ZIKABR24.
- **`classi_fin`:** Classificacao final do documento nao implica definicao de caso ou consolidacao epidemiologica de 2024.

Além das questões anteriores, é necessário conferir com revisão
epidemiológica independente todas as regras condicionais de preenchimento
(notificação, gestação, classificação final, residência/autoctonia,
encerramento). Essas regras aparecem no PDF, mas não foram transformadas
em lógica computacional nem testadas contra 2024.

## Checklist privado de conferência

O [roteiro de revisão documental dos 37 campos](ZIKA_37_FIELDS_INDEPENDENT_REVIEW_CHECKLIST.md)
permite criar arquivo privado com 37 verificações e sete ressalvas,
registrando notas e divergências declaradas pelo operador. Não
autentica revisores nem altera os dez tópicos científicos pendentes.

## CLI administrativa offline

```powershell
py -3.11 -m sinan_mcp conferir-transcricao-zika-pdf
py -3.11 -m sinan_mcp conferir-transcricao-zika-pdf --detalhar
py -3.11 -m sinan_mcp planejar-confronto-documental-2024 --agravo ZIKA
```

A primeira opção retorna totais e avisos; `--detalhar` mostra campos,
tipos, páginas e significados resumidos. Ambas consultam exclusivamente o
JSON versionado neste repositório, sem chamada de rede, PDF, ZIP, SQLite ou
dados de pacientes. O SHA-256 impresso é **do catálogo local JSON**,
não uma autenticação da fonte governamental.

Arquivos envolvidos:
- `sinan_mcp/registry/zika_pdf_37_fields_candidate.json`
- `sinan_mcp/zika_pdf_37_field_curation.py`
- `tests/test_zika_pdf_37_field_curation.py`

**Estado:** 37 registros documentais candidatos; 10 revisões científicas
da matriz ZIKA/2024 pendentes; **0** campos da distribuição 2024
conferidos, **0** indicadores homologados, sem autorização de acesso,
processamento real ou publicação.

A ferramenta privada existente de comparação de esquema permanece
**bloqueada para ZIKABR24**, inclusive após edição manual de layout
JSON. Não usar este catálogo como fonte de autoaprovação, preenchimento
de resultados clínicos ou regra de exclusão de registros.
