# Registro preliminar de tratamento e teste de legítimo interesse — SINAN MCP público

**Versão:** 2026-11-05. **Situação:** análise preparatória; **não** é aprovação do controlador, parecer jurídico ou homologação da ANPD. Controlador identificado e contato LGPD autorizado em 05/11/2026; contratos, transferências internacionais e governança permanecem em revisão. Abrange **somente** `sinan_mcp.public_server` em instância Render pública com dados sintéticos. Não utilizar este documento para justificar publicação de dados SINAN reais.

## 1. Inventário de tratamentos (LGPD, art. 37)

| Atividade | Dados ou categorias | Finalidade | Base legal candidata | Destinatário/operador | Retenção / condicionantes |
| --- | --- | --- | --- | --- | --- |
| Solicitações MCP anônimas | `termo`, `codigo_interno`, `agravo` e filtros restritos, dados enviados intencionalmente pelo cliente | Responder com catálogo estático e simulação sintética | Confirmar fundamento jurídico do tratamento técnico antes de publicar | Aplicação SINAN MCP na Render; cliente MCP separado | Processamento transitório; código não grava histórico nominal; dados enviados indevidamente podem aparecer em camadas externas |
| Infraestrutura/rede e disponibilidade | Possível IP, timestamp, Host, Origin, User-Agent, caminho, status e identificadores técnicos | Entrega do serviço, segurança, diagnóstico e prevenção de abuso | Art. 7º, IX — legítimo interesse **sujeito ao teste documentado**; art. 7º, II quando obrigação legal concreta | Render e suboperadores, conforme contrato e DPA | Logs acessíveis na Render Hobby: documentação de **7 dias**; outros registros/categorias precisam ser contratualmente avaliados |
| Controle de admissão | Contadores agregados em memória de chamadas aceitas/recusadas e concorrência, sem IP por cliente | Restringir saturação do serviço e registrar métricas agregadas | Não são necessariamente dados pessoais no fluxo atual; revisar se forem correlacionáveis a pessoas | Aplicação SINAN MCP | Memória volátil, reset em reinício; resumo de contadores nos logs de aplicação |
| Suporte e direitos LGPD | Identificador e conteúdo mínimo do pedido enviados ao canal privado **miscrapha@gmail.com**, autorizado para divulgação pelo controlador | Exercer direitos, responder ao titular e documentar providências | Obrigação legal, quando aplicável (art. 7º, II) | Operador/contato confirmado | Prazo fundamentado na necessidade do atendimento, deveres legais e registros; ainda **não definido** |
| Auditoria e incidentes | Informações mínimas e sanitizadas sobre eventos técnicos | Investigar falhas e cumprir obrigação aplicável de comunicação | Segurança e obrigação legal, conforme o evento | Operador, Render, ANPD/titulares quando exigido | Registrar incidentes nos prazos aplicáveis; prazo legal para registro de incidente com dados pessoais pode diferir de logs comuns |

**Não há coleta deliberada** de nome, CPF, credencial, cadastro, prontuário, diagnóstico pessoal, ficha de notificação ou dado financeiro no MCP externo. **Não** interpretar a base sintética como dado anonimizado de paciente: ela foi criada artificialmente e não veio de pessoas reais.

## 2. Teste preliminar de legítimo interesse (art. 7º, IX)

### Finalidade e expectativa legítima
Disponibilizar um serviço técnico público e permitir seu uso básico sem cadastro exige roteamento de rede e algumas medidas antifraude/antissaturação da infraestrutura. O titular pode razoavelmente esperar o processamento de metadados técnicos estritamente necessários à conexão e à proteção do serviço.

### Necessidade
A aplicação não usa identificação por IP no limitador; utiliza um orçamento de 300 solicitações MCP/minuto e 16 chamadas simultâneas **globais por processo**. O Uvicorn foi configurado com `access_log=False`. Essas medidas reduzem a coleta deliberada. O provedor pode tratar metadados por motivos próprios de funcionamento, segurança e contratos; a relação de tratamento requer revisão adicional. Não usar os dados para marketing, publicidade ou perfilamento.

### Balanceamento, riscos e mitigadores
- **Risco de vinculação:** endereço IP e horários podem identificar uma pessoa. Mitigar acesso aos logs por princípio de necessidade, retenção documentada e ausência de cópias em sistemas externos não aprovados.
- **Entrada sensível não solicitada:** um usuário pode digitar conteúdo clínico pessoal no campo de pesquisa. Desencorajar explicitamente na política e nos prompts; manter campos restritos; não armazenar payloads na aplicação; inspecionar logging de exceções sem divulgar os textos.
- **Dados em outro país:** a infraestrutura Render está na região Oregon (EUA). Mapear os papéis dos agentes e avaliar se há transferência internacional caracterizada, à luz da Resolução CD/ANPD nº 19/2024; a existência de um DPA não substitui a avaliação nem prova uma cláusula ANPD incorporada.
- **Acesso e indisponibilidade:** controles por processo não substituem WAF por origem; manter monitoramento e resposta a incidentes sem armazenar IP individual em issue pública.
- **Direitos dos titulares:** um canal privado, estável e acessível para solicitação é indispensável; um repositório GitHub público não basta.

### Conclusão **condicional**
A hipótese de legítimo interesse para os **dados pessoais comuns mínimos de operação e segurança** é plausível somente se o controlador comprovar o interesse concreto, a necessidade, a ausência de alternativa menos intrusiva, as salvaguardas e o respeito aos direitos/expectativas dos titulares. **A identidade e o e-mail de contato foram expressamente autorizados pelo responsável em 05/11/2026; isso não constitui assinatura de aprovação da avaliação de legítimo interesse.** Não usar a hipótese para dados pessoais sensíveis ou para finalidades novas.

## 3. Transferência internacional e fornecedores

**Fato confirmado:** servidor público na Render, região Oregon (EUA), com seus serviços de hospedagem e DPA documental publicado em https://render.com/dpa. **Não confirmado:** a vinculação contratual de cláusulas apropriadas à conta, lista efetiva de suboperadores para cada fluxo, países de eventuais subprocessamentos e enquadramento jurídico completo segundo a Resolução ANPD 19/2024. Coleta direta no exterior e transferência internacional de dados não devem ser confundidas: a caracterização exige análise do fluxo concreto.

## 4. Parecer humano necessário

- [x] Controlador indicado: **Raphael Múcio Teixeira Cabral de Pina Bulhões Di Giorgio**, pessoa natural, com autorização expressa para identificação pública.
- [x] Canal privado definido e autorizado para divulgação: **miscrapha@gmail.com**. [ ] Confirmar recebimento de mensagem de teste externa e documentar procedimento de resposta/validação proporcional.
- [ ] Avaliação de pequeno porte/encarregado documentada, sem presunção.
- [ ] Legitimate Interest Assessment validada/assinada e associada aos tratamentos realmente realizados.
- [ ] DPA e eventual transferência internacional/suboperadores avaliados por documentação da conta Render.
- [ ] Retenção efetiva para classes de dados do provedor e possíveis backups mapeada; prazo para pedidos e incidentes aprovado.
- [x] Política HTML com controlador e e-mail preenchidos, sem campos `[PENDENTE]`. [ ] Confirmar implantação por HTTPS e data de início efetivo da vigência.

## Fontes
[LGPD (Lei 13.709/2018)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm) · [ANPD guia de legítimo interesse](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-lanca-guia-orientativo-sobre-legitimo-interesse) · [ANPD Resolução nº 19/2024](https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd/resolucao-cd-anpd-no-19-de-23-de-agosto-de-2024) · [ANPD Resolução nº 2/2022](https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd/resolucao-cd-anpd-no-2-de-27-de-janeiro-de-2022) · [Render logging](https://render.com/docs/logging).
