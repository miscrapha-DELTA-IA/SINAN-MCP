# P0 — Consolidação técnica em revisão do SINAN MCP (sem aprovação clínica)

**Escopo:** consolidação **proposta** dos PRs em rascunho #1 e #3–#13, com nova camada de segurança e observabilidade documental. Este documento não constitui aprovação do Ministério da Saúde, parecer científico independente, autorização legal, disponibilização de dados individuais ou autorização de publicação. Merge na main permanece decisão humana distinta.

## 1. Topologia real da pilha GitHub

Dependências dos PRs (cada PR está em DRAFT; #2 é issue, não PR):

| Ordem | PR | Tema | Base |
|---|---|---|---|
| 1 | #1 | planejamento multiagravo e segurança | main |
| 2 | #3 | proveniência, qualidade, reconciliação | #1 |
| 3 | #4 | semântica e contratos MCP | #3 |
| 4 | #5 | documentos oficiais por agravo/ano | #4 |
| 5 | #6 | identificadores de distribuições CKAN | #5 |
| 6 | #7 | comparação privada de esquemas | #6 |
| 7 | #8 | extração local de metadados de PDF | #7 |
| 8 | #9 | confronto documental DENG/2024 | #8 |
| 9 | #10 | inventário de sete gates de prontidão | #9 |
| 10 | #11 | plano privado de nove checkpoints DENG/2024 | #10 |
| 11 | #12 | ensaio com seis linhas 100% sintéticas | #11 |
| 12 | #13 | sete questões para revisão científica | #12 |

**Consolidar NÃO significa mesclar os PRs automaticamente.** Esta branch sai do HEAD do PR #13 e apresenta um PR único para main **em rascunho** para facilitar auditoria do conjunto. Alterar a base dos PRs originais ou realizar merge depende de revisão humana; não apagar histórico, não executar deploy e não modificar a infraestrutura pública durante a consolidação.

## 2. Capacidades por agravo e ano — sem inventar cobertura

Novo comando de diagnóstico administrativo, com metadados de catálogos versionados **apenas**:

    py -3.11 -m sinan_mcp diagnosticar-cobertura-multiagravo --ano 2024
    py -3.11 -m sinan_mcp diagnosticar-cobertura-multiagravo --ano 2024 --agravo CHIK

Para o índice atualmente curado:

- 14 aliases de referência, não 14 conectores comprovados nem lista exaustiva nacional.
- Esta pilha documental aumenta a contagem de dicionários específicos localizados de 3 para 12. A extensão ZIKA/2024 adiciona 2 recursos catalogados (JSON e Parquet), elevando as distribuições de 3 para 5. Isso **não** aumenta a contagem de dicionários específicos nem confirma correspondência com o arquivo de 2024. Dados individuais, indicadores, acesso real e autorização de publicação permanecem bloqueados.
- DENG/2024: 2 distribuições anuais identificadas no portal (CSV e JSON), **sem validação epidemiológica da exportação**.
- CHIK/2024: 1 distribuição anual identificada (JSON), sem validação anual do esquema/indicadores.
- ZIKA/2024: 2 distribuições anuais identificadas (JSON e Parquet) no portal. **Nenhum dicionário específico ZIKA/2024 validado ou curado neste índice.** A página do Portal SINAN refere o dicionário de Notificação Individual, de natureza geral.
- TUBE/2024: documentação histórica localizada, sem distribuição anual exata autenticada neste índice.
- 12 agravos têm dicionários históricos específicos localizados (incluindo TUBE, DENG e CHIK), todos com **aplicabilidade a 2024 não verificada**. Os aliases ZIKA e SIFA seguem sem dicionário específico curado nesta matriz; uma ficha genérica não supre esse requisito.
- **Nenhum indicador clínico real homologado**; flags arquivo_anual_autenticado, dicionario_aplicavel_ao_ano_validado, coorte_ano_validada, indicador_real_homologado, dados_reais_disponiveis_no_mcp_publico e publicacao_autorizada são obrigatoriamente false.

O diagnóstico não recebe ZIP/CSV/SQLite/credencial, não abre data/, não consulta serviços externos nem disponibiliza linhas ou números epidemiológicos.

## 3. Fronteira público/privado — checagem automatizada

- MCP público: python -m sinan_mcp.public_server **somente metadados e demonstração TUBE inteiramente fictícia**. O Render Blueprint (render.yaml) chama exclusivamente esse módulo, declara autoDeploy: false e SINAN_PUBLIC_REAL_DATA=0. **Não foi alterado nesta branch.**
- scripts/check_public_isolation.py usa AST para percorrer importações locais transitivas do public_server e **só aceita módulos públicos revisados**. Bloqueia imports de core, server, tool_api, release_pipeline, módulos locais administrativos, pacotes típicos de acesso a banco/rede, importação dinâmica e leitura de SINAN_DB_PATH por os.getenv.
- A etapa agora roda no CI em Ubuntu/Windows com Python 3.11/3.12. Suas próprias limitações devem ser conhecidas: análise estática **não substitui** pentest, verificação de comportamento em tempo de execução, revisão de dependências, segurança de transporte, monitoramento nem proteção contra futura manipulação de código.
- O teste existente tests/test_public_mcp_contract.py congela as ferramentas públicas, entradas, descrições e protocolo MCP e recusa ferramentas administrativas.
- **Atenção ao legado:** sinan_mcp.server / sinan_mcp.rest / sinan_mcp.tool_api incluem caminhos locais de acesso a projeções e uma flag SINAN_PUBLIC_REAL_DATA=1. Eles NÃO são o servidor público demonstrativo e NÃO devem ser hospedados, expostos por túnel ou ativados com dados clínicos reais sem autorização, autenticação e revisão institucional adequadas. O verificador AST protege o public_server, não elimina os riscos operacionais desses módulos.
- scripts/check_sensitive_repo.py bloqueia nomes/extensões privadas rastreadas pelo Git, mas **não é scanner de segredos por conteúdo**. Revisão de commits, dependências, segurança de credenciais e histórico permanece necessária.

## 4. Critérios técnicos para futura integração

Executar no branch consolidado, Windows e Linux, 3.11/3.12:

    python scripts/check_sensitive_repo.py
    python scripts/check_public_isolation.py
    python -m pytest -q
    python -m sinan_mcp demo
    python -m sinan_mcp diagnosticar-cobertura-multiagravo --ano 2024

Além disso: executar matrizes opcionais PDF, esquema/JSON, Pandera, PySUS offline. Confirmar testes de inexistência de DB/ZIP no caminho público, congelamento do contrato MCP, ausência de logs de valores clínicos e estabilidade do modo sintético.

**Pendências irredutíveis por engenharia:** revisão independente dos PRs, autenticação institucional, fonte/versão e dicionários de cada agravo, coorte e indicador, revisão de privacidade e divulgação cumulativa, decisão jurídica/ética competente, infraestrutura segura e eventual autorização explícita de deploy. Nenhuma delas pode ser suprida com marcação de true em JSON ou hashes SHA-256.

## 5. Prontidão científica — DENG/2024

A estação do operador já confirmou: 5 de 7 frentes sem evidência, 2 evidências locais **não homologadas**, nove checkpoints de qualidade pendentes, sete questões científicas pendentes e zero pareceres independentes autenticados. O órgão responsável foi contatado pelo operador; **um pedido enviado não significa resposta ou aprovação**.

**Estado até novos pareceres:** BLOQUEADO_PARA_USO_REAL_E_PUBLICACAO. Código integrado em CI não significa dados válidos; o MCP público não fornece consultas reais de doenças cadastradas no índice.


## 6. Snapshot imutável da implantação pública

O novo scripts/check_public_deployment.py compara render.yaml com a configuração **sintética conhecida** byte a byte. A CI recusa alterações involuntárias: iniciar sinan_mcp.server em vez de public_server, ativar SINAN_PUBLIC_REAL_DATA, habilitar autoDeploy, anexar um segundo serviço ou mesmo modificar comentários sem passar por revisão explícita. Este controle de snapshot **não analisa semanticamente YAML** e não inspeciona as configurações efetivas de uma conta Render; é apenas garantia verificável de que o blueprint sob Git não mudou inadvertidamente. Testes adversariais em tests/test_public_deployment_guard.py.

    python scripts/check_public_deployment.py

Antes de uma mudança legítima no blueprint, obter revisão humana da configuração e atualizar o snapshot junto com testes de segurança. Não realizar deploy automático como parte do P0.
