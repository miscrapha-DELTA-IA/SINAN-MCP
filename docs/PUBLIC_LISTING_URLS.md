# Endereços públicos para uma futura submissão do MCP

**Escopo:** instância externa **somente sintética**, sem registros reais de notificações, sem login, sem arquivos enviados, sem banco de dados de pacientes. Documento preparado em 05/11/2026; URLs só devem ser marcadas **verificadas** após um deploy autorizado e uma sonda HTTPS de produção bem-sucedida.

| Campo exigido (MCP) | URL HTTPS prevista | Estado |
| --- | --- | --- |
| `websiteURL` | https://sinan-mcp-public-preview.onrender.com/sobre | Implementado em código, verificar HTTPS depois do deploy |
| `supportURL` | https://sinan-mcp-public-preview.onrender.com/suporte | Implementado em código, verificar HTTPS depois do deploy |
| `privacyPolicyURL` | https://sinan-mcp-public-preview.onrender.com/privacidade | Já publicado e verificado anteriormente |
| `termsOfServiceURL` | https://sinan-mcp-public-preview.onrender.com/termos | Implementado em código, verificar HTTPS depois do deploy |

**Alias legíveis:** `/about`, `/support`, `/terms`, `/privacy`. O vínculo deve usar a URL HTTPS completa, sem token nem credenciais embutidas. O endereço de `/mcp` não deve ser confundido com o site informativo. O plano Render Free está sujeito a suspensão por inatividade.

## Contato, limites e direitos

- Controlador da política LGPD: Raphael Múcio Teixeira Cabral de Pina Bulhões Di Giorgio (pessoa natural), conforme autorização expressa.
- Contato já divulgado e autorizado: **miscrapha@gmail.com**. O mesmo contato aparece no suporte. Não solicitar dados sensíveis em formulário público ou issues.
- Aviso de ausência de vínculo com Ministério da Saúde, DATASUS, SINAN e OpenAI; dados epidemiológicos de exemplo são integralmente fictícios.
- Licença MIT para código-fonte, sem transferir automaticamente direitos sobre marcas ou conteúdo externo. Termos do serviço preservam direitos irrenunciáveis reconhecidos pela legislação brasileira.
- Os documentos são transparência do protótipo e **não** substituem avaliação jurídica final, exame das transferências internacionais, eventual enquadramento de encarregado, análise de incidentes e diligência contratual.

## Bloqueio específico do diretório: não basta a existência das URLs

As [diretrizes vigentes do diretório](https://developers.openai.com/plugins/plugin-guidelines) indicam expressamente que **plugins somente de demonstração ou teste não são aceitos**. Embora os 14 agravos tenham um catálogo de referências, somente o exemplo de TUBE/2024/PI oferece contagens **fictícias**; isso é insuficiente para afirmar que a candidatura já satisfaz a qualidade/utilidade exigida.

**Próxima prova de valor sem dados clínicos:** definir casos de uso de utilidade independente das simulações, desenvolver referência documental verificável com proveniência e testes reais de experiência, sem afirmar que a ferramenta consulta notificações do SINAN. É necessária avaliação explícita do portal e da política atual antes de qualquer submissão. Nenhum teste técnico ou conteúdo jurídico garante aprovação.

## Etapas de implantação

1. Revisar PR e obter CI verde para as páginas; confirmar identidade, Host/Origin, `python -m sinan_mcp.public_server` e ausência de integração com banco.
2. Fazer **deploy manual** da `main` no serviço Render sintético após os checks; não habilitar autoDeploy.
3. Verificar por sonda HTTPS as seis rotas de novas páginas em PT/EN, links cruzados, content-type, CSP, headers `no-store` e `nosniff`, e, sem regressão, `/health`, MCP `tools/list` e a política LGPD.
4. Só então marcar os URLs como publicados e atualizar a [issue #51](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/issues/51).
5. Posteriormente validar o processo de suporte por e-mail; nenhuma ferramenta pode comprovar entrega de mensagens reais sem teste da caixa de entrada.

**Fontes:** [OpenAI — Submission](https://developers.openai.com/plugins/deploy/submission); [OpenAI — Plugin Guidelines](https://developers.openai.com/plugins/plugin-guidelines); [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm); [Marco Civil da Internet](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm); [CDC](https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm).
