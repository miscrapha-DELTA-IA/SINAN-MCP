# DENG/2024 — confronto privado de dicionários documentais

## Evidência PDF recebida em 03/11/2026

O pesquisador forneceu um documento nomeado dic_dados_dengue.pdf com **22 páginas** e identificação Ministério da Saúde / SVSA / DAENT / Sinan Online / DENGUE. Seus metadados indicam **criação em 22/03/2024** (título Word DIC_DADOS_DENGUE_fev20204).

**SHA-256 local desta cópia fornecida (não é checksum oficial assinado):**

    d15122f38b32c4b3caf58cca7e717065b24c888771ecad8e7a3ed02e0efd16a1

O [Portal de Dados Abertos do SUS](https://dadosabertos.saude.gov.br/dataset/arboviroses-dengue) lista um recurso "Dicionário de dados - Dengue" atualizado em **14/07/2025**; data de atualização no catálogo não é a data de criação/edição do PDF. A associação definitiva deste PDF ao ZIP anual de 2024 **não está provada**.

## Auditoria documental preliminar

A tabela de 7 colunas do PDF fornecido contém exatamente **121 entradas sequenciais (1 a 121), mas 120 nomes distintos**. Há duas inconsistências impressas:

| Seq | Página PDF | Nome | Verificação |
| --- | --- | --- | --- |
| 64 | 10 | coufinf | Nome repetido na sequência 67 |
| 67 | 11 | coufinf | Nome repetido na sequência 64 |
| 115 | 21 | complica | Tipo impresso char()1 |
| 116 | 21 | tp_sistema | Tipo impresso char()1 |

O PDF de 2024 inclui clinic_chik (Chikungunya); não contém os seguintes nomes DBF do PDF de 2015: DDD_HOSP, HOSPITAL, TEL_HOSP, CODISINF, CO_BAINF, NOBAIINF e DS_OBS. Isso é uma diferença de documentação, não comprovação de supressão, renomeação ou incompatibilidade do CSV. O contrato de 2015 já foi revisado para remover falso positivo A, página 14.

O operador observou previamente 121 cabeçalhos CSV e 86 candidatos do PDF 2015, com 78 correspondentes, 8 ausentes e 43 extras. **Nenhuma comparação nova entre PDF 2024 e CSV foi executada até agora**; as novas interseções são desconhecidas.

## Como executar o novo confronto local

Somente na branch de PR #9 e após instalação do pacote opcional:

    py -3.11 -m pip install -e ".[dev,pdfaudit,schemaaudit]"

Coloque o PDF **exato** com o hash acima na pasta data, mantenha o ZIP já baixado e o contrato privado anterior. Não copie nenhum deles ao GitHub. No PowerShell 5.1:

    cd "$env:USERPROFILE\Downloads\SINAN-MCP-Auditoria"

    py -3.11 -m sinan_mcp confrontar-dicionario-dengue-2024 `
      --pdf ".\data\dic_dados_dengue.pdf" `
      --contrato-2015 ".\data\contrato-dengue-2024-dbf-candidato-v2015-revisado.json" `
      --zip ".\data\DENGBR24.csv.zip" `
      --parecer-pendente ".\data\parecer-pendente-dengue-crosswalk-2024.json"

O programa consulta apenas: **texto do PDF**, **metadados do ZIP** e **primeira linha CSV (no máximo 128 KiB)**. Não lê registros de notificações. Não devolve nomes das colunas extras do CSV que não estejam listados no documento público; somente contagem. Relatório JSON privado criado exclusivamente em novo destino (sem sobrescrita), contendo hashes, nomes documentais divergentes, duplicações, tipos malformados e flags de validação, divulgação e uso **false**.

## Revisões exigidas antes de qualquer aprovação

1. Verificar a edição oficial do dicionário válida para esta extração CSV/2024 com evidência externa; SHA local não autentica a procedência dos bytes.
2. Conferir o campo coufinf duplicado, tipos char()1 e os 120 nomes únicos por página.
3. Cotejar as diferenças do documento 2015 (DBF) com a tabela 2024, testando apenas equivalências explícitas e revisadas.
4. Revisar definições, domínios, códigos de ignorado, transformação de exportação, data de corte e status preliminar/final.
5. Obter parecer epidemiológico independente e análise de privacidade. Nenhuma análise real, publicação nem abertura de microdados via MCP está autorizada.


## Conflito semântico significativo: campo classi_fin

A fonte de 22 páginas contém uma inconsistência epidemiológica ainda não explicada:
- **Página 12, seq. 70:** a célula Categoria de classi_fin enumera **1 Confirmado, 2 Descartado, 8 Inconclusivo**, além de códigos ignorados.
- **Página 13, seq. 73 e 77:** a descrição de clinic_chik condiciona a apresentação de chikungunya à classificação **13**, enquanto a regra de dengue com sinais de alarme condiciona a classificação a **11** ou **12**. O PDF DBF Sinan Online 2015 também adota classificações **10/11/12/13** na documentação, segundo versão do documento.
- Não há evidência, apenas com estes PDFs, de qual mapeamento foi efetivamente gravado no CSV rotulado 2024; não é lícito inferir equivalência, nem ajustar códigos por suposição.

Por isso a CLI do confronto registra uma **divergência semântica não conciliada** e define explicitamente `dominios_categoricos_verificados: false`, sem liberação de indicador. A correspondência de nomes do cabeçalho NÃO resolve esse bloqueio. É necessário consultar a área técnica para a edição e domínio válidos e revisar conjuntamente com um epidemiologista.


## Primeira execução local com o CSV 2024

Em 03/11/2026, o pesquisador executou o comando administrativo `confrontar-dicionario-dengue-2024` com PDF documental de 22 páginas, contrato candidato DBF 2015 e arquivo `DENGBR24.csv.zip` local. Saída exclusivamente agregada/metadados, informada pelo operador:

- Documento PDF: **121 entradas** e **120 nomes distintos** (`coufinf` consta duas vezes, seq. 64 e 67).
- CSV anual: **121 nomes observados no cabeçalho**; leitura apenas da primeira linha CSV, sem registros individuais.
- PDF ∩ CSV: **119 nomes iguais** (comparação nominal, normalização somente da caixa).
- PDF − CSV: **1 nome documentado ausente** (nome exato permanece em parecer privado local).
- CSV − PDF: **2 nomes adicionais** (não listados nem transmitidos; requerem revisão local de confidencialidade e proveniência).
- Parecer independente: **PENDENTE**, aprovação clínica/semântica, privacidade, qualidade e publicação **não concedidas**.

O número de entradas PDF igual ao número de colunas CSV **não** representa igualdade dos esquemas: há uma duplicação documental e três diferenças no conjunto de nomes (1 + 2). A taxa nominal 119/120 ≈ 99,2% é limitada aos nomes de campos, sem validação de valores ou tipos. O nome **documentado pelo PDF** que falta no CSV está armazenado no JSON privado em `nomes_pdf_atual_ausentes_csv`, seguro para consultar localmente. Os dois nomes presentes apenas no CSV são deliberadamente omitidos pelo software; não devem ser acrescentados automaticamente ao dicionário nem enviados ao GitHub.

O PDF anexado pelo operador apresentou SHA-256 local `d15122f38b32c4b3caf58cca7e717065b24c888771ecad8e7a3ed02e0efd16a1`, e metadados internos de criação em 22/03/2024. Esses metadados não autenticam o documento oficialmente. O aviso `pymupdf_layout` é somente sugestão opcional, não falha de extração neste confronto.

### Encaminhamento pontual

1. Obter **somente** a entrada documental ausente: `(Get-Content .\data\parecer-pendente-dengue-crosswalk-2024.json -Raw | ConvertFrom-Json).nomes_pdf_atual_ausentes_csv`. O nome consta no PDF público; não precisa ler nem enviar o ZIP.
2. Revisar, **somente no computador do pesquisador**, os dois nomes adicionais antes de qualquer divulgação. Verificar se são metadados válidos da exportação, campos de processamento, diferenças de layout ou material não destinado ao público.
3. Revisar domínios, classificações (especialmente `classi_fin` e códigos 1/2/8 contra 11/12/13), duplicação `coufinf`, `char()1` nas seq. 115/116 e a versão documental efetivamente utilizada para 2024.
4. Preservar parecer privado, hashes e datas, solicitar avaliação epidemiológica e de privacidade independentes. Não publicar nem usar para calcular indicadores reais até os gates serem satisfeitos.
