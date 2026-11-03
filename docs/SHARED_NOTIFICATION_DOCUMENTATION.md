# P0 — Referência transversal de Notificação Individual (ZIKA e SIFA)

**Escopo: curadoria documental, não aprovação epidemiológica, acesso ou publicação.**

## Documento primário

O [Portal SINAN — Zika](https://portalsinan.saude.gov.br/zika) vincula
o item "Dicionário de Dados" ao
[documento geral de Notificação Individual](https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/DIC_DADOS_NET_Not_Individual_rev.pdf).
A primeira página informa **SINAN NET versão 5.0** e revisão em
**novembro de 2018**. O documento descreve os campos comuns de notificação,
não a estrutura completa de uma exportação ZIKA/2024.

O [Portal SINAN — Notificações](https://portalsinan.saude.gov.br/notificacoes)
descreve os campos comuns às notificações de múltiplos agravos. Para o alias
**SIFA** (sífilis adquirida), esta é apenas uma **hipótese documental
transversal**: não foi identificada nessa investigação uma página oficial
que associe diretamente um PDF específico de SIFA ao arquivo anual 2024.
Não confundir SIFA com **SIFC** (sífilis congênita) nem **SIFG** (sífilis
em gestante), que possuem fichas e dicionários de outros escopos.

## Evidência oficial adicional de 2024 sobre SIFA

O [Guia de Vigilância em Saúde, volume 2, sexta edição revisada (MS, 2024)](https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/svsa/vigilancia/guia-de-vigilancia-em-saude-volume-2-6a-edicao),
na **página impressa 506**, estabelece o uso da Ficha de
Notificação/Conclusão para registrar **sífilis adquirida em adultos**.
A [Nota Informativa nº 2/2017 do MS](https://portalsinan.saude.gov.br/images/documentos/Agravos/Sifilis-Ges/Nota_Informativa_Sifilis.pdf),
em sua seção 2.2, também refere a Ficha de Notificação Individual
para casos de sífilis adquirida.

Isso confirma a **orientação oficial de instrumento de notificação para
SIFA**, mas **não** confirma vínculo direto do PDF de 2018 ao arquivo SIFA/2024
nem sua correspondência campo a campo. A orientação para sífilis em gestantes
e sífilis congênita é distinta. Para a investigação de SIFA, verificar
prioritariamente a edição aplicável do instrumento de Notificação/Conclusão
e o layout real da exportação, em vez de presumir que deva existir um
dicionário exclusivo de investigação de sífilis adquirida.

O novo campo `orientacao_especifica_de_notificacao_no_guia_2024` registra
esse apoio documental sem alterar `vinculo_direto_na_pagina_do_agravo`,
`dicionario_especifico_neste_registro` ou os bloqueios científicos.

## Evidência registrada

| Agravo | PDF geral localizado | Vínculo direto no Portal SINAN | Dicionário específico 2024 confirmado |
|---|---|---|---|
| ZIKA | Referência encontrada | SIM, na página do agravo | NÃO |
| SIFA | Candidato transversal + orientação ministerial explícita da ficha (2024) | NÃO, apenas página geral | NÃO |

Este módulo registra **2 referências candidatas, das quais 1 tem vínculo
direto**, sempre para o **ano pretendido de 2024**, e sem afirmar que
a edição de 2018 corresponde ao layout ou ao sistema de origem de 2024.

As contagens do diagnóstico multiagravo **não mudam**: 14 aliases,
13 com dicionário específico histórico curado, 5 distribuições anuais
identificadas, 0 indicadores homologados.

## Diagnóstico administrativo

Em uma instalação dessa branch:

```powershell
py -3.11 -m sinan_mcp diagnosticar-documentacao-transversal --ano 2024
py -3.11 -m sinan_mcp diagnosticar-documentacao-transversal --ano 2024 --agravo SIFA
py -3.11 -m sinan_mcp planejar-confronto-documental-2024 --agravo SIFA
py -3.11 -m sinan_mcp planejar-confronto-documental-2024 --agravo ZIKA
py -3.11 -m pytest -q tests/test_shared_notification_documents.py
```

Somente metadados constantes no código, sem arquivos locais, banco, pacientes,
rede ou publicação. Este comando não foi conectado ao servidor MCP público.

## Pendências de revisão científica

1. Identificar o layout nacional de exportação SIFA/2024, a versão da
   Notificação/Conclusão efetivamente aplicável e eventual documentação
   complementar; não substituir por dicionário de sífilis congênita/gestante.
   A ausência de dicionário exclusivo não significa ausência de
   instrução oficial de notificação, já documentada no guia de 2024.
2. Confrontar os campos comuns da Notificação Individual e os campos
   próprios de ZIKA com a edição de 2024, em ambiente institucional
   e mediante protocolo autorizado.
3. Identificar sistema de origem, datas de corte, situação preliminar/final,
   versões e mudanças de layout de cada distribuição.
4. Exigir revisão independente da coorte, indicadores, proteção de dados
   e política de divulgação antes de qualquer uso/publicação real.

A existência de qualquer referência oficial **não** promove automaticamente
flags de acesso, validação ou publicação.
