# Revisão externa | SINAN MCP

**Roteiro para colaboradores · Zika e tuberculose · escopo documental**  
[Documentação](../README.md) · [Protocolo técnico](REVIEW_PROTOCOL.md) · [Matriz de campos](field_matrix.csv) · [Manifesto de fontes](source_manifest.json)

## 1. O que é o SINAN MCP?

O **SINAN MCP** é um projeto independente, de código aberto, que utiliza o *Model Context Protocol* para tornar referências e descrições do Sistema de Informação de Agravos de Notificação (SINAN) acessíveis por ferramentas digitais e assistentes de IA. Seu objetivo é apoiar pesquisa **com proveniência, limitações visíveis e controles de privacidade**.

**O que o sistema faz hoje:** organiza referências oficiais para agravos de notificação e oferece uma demonstração pública somente com dados fictícios. Um pacote documental específico de Zika e tuberculose reúne sete PDFs oficiais, informações de integridade e uma matriz de 57 identificadores de campos.

**O que ainda não faz:** não publica estatísticas reais de pacientes nem comprova que os dicionários observados correspondem integralmente a uma exportação do SINAN de 2024. O projeto não é uma solução oficial do SUS, SINAN ou DATASUS.

## 2. O que está sendo solicitado?

Uma avaliação **externa, objetiva e documentada** sobre o que foi realmente examinado. A auditoria documental não exige acesso a bases clínicas; o pacote tem 57 registros (37 Zika, 15 TB e 5 comuns), apresentados em 42 entradas no bundle Zika e 20 no bundle TB devido ao reuso dos 5 campos comuns. Existem três tipos diferentes de contribuição. **Escolha apenas o que se enquadra na sua experiência.**

| Modalidade | Perfil | Tempo indicativo | Evidência solicitada |
| --- | --- | --- | --- |
| A — Clareza e experiência | Integrantes da comunidade; sem conhecimento de programação | 10–15 min | Registro dos três testes e eventuais dificuldades |
| B — Conferência biomédica | Profissional biomédico ou da saúde | 15–25 min | Campos selecionados, páginas, interpretação e divergências |
| C — Revisão metodológica | Pesquisador ou especialista em epidemiologia/sistemas de informação | Conforme disponibilidade | Parecer delimitado sobre fontes, versões, critérios e riscos metodológicos |

A modalidade A documenta **usabilidade**, não a validade científica. As modalidades B e C só contam como **independentes** depois da declaração de vínculo/conflitos e avaliação do escopo realmente revisado. Nenhuma pessoa está obrigada a aprovar o projeto.

## 3. Onde consultar os documentos?

1. Abra o [repositório SINAN-MCP](https://github.com/miscrapha-DELTA-IA/SINAN-MCP). Consulte a seção **O que é** na [apresentação em português](../pt-BR.md).
2. Abra o [protocolo de Zika e tuberculose](REVIEW_PROTOCOL.md), que explica o estado das evidências.
3. Abra a [matriz CSV](field_matrix.csv). Na visualização do GitHub, procure uma linha pelo campo usando `Ctrl+F` (Windows) ou a busca da página.
4. Confira, quando pertinente, o PDF listado no [manifesto JSON](source_manifest.json). As fontes diretas e respectivas páginas estão também na tabela do [protocolo](REVIEW_PROTOCOL.md).

**Não é preciso instalar software ou conectar o MCP para realizar a revisão documental.** O endpoint `/mcp` é uma interface de programa, não uma página web convencional.

## 4A. Teste de clareza — comunidade

Execute os três testes e registre **SIM, NÃO ou NÃO CONSEGUI TESTAR**.

| Teste | Ação concreta | O que observar |
| --- | --- | --- |
| 1. Entender o projeto | Leia a primeira seção do [README em português](../pt-BR.md). | Ficou claro que os dados numéricos públicos são fictícios? |
| 2. Encontrar uma evidência | Na [matriz](field_matrix.csv), localize `cs_gestant` (Zika, página 3 de `ZIKA-DIC`) e `SITUA_ENCE` (TB, página 19 de `TUBE-DIC`). | Conseguiu encontrar ambos e identificar a origem? |
| 3. Entender o limite científico | Leia o [protocolo](REVIEW_PROTOCOL.md), especialmente **Avaliação científica independente**. | Ficou claro que a revisão e a equivalência com dados 2024 estão pendentes? |

Se algum documento não abrir, registre o **link, dispositivo e mensagem de erro**. Não é necessário enviar capturas com dados pessoais ou arquivos clínicos.

### Modelo de resposta — copiar e preencher

```text
Revisão documental — SINAN MCP
Nome ou identificação para contato:
Data:
Modalidade: A — Clareza e experiência

Teste 1 (README): SIM / NÃO / NÃO CONSEGUI
Teste 2 (campos): SIM / NÃO / NÃO CONSEGUI
Teste 3 (limites): SIM / NÃO / NÃO CONSEGUI

O que ficou confuso:
Links que não abriram:
Sugestão de melhoria (opcional):
```

## 4B. Conferência biomédica — campos selecionados

Acesse os documentos [`ZIKA-DIC`](https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/dic_dados_zika.pdf) e [`TUBE-DIC`](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_NET_Tuberculose_23_07_2020.pdf). Confirme no PDF **rótulo, página, código e significado** de:

- **Zika:** `cs_gestant` (página 3) e mais dois campos Zika à escolha da [matriz](field_matrix.csv).
- **Tuberculose:** `TRATAMENTO` (página 1) e `SITUA_ENCE` (página 19). Verifique especialmente se o documento diferencia *tipo de entrada* de *situação de encerramento*.
- **Limite científico:** a existência de códigos de abandono **não** estabelece, isoladamente, indicador de perda de seguimento, denominador, coorte ou janela temporal.

Informe o que concorda, diverge ou não conseguiu avaliar; para cada ocorrência, anote **documento + página + código + conclusão curta**. A seleção é uma **conferência parcial**, não assinatura das 57 linhas nem homologação da distribuição 2024.

## 4C. Revisão metodológica — pesquisador

Avalie, apenas dentro de sua especialidade:

1. **Proveniência:** URLs, hashes de bytes e versionamento são descritos sem confundir integridade com assinatura do emissor?
2. **Concordância temporal:** que evidência adicional seria necessária para sustentar a correspondência entre instrumentos históricos e uma release 2024 específica?
3. **Semântica epidemiológica:** há extrapolações indevidas de `SITUA_ENCE`, `TRATAMENTO`, critérios de caso, coorte, temporalidade ou denominadores?
4. **Riscos de dados:** a demonstração e a matriz permanecem limitadas a metadados/fixtures fictícias, sem necessidade de acessar microdados?

Um parecer pode indicar **adequado dentro do escopo**, **correções necessárias**, **inconclusivo** ou **não avaliado**. Recomendações ou indicação de outro especialista não são registradas como aprovação.

## 5. Como formalizar a evidência de revisão

**Canal privado sugerido para devolutiva:** envie o relatório por e-mail para **miscrapha@gmail.com**, com o assunto `SINAN MCP — revisão documental externa`. A [issue #62](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/issues/62) é pública: não a use para registrar e-mail pessoal, assinatura, dados clínicos ou declarações de conflito. Não há obrigação de aprovar o projeto.

Envie o relatório ou resposta por escrito, com os campos abaixo:

| Campo | Informação necessária |
| --- | --- |
| Identificação | Nome, formação/área, instituição ou vínculo, contato para autenticar o parecer |
| Independência | Participação anterior no projeto, vínculo com responsáveis ou outros conflitos, inclusive ausência declarada |
| Escopo | Modalidade, documentos e seções/campos realmente inspecionados |
| Evidência | Fonte, versão ou hash quando pertinente; páginas, links e datas verificadas |
| Achados | Concordâncias, divergências, correções, limites e itens que ficaram sem exame |
| Decisão | Adequado no escopo / Correções necessárias / Inconclusivo / Rejeitado |
| Registro | Data e identificação do autor; assinatura eletrônica ou e-mail autenticável se aplicável |

**Consentimento e atribuição:** a identificação do revisor é solicitada para autenticar a devolutiva privada. Nome, afiliação, parecer integral e trechos identificáveis só serão publicados mediante autorização expressa; sem autorização, apenas achados técnicos anonimizados poderão ser resumidos. Evite dados pessoais desnecessários.

**A conferência automática de 7 PDFs e 57 ocorrências textuais não substitui a revisão independente humana.** A validação institucional, privacidade e eventual autorização de uso de dados reais seguem controles próprios. Revisores não devem receber nem encaminhar registros de pacientes.

O andamento e as pendências constam da [issue científica #62](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/issues/62). Respostas recebidas podem ser incorporadas ao histórico técnico **somente com registro fiel do conteúdo e da atribuição autorizada pelo autor**.
