# Fontes e dicionários oficiais: registro por agravo e ano

**Estágio: curadoria de documentação, NÃO validação anual.**

Foram identificados documentos primários do Ministério da Saúde no Portal
SINAN. A indicação "oficial" vale para a página e o documento referenciado,
não para o arquivo de dados pretendido em determinado ano.

## Fontes verificadas no portal em 02/11/2026

| Agravo e ano pretendido | Referência documental | Edição | Correspondência com dados de 2024 |
|---|---|---|---|
| TUBE / 2024 | [Dicionário de tuberculose](https://portalsinan.saude.gov.br/images/documentos/Agravos/Tuberculose/DICI_DADOS_NET_Tuberculose_23_07_2020.pdf) | SINAN NET 5.0; nome PDF indica 2020 | NÃO verificada |
| DENG / 2024 | [Dicionário Dengue/Chikungunya](https://portalsinan.saude.gov.br/images/documentos/Agravos/Dengue/DIC_DADOS_ONLINE.pdf) | SINAN Online 3.0, histórico 2014–2015 | NÃO verificada |
| CHIK / 2024 | [Dicionário Dengue/Chikungunya](https://portalsinan.saude.gov.br/images/documentos/Agravos/Dengue/DIC_DADOS_ONLINE.pdf) | SINAN Online 3.0, histórico 2014–2015 | NÃO verificada |

As páginas oficiais são https://portalsinan.saude.gov.br/tuberculose e
https://portalsinan.saude.gov.br/dengue e
https://portalsinan.saude.gov.br/chikungunya. O Ministério da Saúde explica
a obtenção de dados por agravo e ano em:
https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/svsa/agravos-de-notificacoes/agravos-de-notificacoes .

Essa orientação remete aos dicionários de Docs_TAB_SINAN.zip. Não foram
confirmados nesta etapa o arquivo nacional de 2024, checksum publicado
pela autoridade, status final, data de corte ou versão de dicionário
vinculada ao arquivo TUBE, DENG ou CHIK de 2024.

Uma evidência documental localizada não garante correção para determinado
ano. O SINAN NET, SINAN ONLINE e outros sistemas podem empregar layouts
diferentes; o ano de arquivo não é automaticamente ano de notificação,
diagnóstico ou encerramento.

## Componentes implementados

1. Registro versionado e empacotado:
   sinan_mcp/registry/official_documentary_evidence.json.
   O formato exige HTTPS em domínio oficial, unicidade por agravo/ano,
   campos exatos e rejeita falsas flags de validação.
2. Módulo somente de metadados sinan_mcp/year_evidence_registry.py.
   Nunca lê microdados, banco SQLite nem acessa a internet.
3. Ferramentas públicas: listar_evidencias_documentais e
   consultar_evidencia_agravo_ano. Ambas retornam estados explícitos.
4. O planejador de consultas passa a anexar evidência específica do
   ano quando um único agravo é identificado. Sem registro para ano:
   sem_documentacao_anual_curada, sem inferir outro período.
5. Auditoria offline e facultativa: sinan_mcp/year_evidence_review.py.
   Compara manifesto com a URL exata do documento, verifica integridade
   local dos bytes do arquivo de dados e lê hash/tamanho do PDF fornecido
   pelo pesquisador. NÃO autentica o PDF oficial nem aprova sua
   aplicação a determinado ano.

Os dados reais no servidor público permanecem indisponíveis.

## Comandos locais para Windows PowerShell

    py -3.11 -m pip install -e ".[dev]"
    py -3.11 -m pytest -q tests/test_year_evidence_registry.py
    py -3.11 -m sinan_mcp listar-evidencias-ano
    py -3.11 -m sinan_mcp consultar-evidencia-ano --agravo TUBE --ano 2024
    py -3.11 -m sinan_mcp consultar-evidencia-ano --agravo TUBE --ano 2023

Somente se o pesquisador tiver documentos e arquivos legitimamente
obtidos e mantidos em ambiente privado, é possível executar:

    py -3.11 -m sinan_mcp confrontar-evidencia-ano .\data\manifesto.json .\data\arquivo-local.csv .\data\DICI_DADOS_NET_Tuberculose_23_07_2020.pdf

O manifesto deve seguir sinan-source-evidence-v1, informar agravo,
ano do arquivo, tamanho, SHA-256 e URL completa do PDF.
O documento PDF deve apresentar o nome oficial e cabeçalho PDF.
O hash local NÃO autentica publicação, revisor ou aplicabilidade.

**Não enviar arquivos ou resultados de auditoria privados para chats,
issues, logs públicos ou CI.** Todas as ferramentas administrativas de
verificação continuam fora do servidor MCP público.

## Gate para efetiva validação anual — AINDA PENDENTE

Para cada agravo/ano, exigir em sequência:

1. Origem oficial verificável, nome exato do arquivo nacional, método
   permitido de acesso, classificação de preliminar/final e data de corte.
2. Tamanho e hash observado do arquivo, distinguindo-os de qualquer
   checksum distribuído pela instituição.
3. Documento/dicionário aplicável especificamente ao layout e à edição
   do arquivo daquele ano, com evidência documental independente.
4. Compatibilidade de colunas, domínios, transformação de códigos,
   unidade observacional e sistema de origem.
5. Revisão epidemiológica de definições, coortes, denominadores,
   consistência, reconciliação e limitações.
6. Avaliação institucional de base legal, privacidade, composição
   acumulada de releases, retenção, revogação e divulgação.
7. Processo real de autenticação e atestação de revisores independentes.

A promoção automática de estados de documentação para
ano_validado NÃO está disponível no código. Um operador que altere JSON
ou passe um PDF com o nome correto não pode converter o status.
Os contratos Pandera TUBE_2024_EXAMPLE e DENG_2024_EXAMPLE continuam
inteiramente ilustrativos.

Os próximos passos serão compatibilização de dicionários oficiais com
arquivos concretos e definição de procedimento de revisão independente.
