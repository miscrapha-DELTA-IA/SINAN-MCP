# SINAN MCP — planejamento multiagravo e publicação segura

Este guia separa descoberta de agravos, análise local controlada, candidatos
de tabulações e divulgação revisada. Código independente do MS/DATASUS.

## A instância pública

Ferramentas de metadados: pesquisar_agravos, descrever_agravo,
matriz_capacidades e planejar_consulta_agravo. A última aceita nome ou
alias, ano opcional, UF opcional e sexo ou raca_cor. "Sífilis" retorna
ambiguidade entre adquirida/congênita, em vez de adivinhar uma condição.

Exemplo de chamada: planejar_consulta_agravo(agravo="hanseníase", ano=2023, uf="PI", por="sexo")

O retorno traz referência, fontes oficiais e etapas de verificação:
consulta_executada=false e resultado_epidemiologico=null. Nenhum dado real
é consultado. Nome ausente não significa agravo ausente do SINAN.

A única demonstração numérica pública permanece a simulação 100% FICTÍCIA
TUBE/2024/PI. Catálogo referenciado não equivale a dado disponível.

## Antes de qualquer tabulação real

1. Origem: confirmar arquivo/versão, dicionário por agravo e ano,
   território de residência/notificação, definição temporal e consolidação.
2. Intake local: preparar-tabela-oficial admite apenas candidato privado.
   Não busca dados e NÃO verifica o hash declarado contra arquivo remoto.
3. Bloqueios conservadores: uma dimensão, categorias de sexo/raça-cor
   conhecidas, no mínimo 100 registros totais e 20 por categoria incluída;
   rejeita categorias arbitrárias, JSON com chaves duplicadas e symlink
   que redirecione data/ para fora do local privado.
4. Revisão humana independente: confrontar com fonte original, conferir
   categorias não incluídas/suprimidas, releases anteriores, combinações
   por diferença e dados externos. Limiar de célula não prova anonimização.
5. Divulgação separada: exige autorização institucional explícita, pacote
   estático revisado e checksum; o servidor público sintético NÃO é
   substituído automaticamente.

Microdados não devem ser adicionados ao GitHub nem enviados a assistentes
remotos. O candidato TUBE-2024-PI-sexo previamente bloqueado permanece
NÃO APROVADO e não é habilitado por nenhuma ferramenta deste módulo.

## Segurança e testes

Planejador não usa SQLite, PySUS, arquivos de pacientes, download ou SQL.
Alias de agravo não é código oficial de download validado. O mesmo
dicionário/indicador NÃO deve ser aplicado indiscriminadamente a 14 agravos.
Auditoria preditiva e equidade continuam processos LOCAIS, separados do MCP
público.

Python 3.11 ou 3.12:

    python -m pip install -e ".[dev]"
    python -m pytest -q

Testes cobrem ambiguidade, parâmetros inválidos, integração MCP, proteção
contra categorias cruzadas, JSON duplicado e symlinks. A CI cobre
Windows/Ubuntu. O projeto ainda requer validação epidemiológica e jurídica,
autorização adequada, proteção contra diferenças entre versões e autenticação
antes de acesso remoto a quaisquer dados sensíveis.
