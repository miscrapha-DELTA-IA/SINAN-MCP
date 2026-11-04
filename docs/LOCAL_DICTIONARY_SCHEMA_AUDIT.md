# Auditoria local: campos do dicionário x esquema do arquivo anual

## Escopo de evidência e segurança

Esta PoC compara os nomes de campos de arquivos ZIP CSV/JSON já obtidos legitimamente e mantidos localmente com uma transcrição manual do PDF de dicionário de dados. Nenhum arquivo de paciente é baixado, enviado ao GitHub, disponibilizado no MCP ou incorporado à base SQLite.

O índice oficial possui, até esta etapa, recursos DENG/2024 (CSV e JSON) e CHIK/2024 (JSON); TUBE/2024 ainda não tem ID anual identificado com o mesmo grau de evidência.

Documentos primários consultados:

- [Sinan Online Dengue/Chikungunya, versão 3.0](https://portalsinan.saude.gov.br/images/documentos/Agravos/Dengue/DIC_DADOS_ONLINE.pdf) — página 2 do PDF (contagem a partir de 1): exemplos de identificadores DBF ID_AGRAVO, DT_INVEST e ID_OCUPA_N
- [Sinan NET Tuberculose, versão 5.0](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_NET_Tuberculose_23_07_2020.pdf) — referência documental, não comprovada para arquivo TUBE 2024

Esses três campos DBF servem apenas como exemplo PARCIAL do PDF antigo. Não representam toda a estrutura de 2024 e sua compatibilidade com arquivos de 2024 NÃO foi demonstrada.

## Arquitetura

- Arquivo: sinan_mcp/local_schema_review.py — execução administrativa e offline
- Contrato JSON manual: versão sinan-local-dictionary-structure-candidate-v1; vincula UUID de recurso do portal, versão/documento, SHA-256 observado do PDF, formato, layout, colunas e páginas do PDF
- Comparação: campos esperados presentes/ausentes, contagem de campos extras SEM imprimir nomes desconhecidos, referência anual, hashes locais e estado de revisão
- Revisão: pacote JSON privado com 10 pendências, sem assinatura ou liberação, criado sem sobrescrever arquivo anterior
- Nenhuma nova tool MCP pública com acesso a arquivos; nenhuma alteração na ingestão PySUS/CSV de dados reais

### Quais dados são lidos

CSV compactado: somente primeira linha/cabeçalho até 128 KiB. Não lê valores de notificações.

JSON compactado: se o extra opcional ijson estiver instalado, o programa faz streaming de no máximo 64 registros e consome no máximo 16 MiB descompactados durante a amostragem. Os valores desses registros passam TRANSITORIAMENTE pelo parser, mas não são gravados em relatórios, agregados ou logs. Não é inspeção integral do JSON. Suporta array_of_objects e ndjson declarados; estruturas aninhadas são assinaladas para revisão. Os tipos e categorias epidemiológicas NÃO são inferidos.

Antes da leitura, a estrutura do ZIP, nome de membro, SHA-256 local, número de arquivos e razão máxima de compressão são verificados. O processo não extrai conteúdo em disco. Um ZIP forjado pode passar nessa validação estrutural: autenticidade de origem, checksum oficial, edição exata e status preliminar/final continuam desconhecidos.

## Execução no Windows PowerShell 5.1

No clone desta branch:

    py -3.11 -m pip install -e ".[dev,schemaaudit]"
    py -3.11 -m pytest -q tests/test_local_schema_review.py

Primeiro, salve legitimamente o PDF do dicionário em um diretório privado do seu computador. Para o exemplo DENG CSV, ele deve ter o nome DIC_DADOS_ONLINE.pdf, igual ao documento curado.

    py -3.11 -m sinan_mcp preparar-modelo-esquema --resource-id 4cf2f7b8-9920-41b5-817a-1ffc13e0690c --pdf .\data\DIC_DADOS_ONLINE.pdf --saida .\data\contrato-dengue-2024-local.json

O programa gera um arquivo JSON NOVO, não sobrescrevendo o anterior, com apenas três identificadores demonstrativos da página 2. O candidato é local e explicitamente não revisado. Edite-o localmente para registrar campos, páginas e formato/encoding observados. Use cobertura excerto_parcial enquanto não houver uma transcrição completa independente.

Para comparar um ZIP obtido no ambiente privado:

    py -3.11 -m sinan_mcp comparar-esquema-privado --resource-id 4cf2f7b8-9920-41b5-817a-1ffc13e0690c --zip .\data\DENGBR24.csv.zip --pdf .\data\DIC_DADOS_ONLINE.pdf --contrato .\data\contrato-dengue-2024-local.json --parecer-pendente .\data\parecer-pendente-dengue.json

O comando mostra apenas estado e contagens; o relatório completo é salvo exclusivamente no caminho privado indicado, com criação exclusiva e permissões restritas quando suportadas pelo sistema operacional. Nenhum conteúdo clínico é enviado a um LLM. Evite armazenar arquivos ou pareceres em pastas monitoradas/publicadas automaticamente.

Para JSON DENG e CHIK, o contrato exige indicar explicitamente array_of_objects ou ndjson conforme o layout real. Não adivinhar nem aceitar silenciosamente formatos diferentes. O plugin ijson é opcional e instalado apenas para verificação JSON.

## Atualização ZIKA/2024 — não reutilizar campos de Dengue

O gerador de modelo agora usa **nove exemplos próprios do PDF Zika**
quando recebe o UUID `264978ca-f795-4940-b5d3-ebc21e7d1c7c`.
Os 37 campos numerados no documento não foram transcritos integralmente.
O candidato usa `json_layout=nao_determinado`. Mesmo que o campo
seja editado para um layout específico, o comparador ainda bloqueia
**qualquer confronto com ZIKABR24**, independentemente do conteúdo do ZIP,
até autorização institucional e revisão independente.
Para `41bfda2a-5826-4ef9-8913-497247e6c9ce` (Parquet), o gerador
e o validador recusam a operação porque o formato não é suportado.

Consulte [preparação documental ZIKA sem leitura de arquivos de casos](ZIKA_2024_SCHEMA_TEMPLATE_SAFE_PREPARATION.md).
A comparação real com ZIP de pacientes segue sem autorização nesta etapa.

## Leitura científica do relatório

- Se um campo do trecho transcrito estiver ausente, há divergência de esquema para revisão.
- Em contrato parcial, campos não transcritos são contados, mas não assumidos como incompatibilidades; uma lista curta não representa todo o dicionário.
- Em transcrição declarada completa, campos não documentados geram divergência.
- Um resultado sem divergências significa somente compatibilidade de nomes observados dentro da cobertura declarada, NÃO validação anual, autenticidade, domínios, dados, deduplicação, coorte, incidência ou risco.

O pacote de revisão deixa pendentes identidade/origem da distribuição, hash institucional, edição do dicionário aplicável, transcrição completa, tipos e domínios, datas de corte, consistência, coorte, parecer independente e privacidade cumulativa. Um operador NÃO pode aprovar dados ou publicar resultados alterando esse JSON.

## Critérios que precisam ser atendidos antes de qualquer análise real

1. Verificar o arquivo de 2024 e sua edição/data de corte, com origem autenticada e documentação de eventuais atualizações retroativas
2. Confirmar a edição do dicionário efetivamente aplicada à exportação CSV/JSON para aquele recurso
3. Transcrever nomes, domínios, tipos e regras de transformação de maneira completa, com revisão por especialistas
4. Medir integridade, cobertura, duplicidade e diferenças entre sistemas/anos, sem presumir indivíduo único por notificação
5. Obter revisão epidemiológica, análise institucional de privacidade, controles de composição entre releases e autorização separada para divulgação

Não mesclar nem publicar qualquer candidata com base apenas nesta auditoria estrutural.
