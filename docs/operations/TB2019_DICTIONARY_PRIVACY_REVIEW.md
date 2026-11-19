# SINAN-TB 2019 — revisão do dicionário, método e divulgação (pré-parecer)

**Estado: DOCUMENT_REVIEW_PENDING_INDEPENDENT_SIGNOFF.** Documento de preparação baseado no código versionado da PR #72, no retorno textual do operador e em documentos oficiais consultados em 19/11/2026. Não substitui parecer de vigilância epidemiológica, privacidade, legitimidade institucional ou autorização de publicação.

## Evidências de base

1. **DBC 2019:** `FINAIS/TUBEBR19.dbc`; hash local fixado `7a00e29a5a309b794e21f1a650d3b04b9d3cb05fcc6ef8c9feefab3a961c9144`.
2. **Parquet espelho 2019:** `TUBEBR19.parquet`; hash verificado `7c599143671bb8bd895e2dbd39a325682b12d9fd5a024fcec101bb76ed0fc277`.
3. **Concordância relatada:** multiconjunto de registros projetados em `ID_MN_RESI, CS_SEXO, CS_RACA, SITUA_ENCE` com suas multiplicidades igual após normalização; outras variáveis não comparadas.
4. **Importação privada:** `PRIVATE_RESEARCH_IMPORT_NOT_HOMOLOGATED`, `status_da_fonte_no_sqlite=desconhecido`, `publicacao_autorizada=false`.
5. **Preflight local:** `verificacao_tecnica=concluida`, `relatorio_privado_criado=true`, sem alteração do SQLite.
6. **Resumo de flags sem dados:** o operador executou `scripts.resumir_qualidade_tb2019` e reportou `sqlite_integridade=true`, `uma_unica_fonte=true`, `somente_escopo_tube_2019=true`, `quantidade_compativel_com_metadados=true`, `codigos_projetados_no_dominio=true`, `uf_municipio_projetados_consistentes=true`, `checagens_tecnicas_sem_alertas=true`. Não foram divulgadas contagens, microdados ou bandas de completude. **As verificações tratam da projeção SQLite, não da semântica do arquivo bruto nem da compatibilidade histórica do dicionário.**

## Documentos oficiais identificados

- Ministério da Saúde, [Portal SINAN — Tuberculose](https://portalsinan.saude.gov.br/tuberculose), com ficha, instrucional, dicionário e caderno de análise.
- Ministério da Saúde, [Dicionário de Dados SINAN NET Tuberculose, versão 5.0](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_NET_Tuberculose_23_07_2020.pdf). O documento aberto é datado de 23/07/2020 em seu nome de arquivo; **compatibilidade exata da versão do leiaute com o snapshot 2019 ainda não foi demonstrada**.
- Ministério da Saúde, [Caderno de Análise 2019 — Tuberculose](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/Caderno_de_Analise_2019.pdf). Consultar especialmente seções sobre duplicidade e exercícios de proporções de cura/abandono e coortes.
- Ministério da Saúde, [Dados sobre agravos de notificações](https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/svsa/agravos-de-notificacoes/agravos-de-notificacoes), para o contexto de versão, atualização e documentação aberta.
- Ministério da Saúde, [Notificação Individual — Portal SINAN](https://portalsinan.saude.gov.br/notificacoes), para variáveis comuns a agravos. **É necessário localizar e versionar o dicionário específico da notificação individual aplicável ao período; não presumir que os códigos comuns foram auditados apenas com o dicionário de TB.**

### Complemento documental — materiais anteriores e posteriores a 2019

O [Dicionário de Notificação Individual v5](https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/DIC_DADOS_Notificacao_Individual_v5.pdf) contém o rodapé **Revisado em Julho/2010**. Os campos 11, 13 e 18 correspondem a `CS_SEXO`, `CS_RACA` e `ID_MN_RESI`, respectivamente. O documento apresenta os códigos cadastrais de sexo M/F/I, raça/cor 1–5 e 9 ignorado e município de residência com seis caracteres. Isso estabelece uma fonte **anterior** a 2019 para esses nomes e significados, não prova ausência de modificações até a edição DBC/2019.

Também está disponível uma [cópia do dicionário SINAN-TB v5.0](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_Tuberculose.pdf) com campo 62 `SITUA_ENCE`; sua data de revisão **não foi firmemente estabelecida** no presente protocolo. A cópia de 2020 indica igualmente o código 10 (abandono primário). Ambas mencionam o tipo lógico `Varchar2(1)`, incompatibilidade aparente que exige leitura do **cabeçalho** do DBF 2019 antes de inferir truncamento.

Foi incorporada uma ferramenta offline de inspeção dos quatro descritores DBF: `python -m scripts.inspecionar_cabecalho_tb2019`. Ela não itera sobre registros e apaga o DBF intermediário. A matriz detalhada e o roteiro constam em [TB2019_HISTORICAL_DICTIONARY_CROSSWALK.md](TB2019_HISTORICAL_DICTIONARY_CROSSWALK.md).

A **rota pública de agregados reais V1 permanece explicitamente bloqueada na branch**; ver [modelo de ameaças de release V2](REAL_RELEASE_V2_THREAT_MODEL.md). Esse bloqueio temporário elimina a possibilidade de `status_informado=final` e simples nomes de revisores promoverem um pacote V1, mas não conclui a governança e as revisões necessárias para uma futura versão.

## Matriz semântica das quatro colunas

| Campo no DBC/Parquet | Origem documental a revisar | O que a comparação de bytes projetados permite afirmar | Bloqueio semântico pendente |
| --- | --- | --- | --- |
| `ID_MN_RESI` | Dicionário comum da Notificação Individual e tabela IBGE aplicável | Mesma representação canônica e multiplicidades nos dois arquivos | Revisar competência temporal do município, código de 6/7 dígitos, mudanças territoriais e transformação no `project_record`. Município de **residência**, não necessariamente notificação/diagnóstico/tratamento. |
| `CS_SEXO` | Dicionário comum da Notificação Individual aplicável | Mesmos códigos normalizados entre os dois arquivos | Confirmar categorias aplicáveis, ausência/ignorado e o risco de interpretação de sexo cadastral como variável clínica ou identidade de gênero. |
| `CS_RACA` | Dicionário comum da Notificação Individual aplicável | Mesmos códigos normalizados entre os dois arquivos | Confirmar codificação histórica, diferenças entre raça/cor autodeclarada e medida disponível, ignorados, faltantes e erros de transformação. |
| `SITUA_ENCE` | Dicionário específico SINAN-TB v5.0, campo 62 | Mesmo código normalizado e multiplicidades nos dois arquivos | V5.0 lista 1 Cura, 2 Abandono, 3 Óbito por TB, 4 Óbito outras causas, 5 Transferência, 6 Mudança de diagnóstico, 7 TB-DR, 8 Mudança de esquema, 9 Falência, 10 Abandono primário. **Confirmar correspondência exata de 2019** e regras de seguimento; não inferir desfecho individual sem validação. |

**Limites essenciais:** `SITUA_ENCE` contém códigos 1–10 no dicionário v5.0, enquanto o tipo textual exibido como `Varchar2(1)` exige revisão de como o código 10 é representado na extração DBF. O comparador aceita códigos de até 3 dígitos, mas a constatação de equivalência sob normalização **não** garante que todos os códigos foram semanticamente interpretados corretamente. O relatório de qualidade audita o resultado *após* transformação; valores inválidos no original podem já ter sido convertidos em `NULL` pelo código.

## Evidência documental adicional (verificada em 19/11/2026)

- O [dicionário SINAN NET — Tuberculose, versão 5.0](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_NET_Tuberculose_23_07_2020.pdf), página 19 (numeração física, índice 18), identifica `SITUA_ENCE` como campo 62, apresenta códigos 1 a 8 e continua na página seguinte com **9 Falência** e **10 Abandono primário**. O tipo lógico mostrado na tabela é `Varchar2(1)`, apesar da categoria 10: **essa aparente inconsistência deve ser resolvida com a definição do DBF ou layout efetivo do arquivo de 2019**, sem inferir truncamento a partir do PDF.
- O [Caderno de Análise 2019](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/Caderno_de_Analise_2019.pdf) orienta a selecionar **tipo de entrada**, **ano de diagnóstico**, **situação de encerramento** e **residência** para cálculo de incidência. Uma projeção somente de quatro campos não dispõe das dimensões temporais e de coorte para replicar esse indicador.
- O [Caderno de Indicadores da Tuberculose, Ministério da Saúde, 2024](https://www.gov.br/aids/pt-br/central-de-conteudo/publicacoes/2024/caderno-de-indicadores-da-tuberculose-tuberculose-sensivel-tuberculose-drogarresistente-e-tratamento-preventivo.pdf) orienta seleção específica de tipos de entrada e exclusões de situações de encerramento para diversos indicadores. Esse documento **não demonstra retroativamente a compatibilidade da ficha 2024 com o snapshot 2019**, mas reforça a dependência metodológica de variáveis ausentes da projeção atual.

**Critério de aceite científico para o piloto atual:** a alegação publicável, se futuramente permitida, deve se limitar à contagem de registros por categoria e ano do **arquivo** após documentação de proveniência, completude, validade das codificações históricas e auditoria de privacidade. Indicadores de **incidência, cura, abandono por coorte e casos únicos** ficam explicitamente fora do escopo atual.

## Unidade de análise e denominadores — impacto do Caderno de Análise 2019

O caderno oficial diferencia duplicidades verdadeiras, **duplos registros por transferência** e **tratamentos distintos** (recidiva ou reingresso após abandono), exigindo revisão de vínculo e contexto clínico. Nosso SQLite guarda quatro variáveis, sem nome, datas, tipo de entrada, identificador longitudinal nem unidade notificadora; portanto **não é possível identificar pessoas únicas, episódios únicos, coorte de casos novos ou os procedimentos de vinculação** a partir dele.

Nos exemplos do caderno, a proporção de abandono não equivale à simples razão `SITUA_ENCE in {2,10} / SITUA_ENCE in {1,2,10}`. A análise oficial envolve seleções de coorte (ano de diagnóstico, tipo de entrada e exclusões) e denominador próprio; o caderno soma abandono e abandono primário no numerador. **O indicador `abandono_tb` implementado no projeto é exploratório**, não deve receber rótulo de indicador oficial ou taxa de abandono de uma coorte de 2019. Este é um impedimento metodológico para liberar esses indicadores como epidemiologia oficial.

O ano `2019` no nome do arquivo não prova que todos os registros tenham *ano de diagnóstico* 2019, tampouco que tenham encerramento em 2019. Não há datas na projeção de quatro campos.

## Matriz de privacidade para liberação hipotética de um agregado

| Controle | Condição mínima antes de aprovação | Estado |
| --- | --- | --- |
| Arquivos individuais e SQLite privados | Apenas `data/private/`, sem servidor MCP público, uploads ou logging de dados | **Operação prevista no código, revisão de implantação pendente** |
| Células pequenas | Política atual `K_MIN=20`, partição `PARTITION_MIN=100` e veto de partição com qualquer categoria positiva abaixo do limiar | **Código existe; não comprova anonimização** |
| Ataques de diferença | Inventariar **todas** as liberações anteriores e futuras, filtros, versões, sobreposição de UF e dimensão | **Pendente** |
| Fonte/versionamento | Associar snapshot fixado, confronto de projeção e revisão independente, não apenas `status_informado=final` | **Pendente — issue #73** |
| Revisão científica | Dicionários versionados, unidade observacional, coorte, tratamento de ausências e indicação precisa do que o agregado significa | **Pendente** |
| Revisão de privacidade e jurídica | Avaliar possibilidade de ligação/triangulação e base legal/uso institucional, assinar autorização específica | **Pendente** |
| Implantação | Serviço de agregados separado, somente pacote estático revisado, controles de acesso e registro de revisão | **Bloqueado** |

## Protocolo de revisão externa (sem distribuir microdados)

1. **Revisor de vigilância/TB**: revisar dicionário v5.0 e compatibilidade histórica 2019, dicionário de notificação individual, relação ano arquivo/diagnóstico, duplicidades, ausência de campos para coorte, rótulos e denominadores. Emitir parecer sobre **quais alegações**, se alguma, o recorte de quatro campos sustenta.
2. **Revisor de privacidade**: avaliar o desenho de uma única partição UF/ano/dimensão, células mínimas, dados publicados anteriormente, ataque por diferença e possibilidade de combinação entre versões. Parecer sobre risco residual e política de divulgação.
3. **Operador técnico independente**: revisar os scripts de hash e comparação de multiconjuntos, saída do quality preflight, versões do código/ambiente e demonstrar que a leitura pública não possui referência ao SQLite privado.
4. **Responsável pela divulgação**: decisão explícita e verificável sobre um pacote *específico*, vinculado aos pareceres, sem acesso autônomo dos operadores a declarar `final` e promover um artefato a publicação.

**Não submeter os registros, o SQLite privado nem o JSON integral de qualidade a revisores externos por padrão.** Acesso individual só após avaliação de finalidade, legitimidade, meios apropriados e minimização. Revisores podem trabalhar inicialmente com o código, materiais públicos, metadados e a matriz.

## Status de encerramento desta etapa

`QUALITY_AUDIT_EXECUTED_SEMANTIC_REVIEW_PENDING`.

Nenhuma revisão científica independente foi concluída, nenhum agregado recebeu autorização e o servidor MCP público permanece sintético.
