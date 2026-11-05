# Hardening de repositório e branch main

## Alterações versionadas no PR
- Workflows com permissions.contents=read e actions fixadas em commits imutáveis verificados da origem.
- Dependabot semanal para Python e GitHub Actions cria pull requests; não tem permissão de publicação no Render.
- CI para Windows/Ubuntu e Python 3.11/3.12, contrato sintético, PySUS opcional e auditoria da cadeia pública.
- Nenhum workflow usa evento pull_request_target para executar código não confiável ou tem credenciais de microdados.

## Configurações administrativas ainda pendentes
A consulta aos rulesets retornou vazio e a leitura de proteção clássica recebeu 403 da integração. Portanto, NÃO está comprovada proteção de main.

Passos no GitHub: Settings > Rules > Rulesets; criar regra específica para main, inicialmente em modo de avaliação se disponível; bloquear force-push/deleção; exigir pull request antes de alteração e exigir verificações de CI de Windows/Ubuntu, auditoria de dependências e contrato sintético.

Revisão humana independente é recomendada para mudanças de servidor público, manifestos, dependências e infraestrutura. Se existir apenas um mantenedor, não habilitar uma regra impossível de satisfazer sem incluir outro revisor autorizado. Não permitir bypass permanente de bots; manter procedimento documentado de emergência.

Ativar secret scanning, push protection, alertas de dependências e controles de colaboradores onde disponíveis. Não colocar tokens, hashes de dados sensíveis ou arquivos privados nos relatórios dos Actions.

## Gate de alteração
Todo PR deve apresentar: diff revisado, testes verdes no mesmo SHA, ausência de novas interfaces a dados reais, versão de dependências e riscos. Merge na main NÃO equivale a deploy; a Render deve permanecer autoDeploy=false e ser analisada separadamente.
