# SINAN-MCP · TUBE/2019 — encaminhamento para revisão independente

**Status:** pacote documental preparado para solicitação de parecer; **nenhum parecer recebido e nenhuma publicação autorizada**. Edição: 19/11/2026.

> **Está recebendo um primeiro convite?** Comece pelo [resumo de uma página e três perguntas para cada especialidade](TB2019_REVIEW_QUICKSTART.md). **Este dossiê é complementar e opcional para a resposta preliminar**. Não é preciso executar código, ter conta no GitHub ou analisar microdados para dar uma primeira orientação.

## Objetivo da revisão

Determinar se a extração e a interpretação de **quatro campos** do arquivo TUBE/2019 são metodologicamente adequadas para **descrições de registros do ano do arquivo**, e se algum agregado hipotético pode futuramente ser analisado sob governança de privacidade apropriada. Não solicitar aprovação genérica dos microdados nem interpretar as quatro colunas como base suficiente para indicadores epidemiológicos oficiais.

## Evidências técnicas disponíveis (execução local informada pelo operador)

| Gate | Evidência relatada | Escopo / limite |
| --- | --- | --- |
| DBC | `TUBEBR19.dbc`, `FINAIS`, 5.289.464 bytes, SHA-256 `7a00e29a5a309b794e21f1a650d3b04b9d3cb05fcc6ef8c9feefab3a961c9144` | Hash **local** de FTP não autenticado; não é atestado oficial de versão |
| Parquet PySUS | `TUBEBR19.parquet`, 3.603.114 bytes, SHA-256 `7c599143671bb8bd895e2dbd39a325682b12d9fd5a024fcec101bb76ed0fc277` | Mirror com conteúdo verificado pelo programa; não demonstra origem autenticada |
| Concordância entre fontes | `multiconjunto_4_campos_igual=true` | `ID_MN_RESI`, `CS_SEXO`, `CS_RACA`, `SITUA_ENCE`, com multiplicidades e normalização |
| Layout físico DBF | `C(6)`, `C(1)`, `C(1)`, `C(2)` na mesma ordem | `SITUA_ENCE` comporta representação `10`; não demonstra ocorrência de código 10 |
| SQLite privado | cinco verificações estruturais true, `sqlite_integridade=true` | Projeção de quatro campos, `status=desconhecido` |
| Códigos na origem | `dominios_brutos_sem_alertas=true` | Domínios **candidatos** dos dicionários disponíveis, sem validação histórica independente |
| Preservação | `projecao_sem_perda_de_codigos_preenchidos=true` | Sob as regras implementadas de normalização e `project_record`, não prova preservação byte a byte |
| Igualdade SQLite | `multiconjunto_original_projetado_igual_sqlite=true` | Valores projetados, não todas as colunas nem pessoas/episódios únicos |
| Publicação | `publicacao_autorizada=false` | O carregador legado de dados reais V1 está fail-closed na branch PR #72; sem protocolo V2 aprovado |

**Fontes:** [registro de concordância](TB2019_FOUR_COLUMN_CONCORDANCE.md), [matriz histórica](TB2019_HISTORICAL_DICTIONARY_CROSSWALK.md), [matriz de método e privacidade](TB2019_DICTIONARY_PRIVACY_REVIEW.md), [modelo de ameaças V2](REAL_RELEASE_V2_THREAT_MODEL.md) e [PR #72](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/pull/72).

## Referências documentais a verificar pelos revisores

- [Dicionário SINAN NET Notificação Individual v5 (revisado em julho de 2010)](https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/DIC_DADOS_Notificacao_Individual_v5.pdf): `CS_SEXO`, `CS_RACA`, `ID_MN_RESI`.
- [Dicionário SINAN NET Tuberculose v5.0](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_Tuberculose.pdf): `SITUA_ENCE`, opções 1–10; a vigência exata em 2019 precisa ser atestada.
- [Dicionário TB com nome de arquivo datado de 23/07/2020](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_NET_Tuberculose_23_07_2020.pdf): comparação de versões posterior ao arquivo.
- [Caderno de Análise SINAN Tuberculose 2019](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/Caderno_de_Analise_2019.pdf): unidade de análise, duplicidades, coortes, seleção e denominadores.

## Escopos de revisão e questões decidíveis

### A. Reprodutibilidade computacional — revisor técnico independente

- Inspecionar código da branch auditada, especialmente `tb2019_parity.py`, `tb2019_source_audit.py`, `core.project_record` e os testes fictícios.
- Confirmar que o comparador de multiconjuntos preserva multiplicidades e que normalizações como `"123.0" -> "123"` e valores ausentes são adequadas *campo a campo*.
- Verificar como o código e o ambiente podem ser reproduzidos em uma instalação autorizada; registrar *commit*, Python, dependências, data/hora e identificadores de conteúdo.
- Decidir se o relatório do operador é reproduzível e o que **não** demonstra, sem copiar DBC/DBF/SQLite para GitHub, e-mail, LLM ou serviços compartilhados.

### B. Semântica e coorte — revisor com experiência em vigilância/SINAN-TB

- Identificar a vigência documental aplicável a cada campo da edição 2019; resolver a diferença `Varchar2(1)` no texto versus `C(2)` no DBF de `SITUA_ENCE`.
- Confirmar códigos e tratamento de ausentes, ignorados, municípios e `SITUA_ENCE=10`.
- Validar a unidade: **registro do arquivo TUBE/2019**, sem deduplicação longitudinal ou atribuição automática de ano de diagnóstico.
- Declarar explicitamente se contagem de registros por uma dimensão pode ser descrita, com quais ressalvas, e por que **incidência, cura e abandono de coorte** não são inferíveis a partir de apenas quatro colunas.
- Indicar se é necessário ampliar a projeção em ambiente local *antes* de qualquer análise oficial.

### C. Privacidade e divulgação — revisor de privacidade/governança

- Avaliar se uma partição única de UF/ano/dimensão, com `k=20` e `min_partition=100`, é adequada para o contexto, incluindo inferência por diferença, combinações com outras publicações e interseções.
- Não tratar limites de células isoladamente como garantia de anonimização, segurança ou base jurídica.
- Verificar a separação entre SQLite privado, pacotes candidatos, repositório e serviço MCP público; confirmar o bloqueio V1 e revisar a proposta V2.
- Determinar a necessidade de autorização institucional/jurídica e quem tem autoridade para assinar um pacote específico.

## Formato mínimo de parecer (a preencher por humanos autorizados)

- **Função do revisor:** [técnico independente / vigilância e método / privacidade e governança].
- **Identificação e vínculo institucional:** [a confirmar, em meio apropriado].
- **Versão analisada:** [commit, data, documentos e edição].
- **Verificações reproduzidas:** [sim / não / parcialmente; quais].
- **Achados e limitações:** [referências e severidade].
- **Correções obrigatórias antes de novo parecer:** [itens verificáveis].
- **Decisão:** [apto apenas para pesquisa privada / necessita correções / passível de avaliação de divulgação sob pacote específico].
- **Registro/assinatura do parecer:** [meio institucional ou mecanismo de atestação apropriado; **não** basta um nome digitado no JSON].

Nenhum campo acima é preenchido automaticamente. Não há revisão externa aprovada neste documento.

## Critérios de bloqueio contínuo

- `historical_dictionary_compatibility_confirmed=false` até validação independente;
- `scientific_review_independent=false`, `privacy_review_independent=false`, `publication_authorized=false` até pareceres e decisão aplicável;
- `aggregate_contract.load_approved_release` rejeita V1 na PR #72, mesmo com `status_informado=final` e nomes em texto;
- serviço MCP público e túnel não recebem arquivos nem dados reais;
- incidentes, divergências, falta de autorização ou incapacidade de reprodução: **nenhuma liberação**.

**Próxima decisão de projeto:** após os pareceres, definir se continuamos com um piloto apenas descritivo de registros ou se precisamos de novo estudo de coorte com outras variáveis e modelo de governança mais robusto. Ambos requerem plano metodológico explícito.
