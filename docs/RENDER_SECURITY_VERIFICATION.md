# Render — checklist de auditoria somente leitura

Estado: confirmação de workspace e de configuração efetiva ainda pendentes. Os manifests de Git não provam como o serviço real está configurado.

1. Listar os workspaces e solicitar confirmação explícita do workspaceId correto. Não escolher automaticamente um workspace pelo nome.
2. No workspace confirmado, localizar exclusivamente sinan-mcp-public-preview; não modificar outros serviços da conta.
3. Registrar ID do serviço, URL HTTPS, plano, região, estado, commit SHA efetivamente executado e horário UTC do deploy.
4. Conferir se a inicialização é python -m sinan_mcp.public_server e se autoDeploy realmente está desativado nas definições do serviço.
5. Checar apenas os NOMES das variáveis, nunca os valores de segredos. Não permitir SINAN_DB_PATH, credenciais, configurações de túnel, aprovações de agregados reais ou parâmetros que conectem a dados privados.
6. Confirmar ausência de discos, banco gerenciado, montagens de pesquisa e regras de acesso à base privada.
7. Em implantação FUTURA autorizada, usar requirements-public.lock com hashes e versão validada, sem alterar startCommand, autoDeploy ou limite sintético.
8. Revisar limite por origem na borda, políticas de retenção, TLS, proteção antiabuso, monitoramento e alertas; não inferir que estão ativos só porque existem nos documentos.
9. Rodar a sonda HTTPS em modo leitura no commit implantado: /health, ferramentas 10, contagem fictícia 120, negação de chamadas inválidas e Origin não autorizado.
10. Guardar evidência não sensível do inventário, SHA e resultado. Nunca realizar deploy, reinício, nova variável ou conexão de banco como parte desta auditoria.

Gate: diferença inesperada bloqueia publicação até revisão. Uma versão privada ou base real jamais pode substituir o serviço demonstrativo.
