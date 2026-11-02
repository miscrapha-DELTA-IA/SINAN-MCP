# SINAN MCP — catálogo de fontes e agravos (v0.4.0a4)

## Visão do projeto

O produto é **multiagravo**. Tuberculose (TUBE) é o caso de teste mais avançado e dengue (DENG) é o segundo piloto. O objetivo não é limitar a integração a duas doenças, mas chegar gradualmente a qualquer **agravo com fonte oficialmente publicada no escopo do SINAN**, respeitando ano, qualidade, dicionário, regras de divulgação e a existência de outros sistemas assistenciais e de vigilância.

Nenhuma ferramenta deve supor que existe uma base disponível apenas porque a notificação consta de uma lista. O exemplo sintético TUBE 2024/PI permanece o único conjunto numérico do MCP público.

## Três estágios (nunca confundir)

| Etapa | Permite | Exige |
|---|---|---|
| Referência de fonte | Encontrar doença, assunto, TABNET e documentação | Endereço oficial confirmado; nenhum valor |
| Dados importados no laboratório | Auditar localmente fontes de um agravo | Código real e dicionário do ano, procedência, completude, limitações |
| Agregado aprovado para consulta | Exibir uma tabela real com escopo estrito | Verificação independente, privacidade entre tabelas, revisão epidemiológica, fonte versionada e autorização |

Na implementação atual, `pesquisar_agravos`, `descrever_agravo` e `listar_fontes_oficiais` cumprem **somente a primeira etapa**. Os aliases de quatro letras são identificadores *internos* do projeto, **não** códigos de download do SINAN ou equivalentes a CID. O índice é exemplificativo e não compreende toda a lista nacional de notificação compulsória.

## Exemplos indexados

- TUBE — tuberculose (piloto)
- DENG — dengue (piloto)
- HANS — hanseníase
- CHIK — chikungunya; ZIKA — zika
- SIFA — sífilis adquirida; SIFC — sífilis congênita
- HEPA — hepatites virais; MENI — meningite
- VIOL — violência interpessoal/autoprovocada
- LEIV — leishmaniose visceral; LTAN — leishmaniose tegumentar
- ANIM — acidentes por animais peçonhentos
- COQU — coqueluche

Não inferir que todos possuem a mesma ficha, dicionário, regime de atualização, base nacional acessível ou método de encerramento. Cada agravo requer comprovação de fonte **e** validação específica.

## Fontes oficiais de navegação (não tabelas importadas)

- [Ministério da Saúde — Agravos de notificação](https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/svsa/agravos-de-notificacoes/agravos-de-notificacoes): acesso a documentação, microdados e TABNET.
- [DATASUS — TABNET](https://datasus.saude.gov.br/informacoes-de-saude-tabnet/): links para tabulações SINAN e módulos especializados.
- [Ministério da Saúde — SINAN](https://www.gov.br/saude/pt-br/composicao/svsa/sistemas-de-informacao/sinan/sinan): informação sobre escopo e organização.
- [Portal SINAN](https://portalsinan.saude.gov.br/): fichas e material técnico por agravo.

A página de índice não é uma tabela de dados. Para que valores oficiais sejam usados no MCP será necessário identificar a tabulação exata, data de extração, dimensões, filtros, versão, definição do indicador e referência reproduzível. Em seguida, verificar diferenças e reidentificação em relação a publicações anteriores.

## Roteiro de validação por agravo

1. Confirmar se o agravo é registrado e publicável no SINAN, a fonte histórica e qual sistema contém o dado desejado.
2. Comprovar o identificador correto do arquivo no DATASUS/PySUS e o dicionário aplicável ao ano.
3. Validar se o ano refere-se a arquivo, notificação, diagnóstico ou outro evento; registrar estado preliminar ou final.
4. Reconciliar contagens com TABNET/boletins oficiais; documentar tratamento de ignorados, duplicações, filtros e denominadores.
5. Gerar apenas tabelas candidatas localmente, avaliar cruzamentos e a existência de células recuperáveis por diferença.
6. Obter análise científica e de privacidade com responsável identificado e autorização explícita.
7. Disponibilizar somente artefatos estáticos imutáveis revisados, sem acessos a dados individuais ou SQL de origem; observar comportamento após atualização e capacidade de retirar uma publicação.

**Limiar de contagem mínima não equivale a anonimização formal.**

## Próximo trabalho

Preparar um importador independente de **tabelas oficiais pré-agregadas** com manifesto de proveniência por agravo, ano e filtro, conferência manual dos valores e controle de interações entre releases. Nenhum indicador real foi adicionado ao servidor neste marco.
