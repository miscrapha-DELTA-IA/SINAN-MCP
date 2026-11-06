# Guia rápido — SINAN MCP (sem programação)

O SINAN MCP é um **protótipo independente**. A instância pública oferece **referências documentais** e uma **simulação com números fictícios**; não consulta notificações reais do SINAN. Não é operada ou homologada pelo Ministério da Saúde, SINAN ou DATASUS.

## O que consultar sem instalar nada

1. Leia a [apresentação em português](pt-BR.md) para conhecer o projeto e suas limitações.
2. Para conferir documentos, abra o [protocolo Zika/TB](instruments-2024/REVIEW_PROTOCOL.md) e a [matriz de campos](instruments-2024/field_matrix.csv).
3. Se desejar colaborar, siga o [guia de revisão externa](instruments-2024/EXTERNAL_REVIEW.md). A revisão documental não exige execução de código.

## Conectar um cliente MCP remoto compatível (opcional)

Se o seu cliente **suportar servidores MCP remotos por HTTP**, adicione o endereço:

`https://sinan-mcp-public-preview.onrender.com/mcp`

Configure-o nas opções de servidores/conectores MCP do **próprio cliente**. O caminho `/mcp` é uma interface de comunicação, **não uma página para abrir no navegador**. O menu e o suporte a servidores remotos variam entre versões de clientes; não use instruções de um aplicativo em outro. A hospedagem gratuita pode suspender a instância após inatividade. Nenhuma configuração habilita dados reais.

**Perguntas de demonstração, sem dados clínicos:**

- “Quais fontes documentais públicas o SINAN MCP localiza para Zika e quais são seus limites?”
- “Liste os campos documentados de tuberculose e explique por que a compatibilidade do layout 2024 não está validada.”
- “Execute uma contagem **explicitamente fictícia** para `TUBE`, `ano_inicio=2024`, `ano_fim=2024`, `uf=PI`, `por=sexo`; não interprete como epidemiologia real.”

## Glossário mínimo

- **MCP:** protocolo para ferramentas e assistentes acessarem funções e referências de forma estruturada.
- **SHA-256:** impressão digital dos bytes obtidos de um arquivo; **não é** assinatura digital do emissor.
- **Matriz documental:** lista dos códigos encontrados nos dicionários, com páginas e observações; não contém valores de pacientes.
- **`NOT_VERIFIED`:** não foi comprovado que o campo corresponde a uma coluna da exportação 2024.
- **`PENDING`:** ainda não existe parecer humano independente registrado.
- **Dado sintético:** exemplo inventado para testar o software, não uma observação clínica nem estatística oficial.

## O que os números documentais significam?

Existem **7 documentos PDF oficiais** com integridade de bytes registrada e **57 linhas na matriz**: 37 Zika + 15 TB + 5 comuns. Os cinco campos comuns reaparecem em dois pacotes de apresentação (**42 linhas no pacote Zika** e **20 no pacote TB**, 62 ocorrências em pacotes). Isso **não comprova** a semântica de cada campo, a versão da exportação SINAN 2024 ou qualquer indicador epidemiológico.

Não envie prontuários, nomes, CPF, CNS, endereços nem arquivos individuais a esta instância ou a issues públicas. A documentação está aberta para revisão de sua exatidão e usabilidade.
