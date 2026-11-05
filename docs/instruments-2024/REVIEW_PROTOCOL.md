# Pacote de validação documental — Zika 2024 e tuberculose 2024

**Criado:** 05/11/2026 • **Repositório:** SINAN-MCP • **Escopo:** apenas PDFs oficiais de documentação, **sem acesso a microdados**.

## Conclusão atual, rigorosamente delimitada

- **Zika:** disponível no catálogo oficial do Ministério da Saúde um [dicionário SINAN Net de Zika](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus/resource/58038262-c745-46ea-979b-8727eb08ec5c), PDF de **8 páginas**; a página do recurso informa arquivo de dados atualizado em **22/03/2024** e metadados alterados em **14/07/2025**. O documento, porém, não traz um identificador de versão de layout suficientemente preciso para afirmar que a extração de 2024 usa esse esquema integralmente.
- **Zika — ficha/instrucional:** o [Portal SINAN Zika](https://portalsinan.saude.gov.br/zika) remete à ficha **genérica de notificação/conclusão SINAN NET**, seu instrucional e ao dicionário de notificação individual. Não confundir a ficha de conclusão com um instrumento específico de investigação de Zika. O dicionário comum é versão **5.0**, revisto em **novembro de 2018**, e possui **23 páginas**.
- **TB:** o [Portal SINAN Tuberculose](https://portalsinan.saude.gov.br/tuberculose) aponta dicionário específico SINAN NET versão **5.0** (**22 páginas**, URL com `23_07_2020`), ficha de notificação/investigação (**1 página**, rodapé 2014) e ficha de acompanhamento (**1 página**, rodapé 2014). O uso desses instrumentos para todas as exportações **2024 não foi demonstrado**.
- **Atenção a alterações futuras:** o [Ministério da Saúde informou em abril/2025](https://www.gov.br/aids/pt-br/assuntos/noticias/2025/abril/aprovados-em-grupo-de-trabalho-tripartite-os-campos-da-ficha-de-investigacao-de-tuberculose-que-compora-o-e-sus-sinan) mudanças aprovadas para ficha de TB a integrar o e-SUS Sinan. Não se deve misturar versões futuras ou atuais com um esquema histórico sem prova.
- **Estado do projeto:** matriz documental gerada com **37 campos numerados de Zika**, **15 campos críticos da TB** e **5 campos comuns da notificação individual**. Apenas nomes, tipos resumidos, páginas de origem e pontos de conferência; isto **não significa** que os 57 nomes sejam colunas presentes em qualquer arquivo 2024.

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

[`field_matrix.csv`](field_matrix.csv) contém código, nome documental, tipo resumido, página de referência em PDF (base 1), fonte e duas colunas de bloqueio:

- `status_concordancia_extracao_2024=NOT_VERIFIED`: significa que **não** houve comparação com cabeçalhos e tipagem de um arquivo específico de distribuição 2024.
- `status_revisao_independente=PENDING`: significa que não houve leitura e aprovação por revisores humanos independentes.

Exemplos de alto risco:
1. O dicionário **Zika** usa `cs_raca`, `cs_sexo`, `id_agravo`, `dt_notific`, enquanto o dicionário **comum** fornece códigos DBF `CS_RACA`, `CS_SEXO`, `ID_AGRAVO`, `DT_NOTIFIC`. Normalizar texto não equivale a provar campos correspondentes entre arquivos.
2. Em **TB**, `TRATAMENTO` (tipo de entrada) e `SITUA_ENCE` (situação de encerramento) têm categorias e condicionais próprias. A presença de `2=abandono` e `10=abandono primário` **não** define, por si, numerador ou denominador oficial. O algoritmo de LTFU demanda coorte, modalidade, período, entrada, vinculação, desfecho e revisão epidemiológica.
3. Há códigos de categorias `9` ignorado e campos internos/condicionais; não converter ausências em não-casos.
4. `2024` no nome do recurso público refere-se ao **ano-alvo do conjunto**, não à data de criação, à versão do sistema nem à data de revisão da ficha.
5. Informações de CPF, nome, prontuário, CNS, saúde, diagnóstico, endereço e vinculação não podem ingressar no MCP externo. A matriz só publica **metadados sobre definição de campo**, nunca seus valores.

## Integridade de arquivos e reprodutibilidade

[`source_manifest.json`](source_manifest.json) fixa **sete URLs exatas**, números de páginas e versões identificadas. [`scripts/audit_instruments_2024.py`](../../scripts/audit_instruments_2024.py) faz:

- **Padrão offline:** valida URLs permitidas, documentação e matriz sem abrir a internet.
- Com `--fetch`: baixa somente os sete PDFs explicitamente fixados, recusa qualquer redirecionamento, limite de 12 MiB por arquivo, MIME PDF, assinatura inicial `%PDF-`, marcador terminal `%%EOF`, e usa `pdfinfo` do Poppler para conferir páginas.
- Calcula **SHA-256 e bytes da resposta obtida**, carimbo UTC e nome do documento. Descarta bytes temporários e exporta somente o JSON de proveniência/hash para a CI.
- A **integridade dos bytes obtidos** não equivale à assinatura digital do órgão emissor, autenticidade histórica, prova de exaustividade ou conformidade com a versão 2024.
- Repetições devem comparar os hashes: mudança inesperada requer diff de PDF, atualização de matriz e reaprovação. Não atualizar hash "esperado" automaticamente para fazê-lo passar.

O workflow [`instruments-2024-audit.yml`](../../.github/workflows/instruments-2024-audit.yml) cria **artefato JSON de metadata** com retenção por sete dias. Nenhum PDF ou microdado é enviado como artifact. Falha fechada se fonte ou paginação divergirem.

## Revisão independente — protocolo de homologação

Preencher [`independent_review_template.json`](independent_review_template.json) **somente após** as avaliações humanas efetivas. É proibido atribuir nomes, assinaturas, conflito de interesse ou aprovação fictícios. Três pareceres distintos e verificáveis:

1. **Epidemiologia:** confirmar definições de notificação/caso, características de SINAN NET, temporalidade (ano do arquivo x ano de notificação/diagnóstico), etapas de encerramento, categorias TB e referências metodológicas.
2. **Sistemas e informação em saúde:** conferir **todas as 37 linhas Zika** e **toda a seleção TB** com PDFs exatos + hashes; apontar diferenças nos nomes DBF/nomes lógicos, versão, requisitos, campos internos e fontes; revisar mapeamento específico de 2024, se possível sem dados identificáveis.
3. **Privacidade e ética:** confirmar que a matriz contém somente metadados, sem exemplos de registros, arquivos, endpoints de importação, consultas nominativas ou tabelas de contagem real; avaliar direito de uso dos documentos, transmissão e gravação dos artefatos.

Para cada pessoa: identificação e afiliação verdadeiras, declaração de conflito, evidência das páginas/campos inspecionados, decisão (`APPROVED`, `CHANGES_REQUIRED` ou `REJECTED`), data, vínculo para parecer autenticável e hashes dos PDFs lidos. O responsável pelo repositório registra o PR de revisão com diff e encaminha aos revisores independentes. **Um check automático ou a leitura pelo próprio autor não substitui o parecer.**

**Poderemos liberar apenas a curadoria documental**, se as regras de ausência de dados e alegações científicas forem mantidas; usar dados reais e indicadores exige autorização, compatibilidade comprovada da release 2024 e processos separados, nunca por alteração simples deste manifesto.

## Critérios objetivos para a etapa seguinte

- [x] URLs e versões aparentes dos sete instrumentos/dicionários oficiais localizados.
- [x] Matriz de metadados de 57 linhas, sem valores de pacientes.
- [ ] SHA-256 e páginas **verificados pelos bytes oficiais** em um relatório de CI reproduzível.
- [ ] Confronto independente **de todas** as linhas da matriz com PDFs com hash bloqueado.
- [ ] Divergências entre dicionário comum, específico e arquivo 2024 resolvidas em instrumento apropriado.
- [ ] Três pareceres humanos independentes, incluindo privacidade.
- [ ] Aprovação científica de definições de caso, coleta, datas, regras de vinculação e encerramento.
- [ ] Permissão para uso de dados reais ou publicação de números: **não autorizada** e fora do escopo atual.
