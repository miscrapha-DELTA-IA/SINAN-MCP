# Publicação da política de privacidade — pendências jurídicas e operacionais

**Escopo:** versão externa **100% sintética** de `sinan_mcp.public_server` no Render. Esta revisão **não** abrange o MCP privado, microdados, SQLite, PySUS ou autorização de resultados epidemiológicos reais.

**Data de elaboração:** 05/11/2026. **Estado:** minuta preparada, **não vigente** até revisão e publicação formal. A versão legível e canônica está em [`sinan_mcp/public_privacy.html`](../sinan_mcp/public_privacy.html); após deploy, será servida em `https://sinan-mcp-public-preview.onrender.com/privacidade` e `/privacy`. Não usar a URL antes de a nova revisão alcançar o Render.

## Exigências para colocar a política em vigor

- [ ] **Identidade do controlador:** confirmar nome civil completo ou razão social da pessoa/entidade que de fato define finalidades e meios do tratamento. O nome de um repositório ou projeto **não** substitui, isoladamente, a identificação exigida pela LGPD.
- [ ] **Canal privado de titular:** confirmar e testar um endereço de e-mail ou outro meio **privado** estável para solicitações de acesso, confirmação, eliminação etc. Nunca convidar a publicar IP, CPF, documentos ou dados de saúde em uma issue pública. Definir quem responde, com autenticação proporcional e registro mínimo.
- [ ] **Encarregado / pequeno porte:** definir se o controlador está sujeito à obrigação de encarregado ou se enquadra, mediante comprovação, em hipótese de dispensa da Resolução CD/ANPD nº 2/2022. Mesmo dispensado, deve manter canal de contato acessível. Não presumir dispensa apenas por ser projeto open source ou plano gratuito.
- [ ] **Base legal:** revisar finalidade de operação do serviço e segurança; se usar legítimo interesse (art. 7º, IX), documentar teste de finalidade, necessidade, expectativas e balanceamento. Não usar legítimo interesse para dados pessoais sensíveis.
- [ ] **Provedor e contrato:** verificar a relação de tratamento e [DPA da Render](https://render.com/dpa), inclusive os suboperadores; verificar alcance do tratamento para a região Oregon/Estados Unidos, se há transferência internacional caracterizada e o mecanismo aplicável (LGPD e Resolução CD/ANPD nº 19/2024). **Não** declarar adesão a cláusulas-padrão ANPD sem lastro contratual.
- [ ] **Retenção:** a [Render documenta 7 dias para logs da conta Hobby](https://render.com/docs/logging). Verificar eventuais logs, backups, dados de plataforma, telemetria e incidentes com regras próprias. Não generalizar a retenção de 7 dias para todas as categorias de dados.
- [ ] **Rota e segurança:** confirmar somente o módulo `sinan_mcp.public_server`, documentação estática sem trackers e sem logs de acesso do Uvicorn; rotas `/mcp`, `/health`, `/privacidade` e `/privacy` sem captura de dados pessoais além da infraestrutura indispensável.
- [ ] **Política sem pendências:** substituir todos os campos `[PENDENTE]`, remover o aviso de minuta, fixar data de vigência e verificar coerência entre texto, código e condições do provedor.
- [ ] **Teste de publicação:** PR revisado + todos os checks obrigatórios, deploy Render **manual** após autorização, verificação HTTPS 200 da página, `Content-Type:text/html`, CSP, nenhuma dependência externa, e smoke do MCP sintético sem regressões.
- [ ] **Fluxo OpenAI:** preencher `privacyPolicyURL` com a URL HTTPS realmente publicada; não declarar aceitação no diretório antes do scanner e aprovação de submissão.

O [registro preliminar de tratamentos e teste de balanceamento](PRIVACY_PROCESSING_REGISTER.md) documenta as operações conhecidas e as avaliações que ainda dependem de assinatura humana.

## Orientação de uso

Até o fechamento dos itens acima, a página é uma **minuta auditável** e não substitui a política de privacidade final de uma publicação ampla. **Não fazer deploy desta revisão como se a política já estivesse formalmente aprovada.** Nenhum dado de paciente deve ser habilitado para tornar o texto válido.

## Referências oficiais

- [Lei nº 13.709/2018, LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm), arts. 6º, 7º, 9º, 18, 33 e 46.
- [ANPD — direitos dos titulares](https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados-1/direito-dos-titulares).
- [ANPD — Resolução nº 2/2022: pequeno porte](https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd/resolucao-cd-anpd-no-2-de-27-de-janeiro-de-2022).
- [ANPD — guia de legítimo interesse](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-lanca-guia-orientativo-sobre-legitimo-interesse).
- [ANPD — Resolução nº 19/2024: transferência internacional](https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd/resolucao-cd-anpd-no-19-de-23-de-agosto-de-2024).
- [ANPD — comunicação de incidentes](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis).
- [OpenAI — plugin guidelines / privacy policy](https://developers.openai.com/plugins/plugin-guidelines).
