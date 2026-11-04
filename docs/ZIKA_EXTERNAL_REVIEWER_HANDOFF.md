# Dossiê público de conferência externa — Dicionário Zika (P0)

Este procedimento produz, **sem ler arquivos privados ou clínicos**, um
roteiro Markdown para um **segundo conferente humano** revisar o
[dicionário específico Zika do MS](https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/dic_dados_zika.pdf).

A versão é gerada apenas a partir do
[`zika_pdf_37_fields_candidate.json`](../sinan_mcp/registry/zika_pdf_37_fields_candidate.json),
que continua sendo uma transcrição candidata. Contém 37 linhas de campos,
sete ressalvas e links diretos às páginas do PDF.
**Não** importa o checklist privado criado em etapas anteriores e não
transfere as notas manuscritas do operador.

## Gerar o roteiro em PowerShell 5.1

Atualize a branch no repositório e execute no seu computador:

```powershell
$destino = Join-Path $env:USERPROFILE "Documents\SINAN-MCP-Privado\ZIKA"
New-Item -ItemType Directory -Force -Path $destino | Out-Null
$roteiro = Join-Path $destino "dossie-revisor-externo-zika-37-campos.md"

py -3.11 -m sinan_mcp preparar-roteiro-revisor-zika --saida $roteiro
notepad $roteiro
```

Se esse caminho já existir, **não** sobrescreva: use um nome novo para
que o controle de versões manuais possa ser preservado. O arquivo é
Markdown textual, podendo ser revisado por terceiros em um editor de
texto ou em um editor Markdown institucional. Contém apenas dados
documentais públicos e **campos em branco**. O projeto não assina
nem verifica digitalmente arquivos produzidos por revisores.

## O que o revisor externo deve fazer

1. Abrir o PDF oficial e confirmar que a página 1–8 corresponde ao
   mesmo documento usado no catálogo, registrando versão/fonte e o hash
   local do PDF se aplicável (um hash local não substitui a
   autenticação junto ao publicador).
2. Verificar **cada uma das 37 linhas**, incluindo nome, posição,
   tipo, descrição, códigos, domínios e regras condicionais de
   preenchimento. O roteiro oferece uma coluna de decisão e outra
   para explicitar página e correção.
3. Examinar as sete ressalvas de forma separada, incluindo
   `NDUPLIC_N` (página 5), onde a coluna Categoria mostra uma linha
   sem o numeral esperado, enquanto a coluna Características menciona
   as categorias 1 e 2. Não inferir o código ausente sem evidência.
4. Formalizar, *fora do SINAN MCP*, eventuais divergências,
   correções, qualificação, independência e parecer assinado.
   A instituição responsável deve validar a autenticidade de um
   parecer recebido. Este programa não afirma recebimento, assinatura,
   conformidade ou aprovação.

## Limites e proveniência

A saída registra o SHA-256 **do catálogo versionado**. Esse
identificador é útil para conferir qual transcrição foi encaminhada,
mas **não é um hash oficial do PDF**.

Mesmo após revisão documental legítima, permanecem separados os
requisitos para demonstrar versão aplicável à exportação anual,
data de corte, identidade/autenticidade de JSON/Parquet, definição
epidemiológica, privacidade, autorização de processamento e parecer
científico. A simples marcação das caixas no Markdown **não altera**
o estado do banco, do MCP público, do checklist privado ou dos
10 tópicos científicos da matriz ZIKA/2024.

**Invariantes: 0 registros de ZIKABR24 lidos, 0 indicadores homologados,
nenhuma publicação autorizada, nenhuma assinatura autenticada.**

Arquivos de saída com respostas pessoais/pareceres assinados devem
ser tratados conforme as regras de privacidade institucionais; não
devem ser automaticamente adicionados ao GitHub nem anexados a
serviços públicos.
