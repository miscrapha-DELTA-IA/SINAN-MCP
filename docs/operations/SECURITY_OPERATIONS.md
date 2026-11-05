# Operação segura do SINAN MCP público

Status: hardening sintético implantado em 2026-11-04 na Render (SHA 3ac1db9dd4bb81b3bf685356528da4572c4f0c3d), com sonda HTTPS pós-deploy aprovada. A implantação NÃO certifica configuração de alertas, retenção de logs, variáveis privadas, proteção de borda nem uso de bases reais.

## 1. Limites de entrada e arquitetura
- No código atualmente implantado, o limite global por processo é 300 requisições HTTP ao /mcp por minuto, usando token bucket com reposição contínua e recusa 429 com Retry-After.
- Até 16 requisições /mcp em processamento simultâneo. Inteiros inválidos ou zero são rejeitados no startup.
- **Teto fail-closed:** este perfil público aceita configuração de 1 a 300 requisições/min e de 1 a 16 simultâneas, mas rejeita no startup valores superiores. A instância pública não pode ampliar silenciosamente esses limites por variável de ambiente; reduções conservadoras continuam permitidas.
- O /health não consome o orçamento MCP, para manter sondas de vida; isso exige proteção adicional na borda contra excesso de sondagens.
- Não confiar em X-Forwarded-For nem identificar usuários pelos headers enviados pelo cliente. O controle é por processo, NÃO é rate limit individual, compartilhado entre máquinas ou garantia contra DDoS.
- O provedor/edge deverá impor limites por origem confiável e proteção de /health antes de qualquer ampliação relevante de usuários.
- Apenas 10 ferramentas públicas previstas no contrato, base TUBE 2024/PI com 120 registros ficcionais, sem arquivos/SQL, escrita, banco de pesquisa ou credenciais privadas.

## 2. Observabilidade sem revelar dados
- O middleware emite contagens agregadas por intervalo de 60 segundos **quando chega outra solicitação MCP**: aceitas, rejeitadas por taxa, rejeitadas por concorrência e em processamento. Ausência de linha de telemetria não comprova disponibilidade nem ausência de requisições.
- O uvicorn deverá operar com log de acesso individual desativado. Evitar imprimir payloads MCP, argumentos de ferramentas, IPs, cookies, tokens, pacientes, caminhos privados ou variáveis secretas.
- A telemetria da aplicação não controla automaticamente os logs do proxy ou da Render. Conferir acesso, retenção e conteúdo no workspace correto.
- Metas de alerta, ainda NÃO configuradas/confirmadas: health indisponível por 5 minutos; 5xx acima de 2% por 5 minutos; 429 acima de 10% por 10 minutos; p95 de /mcp acima de 3 s por 10 minutos; mudança inesperada no inventário de ferramentas.
- Meta de retenção para logs operacionais sanitizados: no máximo 14 dias, se o plano permitir. Evidências estritamente necessárias a incidentes: revisar separadamente, com alvo de até 30 dias. Esses prazos são alvos propostos, NÃO política já aplicada pelo provedor.
- A coleta de métricas não pode transformar metadados em um repositório secundário de informações clínicas.

## 3. Classificação e resposta a incidentes
1. Preservar hora UTC, versão SHA executada, ambiente, totais de 429/5xx e status de saúde sem capturar dados sensíveis.
2. Se surgir qualquer acesso a banco, microdado, ferramenta administrativa, SQL ou resultado real no público: interromper o serviço e escalar imediatamente para revisão de segurança e privacidade antes de restaurá-lo.
3. Se ocorrer abuso ou falhas 429/5xx: examinar métricas agregadas e proteção da borda; não aumentar limites cegamente.
4. Reverter manualmente para o último SHA público comprovadamente sintético e testado. Verificar startCommand, variáveis, ausência de disco/DB, controle de origem e inventário antes de retornar.
5. Executar scripts/probe_public_https.py contra a revisão efetivamente implantada: /health, inicialização MCP, 10 ferramentas, 120 registros fictícios, negativa para operações administrativas e Origin estranho.
6. Registrar cronologia, impacto observado, causa, remediação e testes posteriores sem publicar segredos, logs identificáveis ou detalhes exploráveis.
7. Reportar vulnerabilidades privadamente ao mantenedor, por meio de avisos de segurança GitHub quando disponíveis. Não anexar dados clínicos a issues.

## 4. Revisões periódicas
- Semanal: revisão de Dependabot, avisos de dependências e resultados da auditoria de Python.
- Antes de cada merge/deploy: confirmar lockfile e SHA, CI inteira, contrato sintético, revisão de diff e limite de recursos.
- Mensal: testar recuperação, revisar logs e acessos, checar regras da main e versão real no Render.
- Após mudanças em provedor/reverse proxy: repetir testes Host/Origin e verificar se /mcp preserva HTTPS.

## 5. Limites desta proposta
Nenhuma suíte automatizada certifica anonimização, disponibilidade contra ataque ou equivalência de indicadores oficiais. Mesmo com hash-pin e teste de rede, só existe validação funcional do software. O caminho privado de pesquisa nunca deverá ser incorporado ao serviço público. Consulte os checklists de GitHub e Render neste diretório.

### Versão do interpretador

O manifesto proposto fixa Python 3.11.17 para ser compatível com os lockfiles resolvidos sob Python 3.11. Serviços novos da Render podem escolher outro padrão se não houver pin. Conferir qualquer variável PYTHON_VERSION preexistente, que prevalece sobre .python-version; não presumir que mudar o repositório alterou o processo já implantado.

## 6. Verificação contínua, separada de deploy

- A action [Public HTTPS MCP smoke](../../.github/workflows/public-live-smoke.yml) executa a sonda somente leitura `scripts/probe_public_https.py` **duas vezes por dia**, aproximadamente às 06h17 e 18h17 no horário de Fortaleza (UTC-3), além de aceitar execução manual. Agendamentos do GitHub são sujeitos a atraso ou ausência de execução.
- A sonda usa o host público explicitamente fixado no workflow. Verifica `/health`, initialize, inventário exato de 10 ferramentas, dados 100% sintéticos, contagem fictícia 120 e rejeição de operações proibidas/Origin estranho. Nenhum download de microdados, token ou acesso ao servidor privado.
- O workflow usa apenas `contents: read`, sem segredos ou deploy, com concorrência limitada para não sobrepor execuções. Um resultado **vermelho** indica investigação necessária; não aciona automaticamente reinicialização, escalonamento de recursos, publicação nem rollback.
- Consulte [Actions](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/actions/workflows/public-live-smoke.yml) e habilite notificações de falha do GitHub se desejar alertas. Um workflow agendado **não garante que uma notificação será entregue**. Considerar solução externa de monitoramento mais adiante se for necessário SLA ou alerta imediato.
- Um erro pode representar atraso de cold start do plano Free, indisponibilidade da rede, mudança de contrato ainda não implantada ou falha do serviço. Antes de qualquer medida, conferir SHA Live e logs da Render, repetir sonda manualmente e comparar com a revisão anterior.
- Proteção de borda por origem, monitoramento de 5xx/429 e retenção sanitizada continuam **não comprovados**. O serviço em `.onrender.com` não está automaticamente protegido pela zona Cloudflare de um domínio de terceiros.

## 7. Rejeições esperadas versus erros de aplicação

- Parâmetros de ferramenta fora do contrato sintético devem gerar `ToolError` previsto pelo SDK MCP 2.3.0, com `isError=true`; não constituem falhas 5xx da aplicação nem devem emitir traceback.
- Rejeitar parâmetros de município, agravo não habilitado, ano ou agrupamento fora da demonstração permanece obrigatório. A mensagem de erro usa apenas uma explicação fixa e **não repete** argumentos ou identificadores enviados pelo cliente.
- Falhas realmente imprevistas continuam sendo registradas com traceback pelo SDK; não suprimir logs de crash por configuração global para esconder problemas reais.
- Após integrar uma correção na `main`, a mudança só alcança a Render mediante deploy manual controlado, com sonda HTTPS pós-deploy. Não misturar sinal verde de CI com mudança automaticamente publicada.


## 8. Registro de falhas da sonda sintética, sem automatizar a infraestrutura

- O workflow [Record public MCP smoke failure incident](../../.github/workflows/public-smoke-incident.yml) reage a um `workflow_run` com conclusão `failure` somente da sonda pública, em execução agendada ou manual, na branch `main`. Não dispara para um PR, fork, outro workflow nem conclusão de sucesso.
- O workflow original da sonda permanece `contents: read`. Apenas o **job separado** de ocorrência pode usar `issues: write` para criar/comentar uma issue sanitizada no mesmo repositório. Utiliza apenas `GITHUB_TOKEN` efêmero, nunca uma chave Render.
- O job baixa **apenas a `main` protegida**, não o commit/evento de uma execução falha. Não lê nem publica argumentos MCP, logs brutos, artefatos, credenciais, IPs ou dados reais. Issues abertas com o título fixo são atualizadas em falhas subsequentes, evitando duplicatas. Um problema de paginação da API bloqueia a criação.
- A issue serve como **registro rastreável de um incidente**, não como comprovante de que alguém recebeu um e-mail. Para receber notificações automáticas, o mantenedor deve configurar GitHub → Settings → Notifications → System → Actions → Email → Only notify for failed workflows. Segundo a documentação do GitHub, a notificação de uma execução agendada é dirigida ao usuário que criou ou alterou o cron; o recebimento deve ser verificado separadamente.
- **Sem simular queda do serviço** para testar: a suite testa a criação de issue com eventos sintéticos e cliente falso, sem token ou acesso HTTP. As issues reais só serão criadas diante de falhas verdadeiras. Se `issues: write` não estiver autorizado pelas políticas do repositório, o job acusará falha, não tentará um método alternativo de maior privilégio.
- Limitação importante: `schedule` no GitHub é de melhor esforço, e `workflow_run` só dispara após uma execução concluída. Essa solução não é SLA nem monitora intervalos em que uma execução não ocorreu.

### Proteção na borda

- A Render fornece DDoS básico automaticamente, inclusive em `.onrender.com`; isso **não** comprova limites L7 por usuário/origem nem regras WAF personalizadas na conta do serviço.
- O middleware público tem limites globais por processo de 300 requisições/minuto e 16 simultâneas. O endpoint `/health` não entra nesse orçamento, portanto precisa de mitigação no provedor em caso de abuso. Nunca inventar identificação de cliente a partir de headers `X-Forwarded-For` sem um proxy confiável definido.
- Regras IP de entrada para serviços web exigem plano elegível da Render e não são equivalente a filtro L7. Não ativar uma regra restritiva nem forçar um domínio customizado sem plano de conectividade e validação de Host/Origin. Não aplicar proteções do domínio Cloudflare de outro projeto sobre o hostname Render.
- No workspace Hobby, o destino `Email` e o nível `Only failure notifications` foram conferidos visualmente pelo operador. A entrega de e-mail **ainda não foi observada**; o serviço herda `notifyOnFail=default`. A retenção documentada de logs no plano Hobby é sete dias, e o conector retornou logs sanitizados da aplicação.

## 9. Teto de admissão da demonstração pública

- O código limita o valor máximo de `SINAN_PUBLIC_RATE_PER_MINUTE` a **300** e `SINAN_PUBLIC_MAX_IN_FLIGHT` a **16**, na inicialização e também na construção direta de `PublicAdmissionGuard`. Antes da alteração, a validação genérica permitia configurar valores de até 12.000/min e 128 simultâneas, embora o serviço efetivo usasse limites menores.
- Esta proteção impede aumentos involuntários do orçamento global de /mcp, mas **não é** cota por usuário nem substitui um WAF e proteção da borda por origem.
- Testes offline cobrem limites acima do máximo, configuração conservadora inferior, falha de inicialização sem abrir socket e liberação de slots em cancelamentos.
- Uma mudança nesta camada só vale na Render **após deploy manual testado**; antes, a revisão publicada continua com os limites de configuração do código antigo. A variável atualmente observada no painel não foi modificada.
