# Catálogo documental com proveniência — v1.1

[Centro de documentação](README.md) · [Revisão externa](instruments-2024/EXTERNAL_REVIEW.md) · [Evidências Zika/TB](instruments-2024/REVIEW_PROTOCOL.md)

**Data-base da curadoria:** 05/11/2026 · **Versão pública do software:** `0.4.0a6` · **Fonte canônica estruturada:** [`sinan_mcp/documentary_registry.json`](../sinan_mcp/documentary_registry.json) · **Situação:** 14 temas curados / 17 URLs de páginas oficiais institucionais identificadas. **Dados reais carregados: zero.**

## O que é e o que não é uma evidência

Uma página oficial de um órgão público pode apontar para fichas, dicionários, normas, painéis e arquivos de dados. **A identificação do link e do título não prova** que o documento foi obtido, conferido ou que aquele arquivo contém uma coorte válida. Por isso a estrutura devolve sempre:
- `verificacao=pagina_publica_identificada_titulo_escopo` e `data_conferencia=2026-11-05` para indicar apenas a checagem manual de página institucional;
- `arquivo_baixado_e_validado=false`, `conteudo_integral_auditado=false` e `dicionario_ano_versao_confrontado=false`;
- `arquivos_reais_importados=false` e `indicadores_reais_homologados=false`. Essas negações só se referem à **instância externa** do SINAN MCP;
- uma explicação escrita de por que cada página é relevante e seus limites documentais, especialmente quando a página não é específica (sífilis adquirida).

Nenhum teste HTTP é feito durante chamadas MCP. Os endereços são **links inertes de navegação** e não endpoints de extração ou download. Nenhuma URL fornece contagem do projeto, nem é permitido reembalar estatísticas citadas em páginas institucionais como se fossem resultado do servidor.

## Referências institucionais selecionadas

| Alias interno (não código oficial de download) | Agravo/tema | Portal de referência |
| --- | --- | --- |
| `TUBE` | Tuberculose | [Portal SINAN — instrumentos de registro](https://portalsinan.saude.gov.br/tuberculose) · [Vigilância TB no MS](https://www.gov.br/aids/pt-br/assuntos/tuberculose/vigilancia-epidemiologica) |
| `DENG` | Dengue | [Página temática do MS](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/d/dengue/dengue) |
| `CHIK` | Chikungunya | [Página temática do MS](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/c/chikungunya/chikungunya) |
| `ZIKA` | Zika | [Página temática do MS](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/z/zika-virus) · [Catálogo de recursos Zika no SUS](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus) |
| `HANS` | Hanseníase | [Página temática do MS](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/l/h/hanseniase) |
| `SIFA` | Sífilis adquirida | [Página geral Sífilis do MS (não específica)](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/s/sifilis) |
| `SIFC` | Sífilis congênita | [Página temática do MS](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/s/sifilis/congenita) |
| `HEPA` | Hepatites virais | [Índice oficial de publicações do MS](https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/svsa/hepatites/hepatites-virais) |
| `MENI` | Meningite | [Página temática do MS](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/m/meningite/) |
| `VIOL` | Violência interpessoal/autoprovocada | [Página institucional de vigilância de violências](https://www.gov.br/saude/pt-br/composicao/svsa/cnie/violencias-e-acidentes) |
| `LEIV` | Leishmaniose visceral | [Índice de publicações do MS](https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/svsa/leishmaniose-visceral) |
| `LTAN` | Leishmaniose tegumentar | [Índice de publicações do MS](https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/svsa/leishmaniose-tegumentar/leishmaniose-tegumentar) |
| `ANIM` | Acidentes por animais peçonhentos | [Página temática do MS](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/a/animais-peconhentos) · [Orientação oficial de acesso a dados](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/a/animais-peconhentos/como-obter-dados-epidemiologicos) |
| `COQU` | Coqueluche | [Página temática do MS](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/c/coqueluche) |

A ligação `ZIKA` ao catálogo de dados abertos, **isoladamente**, não comprova download ou inspeção dos conjuntos de dados. Em um processo documental separado, o **PDF do dicionário de Zika** foi de fato baixado e submetido à verificação de integridade; **nenhum arquivo de microdados ZIKA/2024 foi baixado por essa auditoria**. A referência de `SIFA` é **geral**, não uma ficha específica de sífilis adquirida. Índices de publicações são rotas para exploração manual, não comprovação do conteúdo integral de cada PDF. Os textos de várias páginas institucionais podem mudar após esta curadoria; ausência de rechecagem não deve ser apresentada como atualização em tempo real.

## Instrumentos e dicionários Zika/TB (expansão documental v1.1)

A partir de `0.4.0a6`, as ferramentas existentes `pesquisar_agravos` e `descrever_agravo` também indicam a existência de um **pacote documental apenas para `ZIKA` e `TUBE`**, formado por **7 PDFs oficiais únicos**, páginas e SHA-256 obtidos em auditoria e campos de instrumentos sem valores de pacientes. O retorno completo inclui **37 códigos Zika + 5 códigos comuns** para Zika, **15 códigos TB + 5 comuns** para TB. Os cinco campos comuns são repetidos de forma documental, não correspondem a 62 linhas independentes.

A prova automatizada de ocorrência dos códigos em suas páginas resultou em **57/57 tokens localizados** no [registro de auditoria e revisão independente pendente](instruments-2024/REVIEW_PROTOCOL.md). Não foi validada a interpretação semântica, tipagem de exportação, coerência de períodos e dados SINAN 2024; nenhuma revisão humana assinou parecer. O pacote é gerado a partir de `docs/instruments-2024/field_matrix.csv` e `source_manifest.json`, preservando testes cruzados com o JSON distribuído `sinan_mcp/public_instruments_2024.json`. O servidor MCP não faz download dos arquivos quando consultado.

## Consultar e verificar uma referência

1. Use `pesquisar_agravos(termo="hanseniase", limite=5)` ou sinônimos como `escorpiao`, `zikv`, `sifilis congenita`. A busca classifica alias/nome exato antes de prefixos, trechos e todas as palavras; não consulta a internet.
2. Erros de digitação como `tuberculoze` retornam `sugestoes_de_grafia`, **não** resultados presumidos.
3. Use `descrever_agravo(codigo_interno="ZIKA")`: o resultado traz URL, título, tipo, justificativa, data e estado de validação de cada referência do tema, além de cinco etapas necessárias antes de qualquer indicador.
4. Abra manualmente a página no portal oficial e localize a ficha/dicionário/release. **Registre fonte, título, identificação do recurso, versão, período, esquema, variáveis e data de acesso.**
5. Confronte o arquivo real com a documentação apropriada, verifique a regra de construção de casos, consistência, deduplicação, temporalidade, estimadores, controles de privacidade e revisão independente — **fora do servidor público**. Uma futura release com dados reais exigirá aprovação e arquitetura separadas.

## Segurança, revisões e controle de mudanças

- **Sem dados individuais**: módulo carregado apenas via `importlib.resources` de JSON empacotado. Não usa SQLite, PySUS, HTTP, SQL, ambiente privado, cookies ou chamadas a sistemas oficiais.
- **Lista de hospedagem estrita**: referências devem ser HTTPS e estar em `www.gov.br`, `portalsinan.saude.gov.br` ou `dadosabertos.saude.gov.br`. Links que não respeitem essa lista falham fechados antes de serem servidos; URLs não vêm de prompts do usuário.
- **Rastreabilidade**: aliases, 17 IDs de referência únicos, data, justificativa e tipo de página em fonte textual versionada; alterações passam por PR, testes e nova sonda externa após deploy manual.
- **Escopo do teste**: os testes validam links institucionais **registrados e identificados na revisão manual** e a integridade da estrutura; não provam disponibilidade HTTP futura nem exatidão do conteúdo de PDF. Use auditoria de acesso externa documentada para renovar a data, sem rotular como revisão de dados clínicos.
- **Próxima etapa científica:** concluir a inspeção humana dos documentos já auditados e confrontar versões e layouts anuais específicos, com revisão independente e sem publicação de microdados. Alterar estados de validação somente após evidência verificável.

**Nota de integridade:** as 120 linhas TUBE/2024/PI são inteiramente fictícias. Nenhum total nacional, estadual ou municipal de SINAN é produzido por este catálogo.

## Portais transversais

- [Ministério da Saúde — acesso aos agravos de notificação](https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/svsa/agravos-de-notificacoes/agravos-de-notificacoes).
- [DATASUS — TABNET](https://datasus.saude.gov.br/informacoes-de-saude-tabnet/).
- [Portal SINAN](https://portalsinan.saude.gov.br/).
