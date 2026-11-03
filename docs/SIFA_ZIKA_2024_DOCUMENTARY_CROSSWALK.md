# P0 — Matriz documental SIFA/ZIKA para o ano de arquivo 2024

**Status: plano reprodutível, sem leitura ou confronto de arquivos clínicos.**

## Achado documental: SIFA

No [Guia de Vigilância em Saúde, volume 2, 6ª edição revisada
(Ministério da Saúde, 2024), página impressa 506](https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/svsa/vigilancia/guia-de-vigilancia-em-saude-volume-2-6a-edicao),
a notificação de **sífilis adquirida em adultos** é associada à
**Ficha de Notificação/Conclusão** do SINAN. A
[Nota Informativa nº 2/2017, seção 2.2](https://portalsinan.saude.gov.br/images/documentos/Agravos/Sifilis-Ges/Nota_Informativa_Sifilis.pdf)
menciona a Ficha de Notificação Individual. Essas orientações documentam
o **instrumento de notificação**, **não** a identidade, o layout do arquivo
de disseminação de 2024, a aplicação do PDF NET 5.0 revisado em 2018,
o preenchimento das variáveis ou a definição operacional de um indicador.

A sífilis adquirida (alias interno **SIFA**) é distinta da sífilis em
gestante e da sífilis congênita (**SIFC**). Não reutilizar a ficha ou
o dicionário de gestantes/congênita para validar SIFA.

## Achado documental: ZIKA

A [página de Zika no Portal SINAN](https://portalsinan.saude.gov.br/zika)
vincula o dicionário geral de
[Notificação Individual](https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/DIC_DADOS_NET_Not_Individual_rev.pdf),
identificado como SINAN NET 5.0, revisão 2018. O
[Portal de Dados Abertos do SUS](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus)
apresenta, no registro curado, dois recursos rotulados ZIKA/2024:
JSON e Parquet. Esses ponteiros não provam bytes, origem completa, data
de corte, esquema ou situação final.

## Subetapa ZIKA concluída: identidade de metadados de catálogo

Uma [conferência independente das duas páginas oficiais de ZIKA/2024](ZIKA_2024_OFFICIAL_RESOURCE_IDENTITY.md)
registrou a coincidência de UUID, formato, título, ID do conjunto e caminho
de distribuição com os dois ponteiros já curados. O comando offline
`confrontar-identidade-zika-2024` detecta divergência entre o snapshot
versionado e o catálogo local. O diagnóstico exibe a situação de cada
subetapa separadamente.

**Não encerrar o tópico "identidade_do_recurso":** a identidade dos
metadados da página é diferente da integridade/autenticidade dos bytes,
versão, data de corte e condição de arquivo preliminar/final.
A matriz permanece com **10 tópicos pendentes**. O novo snapshot não
comprova atualização em tempo real nem altera indicadores científicos.

## Matriz de tarefas sem dados de pacientes

| Grupo documental | Verificação necessária | Situação |
|---|---|---|
| Identidade do recurso | UUID, filename, ano rotulado, data de corte e procedência | PENDENTE |
| Sistema de origem | Sistema, edição e módulo de notificação | PENDENTE |
| Instrumento | Instrumento indicado pelo MS versus versão do arquivo | PENDENTE |
| Campos comuns | Nomes/tipos/códigos documentados versus layout real | PENDENTE |
| Campos próprios | Se há extensões próprias, documentação e mudanças | PENDENTE |
| Definição de caso | Critérios históricos, filtros e exclusões aplicáveis | PENDENTE |
| Temporalidade | Ano do arquivo, notificação, sintomas, atualização | PENDENTE |
| Qualidade | Completude, duplicidade, consistência; somente com protocolo | PENDENTE |
| Privacidade | Minimização, supressão, risco cumulativo, bases legais | PENDENTE |
| Revisão independente | Parecer epidemiológico e autorização de divulgação | PENDENTE |

**Importante:** a tabela contém *categorias de verificação*, **não
colunas DBF/CSV/Parquet previamente encontradas em arquivo real**. Não foi
analisado cabeçalho nem variável de paciente; a matriz não calcula nem
legitima indicadores, coortes, aprovações ou estatísticas.

A etapa técnica posterior poderá produzir, em **ambiente institucional
autorizado e com revisão específica**, um confronto privado de esquema
entre layout/distribuição local e documento apropriado. Nome de coluna,
tipo, código e significado devem ter evidência rastreável, com
divergências explicitadas em vez de inferidas.

## Diagnóstico administrativo: Python 3.11 / Windows PowerShell 5.1

```powershell
py -3.11 -m sinan_mcp planejar-confronto-documental-2024 --agravo SIFA
py -3.11 -m sinan_mcp planejar-confronto-documental-2024 --agravo ZIKA
py -3.11 -m sinan_mcp confrontar-identidade-zika-2024
py -3.11 -m pytest -q tests/test_documentary_crosswalk_2024.py
```

O comando não aceita caminho de arquivo, fonte de dados, credencial, ano
dinâmico ou parâmetro de autorização. O retorno só contém fontes
públicas curadas, contadores de **referências** e tarefas pendentes.
Não importa SQLite, PySUS ou cliente de rede e não está no MCP público.

**Contagem multiagravo inalterada:** 14 aliases, 12 dicionários específicos
históricos localizados, 5 recursos anuais catalogados, 0 indicadores
homologados. Nenhum ZIP foi baixado, nenhum caso individual foi lido e
nenhuma publicação foi habilitada.
