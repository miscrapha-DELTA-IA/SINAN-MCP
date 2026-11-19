# SINAN-TB 2019 — matriz de evidências históricas v2

**Etapa: HISTORICAL_DICTIONARY_CROSSWALK_CANDIDATE.** Levantamento de documentos oficiais e seus campos, sem transcrição de microdados. Ter evidências em versões de dicionários anteriores ou posteriores ao ano do arquivo **não comprova** a compatibilidade integral da edição DBC/2019. Confirmar com layout efetivo e revisor científico.

## Fontes oficiais e posição temporal

- [Notificação Individual — Dicionário de Dados SINAN NET v5](https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/DIC_DADOS_Notificacao_Individual_v5.pdf): rodapé com **Revisado em Julho/2010**. É anterior ao arquivo TUBE 2019, útil para documentar nomenclatura dos campos compartilhados, mas não demonstra ausência de mudanças posteriores.
- [Tuberculose — Dicionário de Dados SINAN NET, versão 5.0](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_Tuberculose.pdf): cópia oficial disponibilizada sem data de revisão inequívoca identificada. Contém variável `SITUA_ENCE` e código 10.
- [Tuberculose — Dicionário NET, cópia nomeada 23/07/2020](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_NET_Tuberculose_23_07_2020.pdf): cópia posterior a 2019; apresenta a mesma variável e opções, ainda sem prova de identidade do DBF 2019.
- [Caderno de Análise 2019 — Tuberculose](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/Caderno_de_Analise_2019.pdf): demonstra que indicadores dependem do ano de diagnóstico, tipo de entrada, critérios de coorte e encerramento. **Não autoriza interpretar ano do arquivo como ano da coorte.**

## Crosswalk: presença e semântica documental

| Campo | Evidência no dicionário | Tipo/códigos documentados | Resultado atual | Pendência |
| --- | --- | --- | --- | --- |
| `ID_MN_RESI` | Notificação Individual v5, campo 18 | `varchar2(6)`; município de residência; tabela IBGE | Coerência projetada UF/município passou | Verificar cadastro IBGE no período, tratamento de valores com sete dígitos e ausência antes/depois da projeção |
| `CS_SEXO` | Notificação Individual v5, campo 11 | `varchar2(1)`; `M` masculino, `F` feminino, `I` ignorado | Códigos *projetados* em domínio | Confirmar compatibilidade com o DBF de 2019 e semântica de variável cadastral |
| `CS_RACA` | Notificação Individual v5, campo 13 | `varchar2(1)`; `1` branca, `2` preta, `3` amarela, `4` parda, `5` indígena, `9` ignorado | Códigos *projetados* em domínio | Confirmar mudanças históricas/ausentes e diferenciação de categorias na origem |
| `SITUA_ENCE` | Dicionários TB v5.0, campo 62 | `Varchar2(1)` na coluna de tipo, com opções 1–10 (10 = abandono primário) | Campo de encerramento preservado na comparação DBC↔Parquet (com normalização) | Confrontar **largura real no DBF**, sistema de representação de 10 e revisão histórica de 2019 |

## Ponto verificável: aparente inconsistência do código 10

A anotação `Varchar2(1)` descreve um caractere, mas a legenda inclui `10`. Isso não prova por si só truncamento, ausência do código ou corrupção de dados. Para reduzir a incerteza técnica, foi criado um comando que lê **somente o cabeçalho DBF**, nunca seus registros:

```powershell
cd $HOME\SINAN-MCP
git pull --ff-only
.\.venv\Scripts\python.exe -m scripts.inspecionar_cabecalho_tb2019
```

O utilitário reconfirma o hash do DBC local fixado, converte-o para um DBF temporário em `data/private/tb2019`, consulta apenas metadados dos **quatro** campos e destrói o arquivo temporário. O terminal mostra exclusivamente tipo, largura e uma conclusão de capacidade física `campo_situacao_10_cabe_em_largura` (possibilidade de **dois caracteres**). Este resultado não examina se o código 10 efetivamente ocorreu, nem demonstra correspondência semântica do dicionário. **Nunca enviar o DBC, DBF ou SQLite.**

## Fatos já evidenciados e incerteza remanescente

- Hashes locais do DBC e PySUS conferidos; multiconjunto integral da projeção de quatro campos concordante em execução relatada.
- Qualidade projetada (cinco flags) sem alertas, segundo retorno redigido. **Não avalia códigos descartados/normalizados como nulos antes da projeção.**
- O dicionário de Notificação Individual revisado em 2010 **antecede** o arquivo 2019, mas não é atestado de que o layout de 2019 era idêntico.
- A cópia TB/2020 é posterior; a ocorrência de código 10 em duas versões documentais torna a questão de largura um item de engenharia verificável, ainda pendente.
- O dataset de quatro campos não contém datas de diagnóstico, tipo de entrada e identificadores longitudinais para cálculo reprodutível de incidência, cura ou abandono oficial.

## Resultado da inspeção física do DBF 2019 (relatado pelo operador)

O operador executou `scripts.inspecionar_cabecalho_tb2019` no DBC de 2019 previamente fixado e informou:

| Campo | Tipo DBF | Largura física (bytes) |
| --- | --- | ---: |
| `ID_MN_RESI` | `C` | 6 |
| `CS_SEXO` | `C` | 1 |
| `CS_RACA` | `C` | 1 |
| `SITUA_ENCE` | `C` | **2** |

A saída registrou `campo_situacao_10_cabe_em_largura=true`, `linhas_lidas=false`, `microdados_exibidos=false`, `compatibilidade_temporal_do_dicionario_verificada=false` e `publicacao_autorizada=false`.

**Interpretação estritamente técnica:** o layout **físico** da edição capturada admite armazenar a sequência de dois caracteres `10` em `SITUA_ENCE`. Portanto, o campo não é fisicamente limitado a um caractere neste arquivo. A divergência aparente em relação ao tipo `Varchar2(1)` no dicionário v5.0 pode envolver texto documental ou diferenças de implementação. Nenhum código clínico foi lido no teste de cabeçalho e **não** se pode afirmar que `10` ocorre na base, nem que a versão de 2020 se aplique integralmente a 2019.

### Próximo confronto: códigos originais versus valores preservados no SQLite

Foi criado um auditor privado, sem rede, `scripts.auditar_codigos_originais_tb2019` que percorre exclusivamente no computador do operador o DBC validado, verifica os códigos dos quatro campos **antes da projeção** e compara o multiconjunto da projeção gerada pelo mesmo algoritmo com o SQLite 2019 já importado. O terminal informa apenas três resultados gerais `true/false` (domínios, ausência de perdas por transformação e igualdade do multiconjunto); detalhes booleanos por campo permanecem no relatório local e não são compartilhados. Nenhum valor, categoria, contagem, coorte ou distribuição é emitido.

```powershell
cd $HOME\SINAN-MCP
git pull --ff-only
.\.venv\Scripts\python.exe -m scripts.auditar_codigos_originais_tb2019
```

O domínio `SITUA_ENCE=1..10` é **hipótese fundamentada nos dicionários disponíveis**, não confirmação de compatibilidade histórica do arquivo 2019. Um resultado positivo nesse auditor significa somente ausência de alertas para esses domínios candidatos, não homologação clínica. **Não enviar** DBF, DBC, SQLite ou relatórios privados.

## Resultado do confronto entre códigos originais e SQLite (19/11/2026)

O operador executou `scripts.auditar_codigos_originais_tb2019` no Windows com o DBC e o SQLite **privados**. O JSON resumido informou:

```json
{
  "stage": "TUBE2019_SOURCE_CODES_PRIVATE_AUDIT_NOT_HOMOLOGATED",
  "dominios_brutos_sem_alertas": true,
  "projecao_sem_perda_de_codigos_preenchidos": true,
  "multiconjunto_original_projetado_igual_sqlite": true,
  "relatorio_privado_criado": true,
  "quantidades_categorias_e_registros_exibidos": false,
  "compatibilidade_temporal_dicionario_2019_verificada": false,
  "revisao_cientifica_independente": false,
  "revisao_privacidade_independente": false,
  "publicacao_autorizada": false
}
```

**Interpretação técnica restrita:** segundo o resultado relatado, os códigos preenchidos nas quatro colunas não escaparam aos domínios candidatos nem foram descartados pelo algoritmo `project_record`, **após** normalização de branco, ausentes e certas representações numéricas. O comparador também confirmou igualdade das projeções com multiplicidades. Não houve exposição de categorias, frequências ou linhas. O relatório é local.

**Limites importantes:** a auditoria aplica `_norm` também à observação de origem, portanto não prova ausência de toda alteração textual/representacional no DBF; a igualdade SQLite foi testada para o recorte de quatro campos, não para os demais atributos; as regras de domínio foram extraídas de dicionários disponíveis, mas a **compatibilidade histórica com a edição de 2019 não foi assinada por revisor científico independente**. A condição `SITUA_ENCE=C(2)` demonstra capacidade física para `10`, não sua ocorrência.

O material agora pode ser usado como **evidência técnica preliminar para revisão externa**, sem anexar microdados ou relatório interno. Consultar [pacote de encaminhamento ao revisor](TB2019_INDEPENDENT_REVIEW_HANDOFF.md).

## Critério para parecer independente

O revisor deve registrar se os quatro códigos se mantiveram no arquivo de 2019; justificar eventuais transformações; distinguir registro de episódio/pessoa; considerar a perda de dados potencialmente causada pelo `project_record`; e indicar **exatamente** que análises descritivas podem ser feitas. Nenhuma publicação pode usar o nome de indicador oficial sem replicar seu método, denominador e critério de coorte.
