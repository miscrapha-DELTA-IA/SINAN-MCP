# ZIKA/2024 — modelo privado de esquema, somente documentação

**Objetivo restrito:** preparar um candidato JSON de **nove campos
documentais visivelmente conferidos** nas oito páginas do
[dicionário específico Zika do Ministério da Saúde](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus/resource/58038262-c745-46ea-979b-8727eb08ec5c).
O PDF possui 37 campos numerados, mas **nove exemplos não constituem
uma transcrição integral**, e nenhuma compatibilidade com a distribuição
ZIKABR24 foi verificada. Nenhum registro de paciente é necessário.

**Transcrição documental posterior:** o catálogo
[`ZIKA_PDF_37_FIELDS_DOCUMENTARY_TRANSCRIPTION.md`](ZIKA_PDF_37_FIELDS_DOCUMENTARY_TRANSCRIPTION.md)
agora contém uma proposta de transcrição dos **37 identificadores**
visíveis no PDF, com tipos, páginas, domínios descritos e sete
ressalvas documentais pendentes. **Ela não modifica automaticamente
o contrato privado anterior**, que permanece como excerto de nove
campos até revisão independente. Nenhum dado de ZIKABR24 foi lido.

## O que foi implementado

O comando administrativo existente `preparar-modelo-esquema` agora
seleciona campos por agravo. Para o recurso oficial
`264978ca-f795-4940-b5d3-ebc21e7d1c7c` (ZIKA/2024, JSON), ele usa
nove identificadores e as páginas 1 a 8 do PDF de Zika,
não os três exemplos de Dengue/Chikungunya antes reutilizados.
A saída permanece `cobertura=excerto_parcial`,
`situacao_transcricao=manual_nao_revisada` e sem autorização.

**A estrutura do JSON ZIKABR24 é desconhecida**: por isso o
novo modelo usa `json_layout=nao_determinado`. O comparador privado
recusa o acesso ao ZIP enquanto o layout for indeterminado **e também
o recusa se alguém alterar manualmente o campo para `array_of_objects`
ou `ndjson`**: ZIKABR24 permanece expressamente bloqueado até haver
revisão independente de proveniência, edição, corte, privacidade e
autorização institucional. A edição do candidato **não desbloqueia
leitura de registros reais**.

O recurso ZIKA/2024 **Parquet**
`41bfda2a-5826-4ef9-8913-497247e6c9ce`
é **rejeitado** pelo comparador atual. Não é tratado como JSON.
Será necessário um caminho independente de metadados Parquet,
auditado e privado, antes de analisar seus campos.

## Como preparar somente o modelo documental no Windows

O PDF é **público**, mas o contrato de trabalho deve ficar em
diretório local privado e não ser enviado ao GitHub, ao MCP público
ou a chats. O PDF pode ser obtido pela
[página do recurso](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus/resource/58038262-c745-46ea-979b-8727eb08ec5c)
e deve se chamar literalmente `dic_dados_zika.pdf`.

```powershell
$privado = Join-Path $env:USERPROFILE "Documents\SINAN-MCP-Privado\ZIKA"
New-Item -ItemType Directory -Force -Path $privado | Out-Null

# Salve manualmente o PDF oficial nesta pasta com esse nome.
$pdf = Join-Path $privado "dic_dados_zika.pdf"
$contrato = Join-Path $privado "zika-2024-candidato-privado.json"

py -3.11 -m sinan_mcp preparar-modelo-esquema `
    --resource-id 264978ca-f795-4940-b5d3-ebc21e7d1c7c `
    --pdf $pdf `
    --saida $contrato
```

O comando faz apenas hash SHA-256 **local** do PDF e grava um novo
candidato JSON. **Esse hash não autentica os bytes do Ministério**,
e nomes/URLs iguais não impedem falsificações. O arquivo de saída
não pode ser sobrescrito automaticamente.

Confira nele:
- `agravo=ZIKA`, `format=JSON`
- `cobertura=excerto_parcial`
- `json_layout=nao_determinado`
- `campos_dbf` contém somente nove exemplos citados nas páginas
- `situacao_transcricao=manual_nao_revisada`

O modelo pode ser revisado em privado por pesquisadores e responsáveis
pela gestão dos dados. **Não execute agora `comparar-esquema-privado`
com ZIKABR24 real**: mesmo em JSON, a implementação existente
pode ler valores transitoriamente de até 64 registros. Primeiro são
necessárias autorização para o processamento, revisão de privacidade,
confronto de versões e mecanismo que inspecione apenas metadados
sem abrir linhas clínicas.

## Critérios pendentes

Continuam os dez tópicos da matriz ZIKA/2024:
identidade, sistema de origem, instrumento, campos comuns,
campos próprios, semântica de casos, temporalidade, qualidade,
privacidade e revisão independente. **Zero** indicadores homologados,
zero leitura real neste PR e nenhuma autorização de publicação.
