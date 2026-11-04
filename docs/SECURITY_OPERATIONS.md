# Operação segura do SINAN MCP público

Status: hardening sintético implantado em 2026-11-04 na Render (SHA 3ac1db9dd4bb81b3bf685356528da4572c4f0c3d), com sonda HTTPS pós-deploy aprovada. A implantação NÃO certifica configuração de alertas, retenção de logs, variáveis privadas, proteção de borda nem uso de bases reais.

## 1. Limites de entrada e arquitetura
- No código atualmente implantado, o limite global por processo é 300 requisições HTTP ao /mcp por minuto, usando token bucket com reposição contínua e recusa 429 com Retry-After.
- Até 16 requisições /mcp em processamento simultâneo. Inteiros inválidos ou zero são rejeitados no startup.
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

- A action [Public HTTPS MCP smoke](../.github/workflows/public-live-smoke.yml) executa a sonda somente leitura `scripts/probe_public_https.py` **duas vezes por dia**, aproximadamente às 06h17 e 18h17 no horário de Fortaleza (UTC-3), além de aceitar execução manual. Agendamentos do GitHub são sujeitos a atraso ou ausência de execução.
- A sonda usa o host público explicitamente fixado no workflow. Verifica `/health`, initialize, inventário exato de 10 ferramentas, dados 100% sintéticos, contagem fictícia 120 e rejeição de operações proibidas/Origin estranho. Nenhum download de microdados, token ou acesso ao servidor privado.
- O workflow usa apenas `contents: read`, sem segredos ou deploy, com concorrência limitada para não sobrepor execuções. Um resultado **vermelho** indica investigação necessária; não aciona automaticamente reinicialização, escalonamento de recursos, publicação nem rollback.
- Consulte [Actions](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/actions/workflows/public-live-smoke.yml) e habilite notificações de falha do GitHub se desejar alertas. Um workflow agendado **não garante que uma notificação será entregue**. Considerar solução externa de monitoramento mais adiante se for necessário SLA ou alerta imediato.
- Um erro pode representar atraso de cold start do plano Free, indisponibilidade da rede, mudança de contrato ainda não implantada ou falha do serviço. Antes de qualquer medida, conferir SHA Live e logs da Render, repetir sonda manualmente e comparar com a revisão anterior.
- Proteção de borda por origem, monitoramento de 5xx/429 e retenção sanitizada continuam **não comprovados**. O serviço em `.onrender.com` não está automaticamente protegido pela zona Cloudflare de um domínio de terceiros.
