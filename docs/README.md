# Documentação do SINAN MCP

O **SINAN MCP** é um projeto independente e de código aberto que organiza referências do Sistema de Informação de Agravos de Notificação por meio do *Model Context Protocol*. Não é um serviço oficial do Ministério da Saúde, DATASUS ou SINAN.

A demonstração pública utiliza **somente dados fictícios** e não disponibiliza indicadores epidemiológicos reais.

## Acesso por objetivo

| Interesse | Documento |
| --- | --- |
| Entender o projeto | [Apresentação em português](pt-BR.md) |
| Começar sem programação | [Guia rápido e glossário](QUICKSTART_PUBLICO.md) |
| Realizar uma avaliação externa | [Guia de revisão](instruments-2024/EXTERNAL_REVIEW.md) |
| Consultar a auditoria Zika/TB | [Dossiê documental](instruments-2024/REVIEW_PROTOCOL.md) |
| Executar a demonstração local | [Instalação](LOCAL_SETUP.md) |
| Reportar vulnerabilidades | [Segurança](../SECURITY.md) |

## Biblioteca

| Área | Conteúdo |
| --- | --- |
| [Pesquisa e fontes](research/README.md) | Catálogo, interpretação epidemiológica e protocolos de pesquisa |
| [Instrumentos Zika/TB](instruments-2024/REVIEW_PROTOCOL.md) | Sete PDFs, matriz e proveniência |
| [Operação e integração](operations/README.md) | Desenvolvimento, testes, clientes MCP e hospedagem |
| [Governança e privacidade](compliance/README.md) | Transparência, bases legais e riscos em avaliação |
| [Histórico](../CHANGELOG.md) | Mudanças no código e nas capacidades verificadas |

## Estado da avaliação documental

| Resultado | Alcance real |
| --- | --- |
| Sete PDFs verificados por SHA-256 e paginação | Integridade dos bytes recebidos |
| 57 registros de códigos localizados historicamente nas páginas indicadas | Checagem antiga por substring e [novo teste delimitado aprovado na CI 42144137431](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/actions/runs/42144137431); não é validação semântica |
| Concordância com exportação SINAN 2024 | **Não verificada** |
| Pareceres científicos e privacidade independentes | **Pendentes** |
| Uso de dados reais no servidor público | **Não autorizado** |

A [issue científica #62](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/issues/62) concentra os itens de acompanhamento. Documentos científicos apresentam evidências e limitações, sem checklists de programação.

[Repositório](https://github.com/miscrapha-DELTA-IA/SINAN-MCP) · [Versão em inglês](../README.md) · [Licença MIT](../LICENSE)
