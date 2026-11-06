# Validação documental | Zika e tuberculose (2024)

**Data-base da verificação:** 05/11/2026 · **Escopo:** somente documentos públicos, sem registros individuais.  
[Centro de documentação](../README.md) · [Guia para revisores externos](EXTERNAL_REVIEW.md) · [Matriz CSV](field_matrix.csv) · [Manifesto JSON](source_manifest.json)

## Sobre o projeto e esta avaliação

O **SINAN MCP** é um projeto independente e de código aberto que organiza referências documentais do Sistema de Informação de Agravos de Notificação e fornece uma demonstração pública de software com dados inteiramente fictícios. Não é um sistema do Ministério da Saúde, SINAN ou DATASUS.

Este documento registra **evidência de integridade documental**, não a homologação de dados epidemiológicos. Destina-se a pesquisadores, revisores e responsáveis técnicos que precisam distinguir o que foi verificado do que ainda depende de julgamento profissional.

| Controle | Resultado em 05/11/2026 | Limite |
| --- | --- | --- |
| PDFs oficiais, hash, tamanho e páginas | **7/7 conferidos automaticamente** | Sem assinatura criptográfica do emissor |
| Códigos localizados na página citada | **57/57 ocorrências textuais** | Rótulos, tipos e contexto não validados por revisão humana |
| Compatibilidade com distribuição SINAN 2024 | **Não verificada** | Não houve confronto de layout de release |
| Três avaliações independentes | **Pendentes** | Sem pareceres, identidades ou decisões presumidas |
| Uso de dados reais e publicação de indicadores | **Não autorizado** | Exige processo jurídico, científico e técnico separado |

### Como participar da revisão

O [guia de revisão externa](EXTERNAL_REVIEW.md) explica, em linguagem acessível, o procedimento para avaliação de clareza/usabilidade, conferência biomédica parcial e parecer metodológico. Ele inclui **links diretos**, campos selecionados, roteiro e modelo de devolutiva. Uma avaliação de usabilidade não substitui um parecer científico independente.


## Escopo documental e limitações

- **Zika:** disponível no catálogo oficial do Ministério da Saúde um [dicionário SINAN Net de Zika](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus/resource/58038262-c745-46ea-979b-8727eb08ec5c), PDF de **8 páginas**; a página do recurso informa arquivo de dados atualizado em **22/03/2024** e metadados alterados em **14/07/2025**. O documento, porém, não traz um identificador de versão de layout suficientemente preciso para afirmar que a extração de 2024 usa esse esquema integralmente.
- **Zika — ficha/instrucional:** o [Portal SINAN Zika](https://portalsinan.saude.gov.br/zika) remete à ficha **genérica de notificação/conclusão SINAN NET**, seu instrucional e ao dicionário de notificação individual. Não confundir a ficha de conclusão com um instrumento específico de investigação de Zika. O dicionário comum é versão **5.0**, revisto em **novembro de 2018**, e possui **23 páginas**.
- **TB:** o [Portal SINAN Tuberculose](https://portalsinan.saude.gov.br/tuberculose) aponta dicionário específico SINAN NET versão **5.0** (**22 páginas**, URL com `23_07_2020`), ficha de notificação/investigação (**1 página**, rodapé 2014) e ficha de acompanhamento (**1 página**, rodapé 2014). O uso desses instrumentos para todas as exportações **2024 não foi demonstrado**.
- **Atenção a alterações futuras:** o [Ministério da Saúde informou em abril/2025](https://www.gov.br/aids/pt-br/assuntos/noticias/2025/abril/aprovados-em-grupo-de-trabalho-tripartite-os-campos-da-ficha-de-investigacao-de-tuberculose-que-compora-o-e-sus-sinan) mudanças aprovadas para ficha de TB a integrar o e-SUS Sinan. Não se deve misturar versões futuras ou atuais com um esquema histórico sem prova.
- **Estado do projeto:** matriz documental com **37 entradas de Zika**, **15 campos críticos da TB** e **5 campos comuns**, totalizando **57 registros documentais**. Os cinco campos comuns são reutilizados nos dois pacotes de apresentação: **42 registros no pacote Zika e 20 no de TB (62 apresentações, sem 62 fontes independentes)**. Apenas nomes, tipos resumidos, páginas de origem e pontos de conferência; isto **não significa** que os 57 nomes sejam colunas presentes em qualquer arquivo 2024.

## Documentos oficiais e versão observada

| ID | Documento | Páginas esperadas | URL oficial |
| --- | --- | ---: | --- |
| `ZIKA-DIC` | Dicionário Zika do MS, edição visível sem número de versão discriminante | 8 | [PDF](https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/dic_dados_zika.pdf) |
| `ZIKA-FICHA` | Ficha genérica notificação/conclusão | 1 | [PDF](https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/Ficha_conclusao_v5.pdf) |
| `ZIKA-INSTR` | Instrucional de preenchimento da ficha | 3 | [PDF](https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/Ficha_conclusao_v5_instr.pdf) |
| `COMMON-NINDIV` | Dicionário de notificação individual SINAN NET v5.0 (nov. 2018) | 23 | [PDF](https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/DIC_DADOS_NET_Not_Individual_rev.pdf) |
| `TUBE-DIC` | Dicionário de TB SINAN NET v5.0 | 22 | [PDF](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_NET_Tuberculose_23_07_2020.pdf) |
| `TUBE-FICHA` | Ficha de notificação/investigação de TB | 1 | [PDF](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/Tuberculose_v5.pdf) |
| `TUBE-ACOMP` | Ficha de acompanhamento TB | 1 | [PDF](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/Tuberculose_Acomp_v5.pdf) |

Todos são *instrumentos ou dicionários*, não datasets. **Jamais substituir** as URLs por `ZIKABR24.parquet.zip`, `ZIKABR24.json.zip`, DBF ou outros arquivos contendo observações de pessoas. Não salvá-los no repositório nem executá-los no processo público.

## Matriz de campos

[`field_matrix.csv`](field_matrix.csv) contém código, nome documental, tipo resumido, página de referência em PDF (base 1), fonte, ano-alvo pretendido, marcador temporal observado da fonte e duas colunas de bloqueio. `ano_alvo=2024` foi mantido para compatibilidade e não denota uma versão aprovada do esquema; `ano_alvo_pretendido` explicita a intenção e `ano_documento_observado` registra apenas a evidência disponível (por exemplo, 2020 no nome da URL de TB, sem comprovar release 2024):

- `status_concordancia_extracao_2024=NOT_VERIFIED`: significa que **não** houve comparação com cabeçalhos e tipagem de um arquivo específico de distribuição 2024.
- `status_revisao_independente=PENDING`: significa que não houve leitura e aprovação por revisores humanos independentes.

Exemplos de alto risco:
1. O dicionário **Zika** usa `cs_raca`, `cs_sexo`, `id_agravo`, `dt_notific`, enquanto o dicionário **comum** fornece códigos DBF `CS_RACA`, `CS_SEXO`, `ID_AGRAVO`, `DT_NOTIFIC`. Normalizar texto não equivale a provar campos correspondentes entre arquivos.
2. Em **TB**, `TRATAMENTO` (tipo de entrada), `TESTE_MOLEC` (teste molecular) e `SITUA_ENCE` (situação de encerramento) tiveram as categorias descritas no dicionário v5.0 transcritas na matriz; o encerramento ocupa as páginas 19–20 e `TRATAMENTO` inclui **reingresso após abandono**. A presença de `2=abandono` e `10=abandono primário` **não** define, por si, numerador ou denominador oficial. O algoritmo de LTFU demanda coorte, modalidade, período, entrada, vinculação, desfecho e revisão epidemiológica.
3. Há códigos de categorias `9` ignorado e campos internos/condicionais; não converter ausências em não-casos.
4. `2024` no nome do recurso público refere-se ao **ano-alvo do conjunto**, não à data de criação, à versão do sistema nem à data de revisão da ficha.
5. Informações de CPF, nome, prontuário, CNS, saúde, diagnóstico, endereço e vinculação não podem ingressar no MCP externo. A matriz só publica **metadados sobre definição de campo**, nunca seus valores.

## Integridade de arquivos e reprodutibilidade

[`source_manifest.json`](source_manifest.json) fixa **sete URLs exatas**, números de páginas e versões identificadas. [`scripts/audit_instruments_2024.py`](../../scripts/audit_instruments_2024.py) faz:

- **Padrão offline:** valida URLs permitidas, documentação e matriz sem abrir a internet.
- Com `--fetch`: baixa somente os sete PDFs explicitamente fixados, recusa qualquer redirecionamento, limite de 12 MiB por arquivo, MIME PDF, assinatura inicial `%PDF-`, marcador terminal `%%EOF`, e usa `pypdf==5.9.0` fixado na CI para conferir páginas.
- Calcula **SHA-256 e bytes da resposta obtida**, carimbo UTC e nome do documento. Descarta bytes temporários e exporta somente o JSON de proveniência/hash para a CI.
- A **integridade dos bytes obtidos** não equivale à assinatura digital do órgão emissor, autenticidade histórica, prova de exaustividade ou conformidade com a versão 2024.
- Repetições devem comparar os hashes: mudança inesperada requer diff de PDF, atualização de matriz e reaprovação. Não atualizar hash "esperado" automaticamente para fazê-lo passar.

O workflow [`instruments-2024-audit.yml`](../../.github/workflows/instruments-2024-audit.yml) cria **artefato JSON de metadata** com retenção por sete dias. Nenhum PDF ou microdado é enviado como artifact. Falha fechada se fonte ou paginação divergirem.

## Hashes fixados a partir da checagem dos bytes oficiais

| Documento | SHA-256 | Bytes | Páginas |
| --- | --- | ---: | ---: |
| ZIKA-DIC | `80b50522c67f550ee2c96aad315dddd524bf38b1c7fa1c40b2ee341cc41cdf0d` | 333.298 | 8 |
| ZIKA-FICHA | `b87ebfd414502c21eb0e7e269b2329eaa66fd6fe1086913b9b46dbfb7f9a93e1` | 15.666 | 1 |
| ZIKA-INSTR | `635578b83d7a5d3be21234ffabbe8a94e40deed21109dd157a5333b22f100997` | 84.434 | 3 |
| COMMON-NINDIV | `db365c9632690ade275eb609badeada8033b042165605a734c5c242048ede221` | 608.286 | 23 |
| TUBE-DIC | `0e0aac57f975343917552225cfd920c88f096f99cba46968c5bca6f46c291b08` | 328.708 | 22 |
| TUBE-FICHA | `77b19f9d41d458bac7c749d25a0b5b6b90c542b0fd7377e371b401abf019ed23` | 26.671 | 1 |
| TUBE-ACOMP | `b0e9d0ef283bb9525b5192eeca76ad611947d315929f383005a27769bec1867b` | 11.927 | 1 |

**Proveniência da evidência:** [GitHub Actions — Official Zika TB PDF evidence audit, execução 41994351476](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/actions/runs/41994351476). O evento de download de 5 de novembro de 2026 confirmou cabeçalho HTTP 200, PDF e paginação. Essa medição da integridade de bytes recebidos é um *lock* de release reprodutível, não certificação do órgão produtor, nem substitui a confrontação com o arquivo de distribuição 2024.

## Verificação automatizada de ocorrência dos identificadores

A [CI histórica de verificação das páginas](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/actions/runs/41994975411) confirmou, **antes do reforço do verificador**, com os **mesmos hashes bloqueados** dos sete PDFs, que os códigos de campo transcritos na matriz estão presentes no texto extraído da **página indicada**: 37/37 entradas de Zika, 15/15 campos críticos de TB e 5/5 campos comuns, perfazendo **57/57 ocorrências de código de campo**. A execução histórica usou `pypdf==5.9.0` e comparações por substring normalizada. A revisão proposta passa a exigir limites de identificadores, inclusive quando o extrator varia separadores. A [execução 42144137431](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/actions/runs/42144137431) concluiu com **sucesso** o novo teste delimitado sobre os PDFs oficiais com hashes fixados; esse novo resultado limita-se a ocorrências textuais e **não** é aprovação humana nem concordância com o esquema 2024.

**Limite indispensável:** mesmo com limites de identificador no teste automatizado, é apenas uma checagem textual do código na página, **não** revisão de rótulo, descrição semântica, tipagem DBF, codificação de valores, obrigatoriedade, coorte, validade temporal ou mapeamento para um arquivo de 2024. Em especial, tokens curtos podem ocorrer em mais de um contexto; um revisor deverá conferir cada linha visualmente e registrar a versão/arquivo efetivamente analisados. Não transformar `57/57` em concordância homologada de esquema SINAN 2024.

## Avaliação científica independente

Preencher [`independent_review_template.json`](independent_review_template.json) **somente após** as avaliações humanas efetivas. É proibido atribuir nomes, assinaturas, conflito de interesse ou aprovação fictícios. Três pareceres distintos e verificáveis:

1. **Epidemiologia:** confirmar definições de notificação/caso, características de SINAN NET, temporalidade (ano do arquivo x ano de notificação/diagnóstico), etapas de encerramento, categorias TB e referências metodológicas.
2. **Sistemas e informação em saúde:** conferir **todas as 37 linhas Zika** e **toda a seleção TB** com PDFs exatos + hashes; apontar diferenças nos nomes DBF/nomes lógicos, versão, requisitos, campos internos e fontes; revisar mapeamento específico de 2024, se possível sem dados identificáveis.
3. **Privacidade e ética:** confirmar que a matriz contém somente metadados, sem exemplos de registros, arquivos, endpoints de importação, consultas nominativas ou tabelas de contagem real; avaliar direito de uso dos documentos, transmissão e gravação dos artefatos.

Para cada pessoa: identificação e afiliação verdadeiras, declaração de conflito, evidência das páginas/campos inspecionados, decisão (`APPROVED`, `CHANGES_REQUIRED` ou `REJECTED`), data, vínculo para parecer autenticável e hashes dos PDFs lidos. O responsável pelo repositório registra o PR de revisão com diff e encaminha aos revisores independentes. **Um check automático ou a leitura pelo próprio autor não substitui o parecer.**

O [Caderno de Indicadores da Tuberculose, edição preliminar de 2023](https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/svsa/tuberculose/caderno-de-indicadores-da-tuberculose) é uma referência metodológica complementar para futura revisão da coorte e de indicadores. **Não integra o conjunto de sete PDFs com hash fixado** e sua leitura não homologou nenhuma estimativa do projeto.

A curadoria documental pode ser divulgada com as limitações declaradas. Dados reais e indicadores exigem autorização específica, compatibilidade documental com a distribuição de 2024 e avaliação científica e de privacidade em processo separado.

## Registro de revisão e rastreabilidade

A auditoria de 5 de novembro de 2026 confirmou **a integridade dos bytes de sete PDFs oficiais** e a ocorrência textual de **57 identificadores** nas páginas declaradas. Essas verificações não validam categorias, definições epidemiológicas ou equivalência com a distribuição SINAN 2024.

As **tarefas pendentes** e o recebimento de pareceres independentes estão concentrados na [issue científica #62](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/issues/62). Este documento permanece como registro de fontes, método, resultados e limitações, sem listas de tarefas de desenvolvimento.
