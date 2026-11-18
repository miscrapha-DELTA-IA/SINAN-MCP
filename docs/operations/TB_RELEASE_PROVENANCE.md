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

## Etapa 2 — equivalência reprodutível, exclusivamente local

1. Transferir o DBC do endereço oficial exato, registrar data/hora UTC, tamanho, hash SHA-256 calculado sobre bytes recebidos, origem e versão. Manter arquivo fora do Git e do servidor público.
2. Fixar URL, tamanho e SHA-256 do Parquet PySUS, versão do pacote, data de consulta e detalhes da transformação. Não comparar diretamente o checksum do DBC com o do Parquet: são formatos distintos.
3. Comparar esquema, linhas totais, nulos, normalização dos tipos, categorias e **multiconjunto integral de linhas canônicas** de ID_MN_RESI, CS_SEXO, CS_RACA e SITUA_ENCE, incluindo multiplicidades. Agregados iguais não demonstram equivalência registro a registro.
4. Conferir o dicionário oficial aplicável, o significado do ano do arquivo, o critério de coorte, a unidade observacional, possíveis duplicatas e as codificações de encerramento. O indicador exploratório de abandono não corresponde automaticamente ao oficial.

Se o DBC oficial estiver inacessível ou qualquer etapa falhar, manter versão **desconhecida** e recusar a homologação. Nunca usar --status final para contornar a ausência de evidências.

## Etapa 3 — gate de publicação

- Parecer científico independente sobre método, coorte, dicionário, contagem e versão.
- Parecer de privacidade sobre células pequenas, inferência por diferenças, versões e cruzamentos entre tabelas.
- Parecer institucional/jurídico aplicável e autorização específica de divulgação.
- Pacote aprovado, pré-agregado e com hashes fixados, **sem qualquer acesso do MCP público aos registros reais**. Antes disso, endurecer aggregate_contract.py para exigir evidência verificável de origem além de status_informado.

**O Render público e a demonstração ChatGPT permanecem 100% sintéticos; todos os arquivos reais e seus candidatos ficam locais.**
