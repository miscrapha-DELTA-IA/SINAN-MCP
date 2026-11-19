# SINAN-MCP | TUBE/2019 — revisão preliminar simplificada

**Leitura rápida para especialistas convidados · versão 19/11/2026**

**O pedido:** uma impressão técnica inicial, **não** uma homologação, assinatura formal, reprodução completa dos testes ou autorização de publicação. Basta responder às **três perguntas da sua especialidade** por e-mail; se não tiver elementos para responder, marque "não sei / preciso de evidência". Não é necessário instalar programas, clonar o repositório, executar comandos ou acessar microdados.

## 1. O que é o projeto e o que foi verificado

O [SINAN-MCP](https://github.com/miscrapha-DELTA-IA/SINAN-MCP) é uma infraestrutura experimental para consultar informações epidemiológicas de forma controlada. O piloto atual utiliza o arquivo **TUBE/2019** e uma projeção de **quatro variáveis**, sem identificadores diretos: `ID_MN_RESI` (município de residência), `CS_SEXO` (sexo registrado), `CS_RACA` (raça/cor registrada) e `SITUA_ENCE` (situação de encerramento).

**Resultados técnicos informados pelo operador, ainda não reproduzidos independentemente:**

- DBC do DATASUS e Parquet do PySUS apresentaram **igualdade do multiconjunto de quatro campos**, incluindo repetições, após normalização definida no código.
- O banco SQLite **privado** passou em cinco verificações estruturais e de consistência dos códigos projetados.
- Uma auditoria local dos códigos **antes da projeção** encontrou domínios documentais candidatos sem alertas, sem perda de códigos preenchidos sob as regras testadas e com igualdade entre projeção do DBC e SQLite.
- O cabeçalho físico do DBF indica `SITUA_ENCE` do tipo caractere e largura **2**, capaz de comportar `10`. O dicionário TB v5.0 traz o código 10 e uma indicação textual `Varchar2(1)`; essa diferença precisa de interpretação documental.

**Ainda não demonstrado:** compatibilidade exata dos dicionários com a edição de 2019, equivalência de todas as colunas, identificação de pessoas/episódios únicos, coortes de diagnóstico, indicadores epidemiológicos oficiais, revisão de privacidade e autorização de dados reais. O MCP público continua **sintético** e o carregador legado de agregados reais V1 está **bloqueado na branch da PR #72**, não necessariamente na implantação.

## 2. Três perguntas para seu perfil (responda somente a um bloco)

### A — Vigilância epidemiológica / SINAN-TB

1. As definições propostas para **município de residência, sexo, raça/cor e situação de encerramento** são adequadas para interpretar *registros do arquivo TUBE/2019*, ou há ressalvas essenciais?
2. A diferença entre `SITUA_ENCE=C(2)` no DBF e `Varchar2(1)` no dicionário merece uma correção metodológica, ou é principalmente uma inconsistência documental? **É necessário confirmar a vigência de um dicionário específico para 2019?**
3. É adequado restringir o piloto a **contagens descritivas de registros por dimensão**, sem falar em incidência, cura/abandono de coorte ou pessoas únicas? O que falta para validar esse escopo?

### B — Privacidade e governança

1. Há risco evidente que inviabilize até **considerar**, futuramente, um agregado de **uma UF, um ano do arquivo e uma dimensão demográfica**?
2. Que proteção adicional, além de limitar células pequenas (política experimental `k>=20`, partição `>=100`), deveria ser exigida para impedir inferência por comparação com outras publicações?
3. Que processo de **parecer/autoridade institucional** seria necessário antes de avaliar a divulgação de um pacote específico? O projeto **não** solicita autorização agora.

### C — Revisão computacional / reprodutibilidade

1. O método descrito de comparar **multiconjuntos** com multiplicidades e normalização de ausentes é defensável para a concordância restrita de quatro campos? Quais testes faltam?
2. A checagem pré-projeção seguida da comparação com o SQLite é suficiente como **evidência preliminar**, sem afirmar equivalência byte a byte ou integral?
3. Que evidência adicional mínima seria necessária para uma **reprodução independente**? Nenhum dado real é disponibilizado ao revisor nesta etapa.

## 3. Responda copiando somente este pequeno bloco

> **Perfil:** A / B / C  
> **Q1:** Adequado / Com ressalvas / Não adequado / Não sei  
> **Q2:** Adequado / Com ressalvas / Não adequado / Não sei  
> **Q3:** Adequado / Com ressalvas / Não adequado / Não sei  
> **Observação essencial ou correção prioritária:** [texto livre, se houver]  
> **Aceitaria uma revisão mais aprofundada posteriormente?** Sim / Não / Talvez

Não é necessário preencher justificativas extensas. Uma resposta breve com as principais ressalvas já ajuda a orientar a próxima versão. **Ela será tratada somente como feedback preliminar, nunca como aprovação formal, homologação epidemiológica ou autorização para publicar dados reais.**

## 4. Referências sob demanda (leitura opcional)

- [Dicionário da Notificação Individual v5 (revisão julho/2010)](https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/DIC_DADOS_Notificacao_Individual_v5.pdf) — campos comuns.
- [Dicionário de Tuberculose SINAN NET v5.0](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_Tuberculose.pdf) — situação de encerramento.
- [Caderno de Análise 2019](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/Caderno_de_Analise_2019.pdf) — distinção entre coortes, transferências e registros.
- [Dossiê técnico completo de revisão](TB2019_INDEPENDENT_REVIEW_HANDOFF.md), [matriz histórica](TB2019_HISTORICAL_DICTIONARY_CROSSWALK.md), [código e testes na PR #72](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/pull/72) — **somente se quiser aprofundar**.

**Privacidade:** não enviar DBC/DBF/Parquet, SQLite, relatórios privados, frequências estratificadas ou registros individuais por e-mail, GitHub ou LLM. Esta página não contém microdados e não representa parecer de revisão já emitido.
