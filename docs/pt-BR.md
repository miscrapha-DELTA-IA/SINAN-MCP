# SINAN MCP

**Catálogo documental, interoperabilidade MCP e pesquisa epidemiológica reprodutível**

[Centro de documentação](README.md) · [Guia rápido](QUICKSTART_PUBLICO.md) · [Dossiê Zika/TB 2024](instruments-2024/REVIEW_PROTOCOL.md) · [Revisão externa](instruments-2024/EXTERNAL_REVIEW.md) · [English](../README.md)

> [!IMPORTANT]
> **Protótipo independente de pesquisa.** Não é operado, certificado ou homologado pelo Ministério da Saúde, DATASUS ou SINAN. O servidor público fornece **apenas dados fictícios** para demonstração, nunca notificações reais nem indicadores clínicos validados.

## O que é

O **SINAN MCP** é um projeto de código aberto que utiliza o *Model Context Protocol* para organizar referências oficiais e descrições documentais relativas ao Sistema de Informação de Agravos de Notificação. Seu foco é identificar a origem dos documentos, registrar versões e explicitar limites científicos.

O projeto distingue três ambientes: **catálogo documental**, **demonstração pública sintética** e **ferramentas locais experimentais**. A infraestrutura pública não acessa o banco privado de pesquisa.

## Recursos disponíveis

| Recurso | Estado |
| --- | --- |
| Catálogo de referências | 14 identificadores internos para agravos e 17 páginas institucionais curadas |
| Instrumentos Zika e tuberculose | 7 PDFs de origem oficial e 57 registros de campos na matriz (42 Zika + 20 TB nos pacotes devido à reutilização de 5 campos comuns) |
| Ferramentas MCP externas | 10 operações somente leitura |
| Demonstração de tuberculose | 120 registros fictícios determinísticos, sem valor epidemiológico real |
| Ferramentas de pesquisa local | Diagnóstico/importação experimental fora do serviço público |

Os nomes de agravos no catálogo não representam automaticamente a disponibilidade de suas bases históricas, dicionários ou séries de casos.

## Validação documental

Os sete PDFs de Zika e tuberculose tiveram **hash SHA-256, tamanho e páginas** conferidos nos bytes recebidos. A CI histórica localizou 57 códigos por correspondência textual normalizada. O verificador exige agora identificadores delimitados, e a [CI 42144137431](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/actions/runs/42144137431) concluiu essa checagem com sucesso. Isso não demonstra concordância com dados reais de 2024.

Isso **não confirma** a semântica integral dos campos, a equivalência com arquivos SINAN de 2024 ou a aprovação independente do estudo. Essas atividades seguem pendentes de revisão epidemiológica, de sistemas de informação e de privacidade.

- [Dossiê de evidências e limitações](instruments-2024/REVIEW_PROTOCOL.md)
- [Guia para participar da revisão externa](instruments-2024/EXTERNAL_REVIEW.md)
- [Registro de pendências científicas #62](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/issues/62)

## Demonstrador público

| Serviço | Endereço |
| --- | --- |
| Conexão MCP para aplicativos | [`/mcp`](https://sinan-mcp-public-preview.onrender.com/mcp) |
| Estado do serviço | [`/health`](https://sinan-mcp-public-preview.onrender.com/health) |
| Informações | [Sobre](https://sinan-mcp-public-preview.onrender.com/sobre) · [Suporte](https://sinan-mcp-public-preview.onrender.com/suporte) |
| Privacidade e termos | [Privacidade](https://sinan-mcp-public-preview.onrender.com/privacidade) · [Termos](https://sinan-mcp-public-preview.onrender.com/termos) |

O endereço `/mcp` é uma **interface técnica**, não um site para leitura no navegador. A hospedagem gratuita pode apresentar demora após inatividade.

## Guia sem programação

Para navegar pelas fontes, conectar opcionalmente um cliente MCP remoto compatível e testar três perguntas com avisos sobre dados fictícios, consulte o [guia rápido público](QUICKSTART_PUBLICO.md).

## Instalação local

Para executar a demonstração em Windows PowerShell com Python 3.11+:

```powershell
git clone https://github.com/miscrapha-DELTA-IA/SINAN-MCP.git
cd SINAN-MCP
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m sinan_mcp demo
.\.venv\Scripts\python.exe -m pytest -q
```

A execução cria **exemplos fictícios**. Consulte as [instruções para outras plataformas](LOCAL_SETUP.md). A conexão ao ambiente local é assunto distinto da demonstração pública e exige os cuidados previstos na [política de segurança](../SECURITY.md).

## Documentação por área

| Área | Conteúdo |
| --- | --- |
| [Pesquisa e fontes](research/README.md) | Curadoria, abrangência e interpretação científica |
| [Instrumentos Zika/TB](instruments-2024/REVIEW_PROTOCOL.md) | Documentos, matriz, métodos, hashes e limites |
| [Guia rápido público](QUICKSTART_PUBLICO.md) | Passo a passo sem programação, glossário e exemplos sintéticos |
| [Operação técnica](operations/README.md) | Integração, infraestrutura, testes e documentação de engenharia |
| [Governança e privacidade](compliance/README.md) | Riscos, transparência e conformidade em avaliação |
| [Contribuições](../CONTRIBUTING.md) | Relatos verificáveis, revisão e contribuição com dados sintéticos |

O uso ou a divulgação de dados reais exige avaliação legal, ética, técnica e epidemiológica separada. O projeto não deve ser usado para decisões clínicas, relatórios oficiais ou estimativas de saúde pública.

O código-fonte original está sob a [licença MIT](../LICENSE), sem transferência de direitos sobre marcas ou documentos oficiais.
