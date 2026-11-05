# Render — checklist de auditoria somente leitura

Estado: workspace confirmado pelo usuário e inspeção da configuração acessível concluída em 2026-11-04. Os dados do manifesto de Git não substituem a configuração efetiva do serviço; itens não verificáveis permanecem explicitamente pendentes.

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

Observação de compatibilidade: a versão proposta é Python 3.11.17, declarada em .python-version e no Blueprint; no serviço real, PYTHON_VERSION do ambiente tem precedência e deve ser conferida sem revelar valores secretos. Não instalar um lockfile gerado para Python 3.11 em um Python padrão 3.14.

## Evidências da auditoria de leitura — 2026-11-04

Workspace confirmado pelo operador: **My Workspace**. Serviço inspecionado: `sinan-mcp-public-preview` (`srv-dbkdt4g8v5cc73f33cfg`). Nenhuma configuração foi alterada.

| Propriedade observada na API Render | Valor |
| --- | --- |
| Serviço | Web service, plano Free, região Oregon |
| URL do serviço | https://sinan-mcp-public-preview.onrender.com |
| Repositório e branch | miscrapha-DELTA-IA/SINAN-MCP, main |
| autoDeploy efetivo | no |
| Comando de inicialização | python -m sinan_mcp.public_server |
| Comando efetivo de build | python -m pip install -e . (ainda sem lockfile) |
| Health check dedicado | vazio; /health não configurado como healthCheckPath |
| Instâncias informadas | 1 |
| Política IP no serviço | 0.0.0.0/0, pública |
| Commit implantado | 678e15523bb13ec2f36778ffe879c479dff2b3bf |
| Último deploy | dep-dbkgj9o8v5cc73eulii0, status live, finalizado em 2026-11-02T22:08:27Z |
| Deploys listados | 2: o anterior foi desativado |
| Tipos de logs retornados no período consultado | app; não assumir ausência de logs ou tráfego adicionais |
| Métricas consultadas para período de novembro | nenhuma série retornada; isso NÃO significa tráfego zero |

**Não verificado:** nomes e conteúdo das variáveis de ambiente em produção, anexos externos de banco/disco ou caminhos privados, status real de alertas, política de retenção, limites de edge por origem, controles DNS/TLS, versão efetiva de Python no runtime e comportamento HTTPS atual por chamadas MCP reais. A leitura API disponível não dá cobertura suficiente desses controles.

**Gates de implantação futura:** (a) confirmar, pela interface autorizada, que não há banco ou segredos de pesquisa e que o runtime usa Python 3.11.17; (b) configurar healthCheckPath como /health e estabelecer alertas e retenção; (c) manter autoDeploy desativado e o comando de servidor público sintético; (d) só após revisão do diff e CI, executar um deploy manual autorizado; (e) rodar a sonda HTTP após o deploy e, em falha, reverter manualmente ao SHA sintético anterior. Não confundir revisão de repositório, deploy e aprovação institucional.

## Implantação e sonda HTTPS pós-deploy — 2026-11-04

A tabela anterior registra uma **fotografia anterior à implantação** e não descreve a configuração atual. Inspeção do serviço e logs/eventos Render concluída novamente após atualização.

| Verificação de produção | Evidência observada |
| --- | --- |
| Serviço e workspace | `sinan-mcp-public-preview` em `My Workspace`; id `srv-dbkdt4g8v5cc73f33cfg` |
| SHA Live | `3ac1db9dd4bb81b3bf685356528da4572c4f0c3d` |
| Deploy | `dep-dblj5kon74is73a9idj0`, concluído em `2026-11-04T13:28:50Z` como `Live` |
| Build | `python -m pip install --require-hashes --no-deps -r requirements-public.lock && python -m pip install --no-deps -e .`; build concluído |
| Start | `python -m sinan_mcp.public_server`; startup do Uvicorn concluído |
| Health check | `/health` salvo na configuração efetiva; HTTPS `/health` validado |
| AutoDeploy | `no`, preservado; o deploy foi acionado manualmente |
| Proteção de branch | `SINAN-MCP-Main-Protection` ativo com oito checks obrigatórios |
| Validação HTTPS | [GitHub Actions run 41805947076, tentativa 2](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/actions/runs/41805947076), job `126603928099`, sucesso após a implantação |
| Contrato validado | Initialize; dez tools sem escrita; `listar_bases` sem dados reais; 120 registros fictícios TUBE/2024/PI; rejeição de operações administrativas e Origin não autorizado |
| Rollback de referência | SHA `678e15523bb13ec2f36778ffe879c479dff2b3bf` (revisão sintética anterior) |

**Sem atestado administrativo:** nomes/valores completos de variáveis e environment groups, efetiva vinculação ou ausência de discos/bancos, controle de acesso a dados externos, retenção/logs em provedor, alertas, proteção por origem na borda, e validação institucional de fontes reais. Não se deve declarar esses controles como auditados.

A action [Public HTTPS MCP smoke](../../.github/workflows/public-live-smoke.yml) executa uma sondagem periódica somente leitura (06h17/18h17 BRT, melhor esforço). A sonda não monitora diretamente versões/SHAs da Render nem substitui uma revisão humana. Ver [issue #43](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/issues/43).

## Verificação local adicional de variáveis, grupos e secret files — somente leitura

O conector Render atualmente disponível **não** possui método de listagem de env vars/arquivos secretos/env groups. O serviço já foi testado como estritamente sintético, mas isso não certifica o seu ambiente. A API oficial disponibiliza endpoints de leitura para as variáveis diretamente configuradas, secret files e grupos ligados. **Alguns retornam valores sensíveis**; nunca copiar respostas API, executar chamadas com output verboso ou colar tokens no chat.

Para executar localmente em Windows, após atualizar seu clone da branch `main`:

```powershell
py -3.11 scripts/audit_render_public_environment.py
```

O script solicita a chave de API **sem exibir o texto**, caso `RENDER_API_KEY` não esteja definida, e realiza somente chamadas GET para o serviço esperado. Prefira uma chave escopada exclusivamente para leitura se disponível; **nunca** armazene a chave no repositório, nos workflows CI, em mensagens ou em arquivo de configuração. Revogue uma chave temporária após a auditoria. Não há upload de relatório nem impressão de valores.

O script emite exclusivamente `PASS`, `FAIL` ou `REVIEW` em categorias predefinidas, sem nomes de variáveis não permitidas, nome ou conteúdo de secret file, nome de env group ou corpo de erro HTTP. Falha de API ou paginação incompleta bloqueiam a certificação. `REVIEW` indica verificação humana pendente, e **não** ausência de problema.

As verificações incluem isolamento do serviço correto, `autoDeploy=no`, `healthCheckPath=/health`, build com hashes, comando sintético, versão Python 3.11.17, flag de dados reais desligada, hostname autorizado, limites conservadores, **zero arquivos secretos diretos e zero grupos vinculados**. Variáveis inesperadas exigem revisão sem revelar seus nomes; listas de grupos vinculados devem estar vazias, já que poderiam fornecer segredos por herança. APIs de configuração não demonstram qual código foi de fato executado — correlacionar sempre com o SHA Live e a sonda HTTPS pós-deploy.

**Não checado pelo script:** existência de credenciais em sistemas externos, retenção e conteúdo dos logs de proxy, destinos reais de email/Slack, regras avançadas de proteção na borda e homologação epidemiológica. São etapas separadas do [issue #43](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/issues/43).

Referências oficiais da Render: [env vars do serviço](https://api-docs.render.com/reference/get-env-vars-for-service), [secret files do serviço](https://api-docs.render.com/reference/list-secret-files-for-service), [environment groups](https://api-docs.render.com/reference/list-env-groups), [notificações](https://render.com/docs/notifications).

## Formatos da API de environment groups e evidência do operador — 2026-11-05

A referência oficial `GET /v1/env-groups` documenta objetos com `ownerId` e `serviceLinks` (lista de vínculos por ID): https://api-docs.render.com/reference/list-env-groups . Algumas respostas de paginação podem conter itens `{"envGroup": {...}, "cursor": "..."}`; o auditor local reconhece ambas as estruturas, sem reportar nomes, valores de grupos ou conteúdo de arquivos secretos. A rotina verifica a propriedade do workspace selecionado e cada ID de `serviceLinks`. Quando não consegue validar a estrutura ou o proprietário, registra `REVIEW`, **nunca `PASS` automático**. Um vínculo do serviço efetivamente encontrado permanece `FAIL`.

O operador confirmou a seção `Linked Environment Groups` vazia no painel do serviço. A auditoria anterior retornou `REVIEW` para metadados; esta alteração é **correção do verificador local**, não alteração da Render. Rodar a versão atualizada do script somente leitura e examinar apenas estados `PASS/FAIL/REVIEW`; a não publicação de valores de ambiente continua obrigatória.

Mesmo `PASS` para ausência de grupos não significa autorização de dados SINAN reais, nem certifica bancos externos ou logs de terceiros.
