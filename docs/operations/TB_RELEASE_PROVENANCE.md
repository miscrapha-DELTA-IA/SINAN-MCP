# Proveniência SINAN-TB — piloto 2024 e candidato 2019

**Estado: descoberta de metadados. Nenhuma fonte real homologada ou aprovada para publicação.**

O piloto TUBE/2024 da PR #71 fixa o SHA-256 de um Parquet do espelho PySUS. O hash identifica esse Parquet, mas não comprova sua equivalência ao arquivo DBC do DATASUS. Na CLI atual, a opção de status final é uma declaração do operador, não uma verificação de origem.

## Evidência e hipótese de trabalho

- Fonte primária: [DATASUS, dados sobre agravos](https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/svsa/agravos-de-notificacoes/agravos-de-notificacoes). Diretórios de interesse: /dissemin/publicos/SINAN/DADOS/FINAIS e /dissemin/publicos/SINAN/DADOS/PRELIM.
- Catálogos de descoberta independentes: [ALPACA](https://quantilica.com/alpaca/dados/sinan-tube?page=1) e [CIDACS PDD](https://pdd.cidacs.org/bases?page=2), consultados em 2026-11-18. Ambos listam TUBEBR19.dbc em FINAIS e TUBEBR24.dbc em PRELIM. Catálogos terceiros não substituem conferência com a origem.
- Candidato à conferência final: **2019**. Piloto privado, ainda não homologado: **2024**.

## Etapa 1 — descoberta sem baixar dados

Na raiz do repositório, em ambiente local:

    python -m scripts.auditar_edicao_tb --anos 2019 2024

O script consulta somente nomes, tamanhos e datas de modificação do FTP oficial. Não baixa microdados, não cria SQLite e não altera a configuração MCP. Sem resposta, marca desconhecido; se o mesmo nome aparecer nas duas pastas, marca duplicidade. A descoberta nunca marca status_final_homologado nem publicacao_autorizada como verdadeiros.

### Resultado de observação direta do FTP (2026-11-18)

Na execução local Windows (PowerShell 5.1), `python -m scripts.auditar_edicao_tb --anos 2019 2024` retornou:

| Arquivo | Diretório observado | SIZE (bytes) | MDTM reportado pelo FTP |
| --- | --- | ---: | --- |
| `TUBEBR19.dbc` | `FINAIS` | 5.289.464 | `20251015195757` |
| `TUBEBR24.dbc` | `PRELIM` | 6.118.830 | `20260507190800` |

Nenhuma das consultas retornou erros. Estes valores provêm da saída de terminal do operador; são **metadados observados**, não um checksum oficial, validação do conteúdo, ou endosso de publicação.

### Etapa 1B — captura local restrita do DBC de 2019

Após atualizar a branch de auditoria, execute **na raiz do repositório**:

```powershell
git pull --ff-only
py -3.11 -m scripts.capturar_tb2019
```

O comando acessa somente `TUBEBR19.dbc` em `FINAIS`. Exige que **diretório, tamanho e MDTM** coincidam com a observação acima. A transferência binária é limitada a 20 MiB; se incompleta, é descartada. O destino é `data/private/tb2019/TUBEBR19.dbc`, ignorado pelo Git, e o manifesto de proveniência fica em `data/private/tb2019/TUBEBR19.manifest.json`. **Não envie o DBC nem o manifesto para o GitHub, ChatGPT, Drive ou hospedagem pública.** Caso execute novamente, o comando não sobrescreve a cópia existente.

**Limite de autenticidade:** o FTP oficial usa conexão sem TLS; o SHA-256 calculado localmente fixa os bytes recebidos, mas não comprova criptograficamente a identidade da origem ou a veracidade clínica. Ainda será necessário localizar a evidência documental independente, comparar o conteúdo convertido com o Parquet PySUS e obter revisão externa. O script **nunca** habilita `--status final`, edição da base pública ou publicação MCP.

## Etapa 2 — equivalência reprodutível, exclusivamente local

1. Transferir o DBC do endereço oficial exato, registrar data/hora UTC, tamanho, hash SHA-256 calculado sobre bytes recebidos, origem e versão. Manter arquivo fora do Git e do servidor público.
2. Fixar URL, tamanho e SHA-256 do Parquet PySUS, versão do pacote, data de consulta e detalhes da transformação. Não comparar diretamente o checksum do DBC com o do Parquet: são formatos distintos.
3. Comparar esquema, linhas totais, nulos, normalização dos tipos, categorias e **multiconjunto integral de linhas canônicas** de ID_MN_RESI, CS_SEXO, CS_RACA e SITUA_ENCE, incluindo multiplicidades. Agregados iguais não demonstram equivalência registro a registro.
4. Conferir o dicionário oficial aplicável, o significado do ano do arquivo, o critério de coorte, a unidade observacional, possíveis duplicatas e as codificações de encerramento. O indicador exploratório de abandono não corresponde automaticamente ao oficial.

Se o DBC oficial estiver inacessível ou qualquer etapa falhar, manter versão **desconhecida** e recusar a homologação. Nunca usar --status final para contornar a ausência de evidências.

### Etapa 2A — descobrir versão PySUS de 2019, sem baixar registros

O arquivo DBC local capturado em 2026-11-18 apresentou SHA-256
`7a00e29a5a309b794e21f1a650d3b04b9d3cb05fcc6ef8c9feefab3a961c9144`,
tamanho `5289464` bytes e manifesto local registrado. O hash é calculado pelo operador a partir dos bytes FTP recebidos e **não** constitui checksum oficial autenticado.

Na raiz do repositório Windows, use o Python isolado:

```powershell
git pull --ff-only
if (!(Test-Path .venv\Scripts\python.exe)) { py -3.11 -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -e ".[ingest]" "pyreaddbc==2.0.4"
.\.venv\Scripts\python.exe -m scripts.avaliar_equivalencia_tb2019 --etapa planejar
```

A consulta de planejamento só obtém metadados do catálogo PySUS, sem baixar Parquet ou enviar dados do DBC. Exige exatamente uma entrada `TUBEBR19.parquet` em `TUBE/2019` e SHA-256 de catálogo disponível. Se o catálogo estiver indisponível, a etapa falha conservadoramente e o status continua desconhecido.

### Etapa 2B — comparação local das quatro colunas do piloto

Execute somente após conferir o planejamento anterior:

```powershell
.\.venv\Scripts\python.exe -m scripts.avaliar_equivalencia_tb2019 --etapa comparar
```

O procedimento valida novamente o hash fixado do DBC e o manifesto. Baixa **somente** o Parquet listado no catálogo para um diretório temporário privado, exige SHA-256 e tamanho exatos, extrai do DBC as quatro colunas do piloto usando `pyreaddbc` em subprocesso isolado e compara, sem divulgar categorias, o multiconjunto das tuplas `(ID_MN_RESI, CS_SEXO, CS_RACA, SITUA_ENCE)` com todas as multiplicidades. Os artefatos temporários (Parquet, projeção DBC, tabela de comparação SQLite) são apagados ao término.

Se o campo `multiconjunto_4_campos_igual` resultar `true`, isso prova **apenas a concordância da projeção de quatro campos sob a normalização descrita no código**, não equivalência integral do arquivo, completude, legitimidade epidemiológica, nem autorização de divulgação. Se resultar `false`, nenhuma fonte é homologada e será necessária auditoria privada de layout, codificação e versões.

Mesmo quando a comparação for bem-sucedida, os campos `equivalencia_integral_verificada`, `status_final_homologado` e `publicacao_autorizada` permanecerão `false`. O código do servidor MCP público e o túnel são preservados.

## Etapa 3 — gate de publicação

- Parecer científico independente sobre método, coorte, dicionário, contagem e versão.
- Parecer de privacidade sobre células pequenas, inferência por diferenças, versões e cruzamentos entre tabelas.
- Parecer institucional/jurídico aplicável e autorização específica de divulgação.
- Pacote aprovado, pré-agregado e com hashes fixados, **sem qualquer acesso do MCP público aos registros reais**. Antes disso, endurecer aggregate_contract.py para exigir evidência verificável de origem além de status_informado.

**O Render público e a demonstração ChatGPT permanecem 100% sintéticos; todos os arquivos reais e seus candidatos ficam locais.**
