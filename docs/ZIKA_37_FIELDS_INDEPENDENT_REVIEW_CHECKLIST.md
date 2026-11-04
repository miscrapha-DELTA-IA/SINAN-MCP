# Revisão independente da transcrição do dicionário Zika — pacote privado P0

## Objetivo e limites

O SINAN MCP possui um inventário **documental candidato** de **37 campos
numerados nas oito páginas** do dicionário público
[Sinan Net — Zika, PDF ministerial](https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/dic_dados_zika.pdf).
Este roteiro permite registrar uma conferência humana campo a campo,
sem fingir que o software identifica, autentica ou substitui um
revisor independente.

A fonte primária também está disponível na
[página de recurso do Ministério da Saúde](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus/resource/58038262-c745-46ea-979b-8727eb08ec5c).
A transcrição é documentada na
[tabela de 37 campos](ZIKA_PDF_37_FIELDS_DOCUMENTARY_TRANSCRIPTION.md).

**Não é uma auditoria do esquema de `ZIKABR24`:** nenhuma coluna,
linha clínica, valor de notificação, data de corte ou identidade de
release anual é lida. Um parecer documental de um PDF não comprova
que seus campos, regras e códigos correspondem às distribuições
JSON ou Parquet de 2024.

## Fluxo offline no PowerShell 5.1

Use uma pasta **privada fora do checkout Git**, preferencialmente em
um diretório institucional autorizado, sem sincronização automática
para repositórios públicos:

```powershell
cd "$env:USERPROFILE\Downloads\SINAN-MCP-ZIKA-2024"

$privado = Join-Path $env:USERPROFILE "Documents\SINAN-MCP-Privado\ZIKA"
New-Item -ItemType Directory -Force -Path $privado | Out-Null

$pacote = Join-Path $privado "revisao-documental-zika-37-campos.json"

py -3.11 -m sinan_mcp preparar-revisao-documental-zika --saida $pacote
py -3.11 -m sinan_mcp diagnosticar-revisao-documental-zika --arquivo $pacote
```

A geração cria arquivo **novo**, sem sobrescrever, com controles
de permissão do usuário quando o sistema operacional oferece suporte.
Se já existir um `revisao-documental-zika-37-campos.json`,
não tente recriá-lo: preserve a versão preenchida ou escolha outro nome.

## Estrutura e preenchimento humano

O JSON privado contém:

- **37 entradas de campos** na ordem do PDF, com `seq`,
  `campo`, `pagina_pdf`, `tipo_documental`,
  `dominio_descritor`, `codigos_citados` e
  `significado_resumido`; esses campos de fonte são imutáveis.
- **7 ressalvas documentais** inicialmente pendentes, sem apagar
  as interpretações conflitantes ou ilegíveis.
- `avaliacao_declarada_operador` em cada campo:
  `PENDENTE`, `CONFERIDO_MANUALMENTE`,
  `DIVERGENCIA_DOCUMENTAL` ou `ILEGIVEL`.
- Para as sete ressalvas: `PENDENTE`,
  `OBSERVACAO_DOCUMENTADA` ou `DIVERGENCIA_IDENTIFICADA`.
- `nota_documental` local, até 600 caracteres, para registrar
  referência à página, dúvida ou justificativa. Divergência,
  ilegibilidade e observação de ressalva exigem nota não vazia.

**O operador pode preencher essas avaliações localmente** após examinar
o PDF. Mas o sistema as conta apenas como **declarações**, não
verificação de qualificação, identidade, assinatura ou aprovação
institucional. O comando de diagnóstico mostra somente contagens,
não mostra nomes de pacientes nem imprime notas privadas.

Exemplo de avaliação válida, editando manualmente uma entrada
*existente* do arquivo privado:

```json
{
  "avaliacao_declarada_operador": "DIVERGENCIA_DOCUMENTAL",
  "nota_documental": "Verificar na pagina 5 a legibilidade dos codigos de NDUPLIC_N."
}
```

**Não substitua a entrada inteira por esse exemplo**: preserve as
outras chaves originais; o validador recusa qualquer mudança na fonte.

Mesmo que todos os 37 campos recebam
`CONFERIDO_MANUALMENTE`, a saída é sempre:

```text
Parecer independente autenticado: NAO
Campos de ZIKABR24 lidos: 0
Topicos cientificos pendentes: 10
Indicadores homologados: 0; publicacao autorizada: NAO
```

## Critérios para revisão externa efetiva

Um especialista externo ao trabalho de transcrição deverá conferir
cada linha contra a página do PDF, registrar dúvidas, distinguir
códigos visíveis de valores de domínio exaustivos e decidir se a
divergência requer uma errata documental. Especialmente:

- `NU_IDADE_N`: unidade de tempo codificada; não converter
  automaticamente em anos.
- `NDUPLIC_N`: célula ambígua no PDF; não inferir códigos nem
  regras de deduplicação.
- `IN_VINCULA`: tipo `char(6)` e categorias visíveis 0/1;
  não corrigir a largura por intuição.
- `CS_ESCOL_N`: codificações heterogêneas e categorias ignoradas;
  evitar esquema simplificado.
- `ID_RG_RESI`: possível divergência entre a descrição da
  regional de residência e a referência textual à notificação.
- `TP_SISTEMA`: domínio histórico não autentica o sistema de
  origem de cada registro do arquivo anual.
- `CLASSI_FIN`: classificação no dicionário não substitui
  definição epidemiológica de caso e edição da vigilância.

A instituição deverá arquivar **separadamente** a identidade e
qualificação do avaliador, versão e hash do PDF que efetivamente
conferiu, data, declaração de independência, correções, divergências,
eventuais pareceres assinados e decisão institucional sobre o uso
científico. **Este projeto não cria nem verifica assinatura digital,
não autentica parecer e não disponibiliza opção de aprovação**.

Os artefatos privados, que podem conter notas sensíveis, **não devem
ser enviados ao GitHub público, ao servidor MCP, a chats ou ao banco
de dados clínico**.

## Invariantes verificáveis

As chaves de controle não podem ser alteradas manualmente para
`true` nem para valores de aprovação. O validador compara
identificadores, ordem, tipos, páginas, domínios e ressalvas com a
versão imutável da transcrição pública. Recusa chaves JSON duplicadas,
estrutura adulterada, assinatura/parecer falsamente aprovado,
mudança no fingerprint local do catálogo e tentativa de usar o
relatório para liberar `ZIKABR24`.

O SHA-256 do catálogo versionado identifica o texto local que foi
revisado; **não é um hash oficial autenticado do PDF**. O código
continua sem ler arquivo anual. Não há etapa automática para
converter esse checklist em homologação científica.

**Status final esperado: `CHECKLIST_OPERADOR_SEM_PARECER_INDEPENDENTE`.**

## Dossiê de conferência externa separado do checklist privado

O comando `preparar-roteiro-revisor-zika --saida roteiro.md`
gera um roteiro Markdown *a partir de metadados documentais públicos*,
com 37 linhas, sete ressalvas e links para as páginas do PDF. Ele não
lê as notas do checklist privado, nem marca campos como conferidos.
Veja o [fluxo de entrega a avaliador externo](ZIKA_EXTERNAL_REVIEWER_HANDOFF.md).

## Registro de observações pelo PowerShell (sem editar JSON)

Após abrir o [PDF ministerial](https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SINAN/Zikavirus/dic_dados_zika.pdf)
e conferir **de fato** a linha correspondente, é possível registrar
uma declaração documental individual no checklist privado. **Não execute
um exemplo com status `CONFERIDO_MANUALMENTE` sem realizar a conferência.**

A ferramenta cria uma **nova versão** na mesma pasta privada,
preserva integralmente o arquivo original e recusa sobrescrita,
mudanças no catálogo e autenticação de parecer. Exemplo de registro
honesto de campo ainda pendente, **sem alegar que foi conferido**:

```powershell
$privado = Join-Path $env:USERPROFILE "Documents\SINAN-MCP-Privado\ZIKA"
$origem = Join-Path $privado "revisao-documental-zika-37-campos.json"
$nova = Join-Path $privado "revisao-documental-zika-v2.json"

py -3.11 -m sinan_mcp registrar-observacao-revisao-zika `
  --arquivo $origem --saida $nova `
  --tipo campo --campo nduplic_n `
  --avaliacao PENDENTE `
  --nota "Aguardando segunda leitura da categoria na pagina 5"

py -3.11 -m sinan_mcp diagnosticar-revisao-documental-zika --arquivo $nova
```

**Observação:** marcar `PENDENTE` não reduz a contagem de pendências;
isto é esperado. Somente após inspeção humana real, um operador poderá
declarar `CONFERIDO_MANUALMENTE`, `DIVERGENCIA_DOCUMENTAL` ou
`ILEGIVEL` para um campo; divergência ou ilegibilidade exige nota.
Para registrar uma das **sete ressalvas**, use
`--tipo ressalva --campo nduplic_n` com
`--avaliacao OBSERVACAO_DOCUMENTADA` ou
`DIVERGENCIA_IDENTIFICADA`, sempre com justificativa.
Os comandos aceitam a opção `PENDENTE` para manter assuntos abertos.

A saída é apenas uma contagem de declarações do operador; **não**
é parecer independente autenticado. O programa não confirma que
o PDF foi realmente aberto. Não copie as notas privadas para
issues, pull requests, chats ou servidor MCP.

Se `revisao-documental-zika-v2.json` já existir, escolha outro
nome de saída; o comando nunca sobrescreve versões anteriores.
