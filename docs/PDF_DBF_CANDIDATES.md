# Rascunho DBF extraído de PDF local — Dengue/Chikungunya

## Motivação observada no primeiro confronto local

A comparação privada do pacote DENGBR24.csv.zip de 2024, após obtenção no computador do operador, encontrou **121 nomes de colunas**. Apenas **3 campos** estavam no contrato de demonstração; os outros **118 eram campos fora da transcrição, não erros de layout confirmados**. O operador conseguiu gerar um parecer privado marcado como pendente. O programa não recebeu microdados por chat ou GitHub.

Para diminuir transcrição repetitiva, uma ferramenta administrativa **estritamente local** extrai candidatos a nomes DBF de um PDF de dicionário e registra páginas. É uma proposta de transcrição para revisão humana, e NÃO substitui a comparação com o dicionário mais recente.

## Evidência documental diferente da validação anual

O documento [Portal SINAN — Dicionário de Dados Sinan Online 3.0, Dengue/Chikungunya](https://portalsinan.saude.gov.br/images/documentos/Agravos/Dengue/DIC_DADOS_ONLINE.pdf), revisado em 2015, tem **27 páginas** e uma coluna à direita, identificada como DBF. Um perfil de layout verificado visualmente com páginas 2 e 3 seleciona palavras inteiras da coluna (por coordenadas). Confere as três âncoras documentais ID_AGRAVO, DT_INVEST e ID_OCUPA_N. Nomes com acentos, espaços ou ambiguidades são **contados e não normalizados silenciosamente**; podem exigir transcrição manual.

ATENÇÃO: o próprio [Portal de Dados Abertos do SUS — Sinan/Dengue](https://dadosabertos.saude.gov.br/dataset/arboviroses-dengue) lista um recurso documental **Dicionário de dados - Dengue**, com **atualização indicada em 14/07/2025**. Uma versão em PDF [indicada pelo catálogo antigo do OpenDataSUS](https://opendatasus.saude.gov.br/dataset/4d5e5d44-58a8-4d67-b8aa-4ef1e4b00a1c/resource/ccc60f03-2834-49a3-98f7-7ee76f50a316/download/dic_dados_dengue.pdf) descreve campos comuns e de investigação e possui estrutura de tabela diferente. A extração abaixo **NÃO analisa esse PDF de 2025** e NÃO declara equivalência entre as duas edições. O identificador e edição exatos do documento associado à exportação anual seguem exigindo parecer da área técnica.

Códigos de campos documentais podem conter acentos ou caracteres que não são aceitos como nomes válidos de coluna CSV; essas diferenças não são corrigidas automaticamente. O perfil é somente da coluna DBF do documento de 2015 e não deve ser aplicado a outro PDF mediante renomeação do arquivo.

## Executar em Windows PowerShell 5.1

Use o clone da branch deste PR, sem mexer nos arquivos locais da análise anterior. Para uma instalação separada:

    cd "$env:USERPROFILE\Downloads"
    git clone --branch feat/offline-pdf-dbf-candidate-transcription --single-branch https://github.com/miscrapha-DELTA-IA/SINAN-MCP.git SINAN-MCP-Pdf-Auditoria
    cd .\SINAN-MCP-Pdf-Auditoria
    py -3.11 -m pip install -e ".[dev,pdfaudit,schemaaudit]"
    py -3.11 -m pytest -q tests/test_local_pdf_dictionary_candidate.py

Se já tiver uma cópia legítima do PDF e ZIP dentro do clone anterior SINAN-MCP-Auditoria, é preferível apontar os comandos abaixo diretamente aos caminhos daquele clone. **Não precisa baixar o ZIP novamente, copiá-lo, descompactá-lo nem anexá-lo ao GitHub.**

Gere um **novo** rascunho candidato, sem sobrescrever o anterior:

    py -3.11 -m sinan_mcp rascunhar-campos-dbf-pdf --resource-id 4cf2f7b8-9920-41b5-817a-1ffc13e0690c --pdf "$env:USERPROFILE\Downloads\SINAN-MCP-Auditoria\data\DIC_DADOS_ONLINE.pdf" --saida "$env:USERPROFILE\Downloads\SINAN-MCP-Auditoria\data\contrato-dengue-2024-dbf-candidato-v2015.json"

O programa devolve contagens de candidatos, ambiguidades e repetições. O JSON fica **apenas no computador do pesquisador**, com campos aceitos e páginas do PDF. Seu status é manual_nao_revisada, com cobertura excerto_parcial. Não há relatório que proclame dicionário validado para 2024.

Uma comparação opcional contra o ZIP local (sem copiar dados):

    py -3.11 -m sinan_mcp comparar-esquema-privado --resource-id 4cf2f7b8-9920-41b5-817a-1ffc13e0690c --zip "$env:USERPROFILE\Downloads\SINAN-MCP-Auditoria\data\DENGBR24.csv.zip" --pdf "$env:USERPROFILE\Downloads\SINAN-MCP-Auditoria\data\DIC_DADOS_ONLINE.pdf" --contrato "$env:USERPROFILE\Downloads\SINAN-MCP-Auditoria\data\contrato-dengue-2024-dbf-candidato-v2015.json" --parecer-pendente "$env:USERPROFILE\Downloads\SINAN-MCP-Auditoria\data\parecer-pendente-dengue-dbf-v2015.json"

É preciso usar um nome NOVO de parecer, pois a CLI impede sobrescrever o relatório existente. O ZIP é conferido localmente e só o cabeçalho é lido para comparação. Não há envio ou publicação de dados.

## Revisão antes de promover um contrato

1. Revisar cada campo candidato e página no PDF, identificando falsos positivos e campos não extraídos pela geometria
2. Confrontar **o dicionário de dengue indicado no catálogo de dados abertos em 2025**, incluindo campos gerais e alterações do formato de exportação, contra o de 2015
3. Verificar que a distribuição CSV de 2024 foi obtida da origem esperada, com versão e data de corte registradas; SHA-256 calculado localmente NÃO equivale a checksum oficial assinado
4. Registrar tipos, domínios, códigos inválidos, valores ignorados, variáveis condicionais e mudança de definição de caso, sempre em ambiente local autorizado e sem vazar valores
5. Encaminhar transcrição e divergências à revisão epidemiológica independente e à análise de privacidade, antes de qualquer habilitação de análise ou publicação real

O rascunho é uma conveniência de curadoria, **não atestado nem contrato validado**. A ferramenta não permite aprovar um release nem disponibilizar registros via MCP.

## Correção verificada de falso positivo na página 14

No relatório local do operador, a primeira extração de candidatos do PDF de 2015 indicou 87 campos, com 9 ausentes e 43 extras no CSV. A revisão visual do documento mostrou que o candidato `A` na página 14 é apenas texto narrativo da continuação do campo de bairro, e não um nome na coluna DBF. O código agora **exclui somente (`A`, página 14)** e conta exclusões revisadas no resumo de extração. Portanto, o documento anterior contém 86 candidatos realmente listados (78 observados e 8 ausentes) — a confirmação automática dessas contagens ainda exige executar a nova versão no PDF/ZIP locais.

Ver [revisão documental específica](DENG_2024_SCHEMA_DIVERGENCE_REVIEW.md). Não alterar documentos anteriores manualmente: gerar novos candidato e parecer em nomes diferentes para preservar rastreabilidade. A diferença entre o PDF de 2015 e o dicionário de dengue do portal atualizado em 2025 ainda precisa de revisão epidemiológica independente.
