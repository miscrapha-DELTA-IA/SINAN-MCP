# Documentação | SINAN MCP

**Centro documental do projeto — 5 de novembro de 2026**  
[Visão geral](../README.md) · [English overview](../README.md) · [Código-fonte](../sinan_mcp) · [Segurança](../SECURITY.md)

O **SINAN MCP** é um projeto independente de código aberto que utiliza o *Model Context Protocol* para organizar a consulta a referências documentais e testar fluxos de pesquisa epidemiológica. **Não é um serviço do Ministério da Saúde, SINAN ou DATASUS.** A demonstração pública utiliza somente dados fictícios; não consulta registros reais de notificações.

> [!IMPORTANT]
> **Limite de validação:** sete PDFs oficiais foram submetidos a conferência automática de integridade e 57 identificadores de campos foram localizados nas páginas citadas. A compatibilidade com exportações SINAN de 2024, a semântica dos campos e a revisão científica independente **não foram homologadas**.

## Acesso rápido

| Preciso... | Documento | Conteúdo |
| --- | --- | --- |
| Entender o projeto | [Introdução em português](pt-BR.md) | Objetivo, estágio, demonstração e arquitetura |
| Avaliar a documentação | [Guia de revisão externa](instruments-2024/EXTERNAL_REVIEW.md) | Passos, fontes, como registrar um parecer ou teste |
| Consultar as evidências de Zika/TB | [Protocolo documental 2024](instruments-2024/REVIEW_PROTOCOL.md) | Versões, sete PDFs, hashes, 57 campos e limites |
| Conferir os campos | [Matriz CSV](instruments-2024/field_matrix.csv) | Código, rótulo, página, origem e status de revisão |
| Verificar os PDFs de origem | [Manifesto JSON](instruments-2024/source_manifest.json) | Fonte exata, páginas, hash e versionamento |
| Entender o catálogo | [Catálogo documental](research/DOCUMENTARY_CATALOG_V1.md) | Referências institucionais para 14 temas |
| Testar o software | [Instalação local](LOCAL_SETUP.md) | Demonstração exclusivamente sintética |
| Reportar um problema | [Contribuições](../CONTRIBUTING.md) | Fluxo de issue, PR e evidências reprodutíveis |

## Estado de qualidade

| Evidência ou requisito | Situação | O que comprova |
| --- | --- | --- |
| Identidade, tamanho, hash SHA-256 e paginação de sete PDFs | **Verificado automaticamente** | Correspondência dos bytes recebidos com o manifesto |
| Presença de 57 identificadores nas páginas declaradas | **Verificado automaticamente** | Ocorrência textual dos códigos nas páginas |
| Definições, rótulos, categorias e obrigatoriedade dos campos | **Pendente de revisão humana** | Interpretação documental correta |
| Equivalência com arquivos de dados do ano de 2024 | **Não verificada** | Layout, tipagem e versão da distribuição |
| Parecer independente epidemiológico, de sistemas e privacidade | **Pendente** | Escopo, achados, limitações e responsáveis |
| Autorização para usar ou publicar dados reais | **Não concedida** | Depende de processo separado, inclusive base legal aplicável |

O [protocolo 2024](instruments-2024/REVIEW_PROTOCOL.md) diferencia as provas automatizadas de qualquer conclusão científica. Consultas ao servidor público não alteram esse status.

## Referência técnica

| Área | Conteúdo |
| --- | --- |
| [Catálogo multiagravo](research/MULTI_AGRAVO_CATALOG.md) | Cobertura prevista e identificação interna |
| [Epidemiologia](research/EPIDEMIOLOGY.md) | Casos, indicadores, denominadores e inferências |
| [Segurança operacional](operations/SECURITY_OPERATIONS.md) | Controles técnicos e limitações da implantação |
| [Privacidade e divulgação](compliance/PUBLIC_DISCLOSURE.md) | Aviso da demonstração pública e dados sintéticos |
| [Publicação de agregados](research/AGGREGATE_PUBLICATION.md) | Bloqueios e avaliação para eventual uso futuro |
| [Equidade em modelos](research/FAIRNESS_PROTOCOL.md) | Métodos experimentais, exclusivamente locais |
| [Contrato MCP](public-mcp-contract-v1.json) | Interface versionada da demonstração |

## Registro de mudanças

Cada alteração em **fonte, hash, classificação de campo, regra epidemiológica ou estado de revisão** deve ter diff rastreável, justificativa, teste aplicável e, quando pertinente, um novo parecer. A mera edição de documentação ou aprovação de CI não muda o status de autorização.

**Auditoria em andamento:** [issue #62 — revisão científica e documental](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/issues/62). A identidade de revisores, vínculos e decisões deve ser registrada somente após manifestação efetiva, nunca antecipada.
