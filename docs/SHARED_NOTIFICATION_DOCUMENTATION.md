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

## Evidência registrada

| Agravo | PDF geral localizado | Vínculo direto no Portal SINAN | Dicionário específico 2024 confirmado |
|---|---|---|---|
| ZIKA | Referência encontrada | SIM, na página do agravo | NÃO |
| SIFA | Candidato transversal | NÃO, apenas página geral | NÃO |

Este módulo registra **2 referências candidatas, das quais 1 tem vínculo
direto**, sempre para o **ano pretendido de 2024**, e sem afirmar que
a edição de 2018 corresponde ao layout ou ao sistema de origem de 2024.

As contagens do diagnóstico multiagravo **não mudam**: 14 aliases,
12 com dicionário específico histórico curado, 5 distribuições anuais
identificadas, 0 indicadores homologados.

## Diagnóstico administrativo

Em uma instalação dessa branch:

```powershell
py -3.11 -m sinan_mcp diagnosticar-documentacao-transversal --ano 2024
py -3.11 -m sinan_mcp diagnosticar-documentacao-transversal --ano 2024 --agravo SIFA
py -3.11 -m pytest -q tests/test_shared_notification_documents.py
```

Somente metadados constantes no código, sem arquivos locais, banco, pacientes,
rede ou publicação. Este comando não foi conectado ao servidor MCP público.

## Pendências de revisão científica

1. Identificar fonte nacional específica de SIFA e esquema da exportação;
   não substituir por dicionário de sífilis congênita/gestante.
2. Confrontar os campos comuns da Notificação Individual e os campos
   próprios de ZIKA com a edição de 2024, em ambiente institucional
   e mediante protocolo autorizado.
3. Identificar sistema de origem, datas de corte, situação preliminar/final,
   versões e mudanças de layout de cada distribuição.
4. Exigir revisão independente da coorte, indicadores, proteção de dados
   e política de divulgação antes de qualquer uso/publicação real.

A existência de qualquer referência oficial **não** promove automaticamente
flags de acesso, validação ou publicação.
