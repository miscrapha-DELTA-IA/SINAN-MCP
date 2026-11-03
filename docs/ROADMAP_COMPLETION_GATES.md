# Conclusão do roadmap SINAN MCP — P0 a P6

**Referência: 03/11/2026.** Complementa ROADMAP_IMPLEMENTATION.md e a issue #2. SINAN MCP é projeto independente: localizar documentos oficiais, inspecionar ZIP ou aprovar testes não autentica estatísticas, liberação institucional nem anonimização. Nenhum dado real deve ser exposto no MCP público por padrão.

## Produto-alvo: separar funções e alegações

- **MCP público demonstrativo:** apenas metadados, planos de pesquisa e dados totalmente sintéticos; sem SQLite, PySUS ou entrada administrativa. Não alterar esse serviço sem revisão explícita.
- **Ambiente privado de pesquisa:** instalações locais/institucionais com dados legalmente obtidos, proveniência, dicionários, qualidade, protocolos e auditoria de privacidade. Dados individuais nunca devem ser enviados a este repositório, PR, chat ou MCP público.
- **Extensão futura opcional de publicação:** artefatos estáticos agregados, com aprovação externa por agravo/ano, composição com releases anteriores, rastreabilidade e autorização de implantação separada. A arquitetura não implica que todos os agravos estejam validados.

## Situação verificável atual

- PRs #1, #3 a #9 estão empilhados, em rascunho, sem merge nem deployment da trilha científica na main.
- DENG/2024: ZIP CSV e PDF pesquisados localmente, sem transmitir notificações. PDF recente: 121 entradas, 120 nomes distintos (duplicação COUFINF); cabeçalho anual: 121 nomes; 119 coincidentes literalmente, CLINIC_CHIK documentado no PDF ausente no CSV, CLINC_CHIK e UF no CSV fora do PDF. Semelhança CLINC_CHIK com CLINIC_CHIK é hipótese, não equivalência aprovada. UF não tem significado confirmado no CSV. SHA-256 do ZIP observado localmente não autentica assinatura da autoridade.
- DENG/2024: domínio CLASSI_FIN contraditório entre tabela de categorias 1/2/8 e regras que citam 11/12/13; campos COMPlica e TP_SISTEMA com tipos impressos incorretamente como char()1; estado da distribuição e definição da variável continuam em revisão.
- CHIK/2024: link oficial JSON catalogado, mas esquema anual e semântica não validados. Em JSON, inspeção opcional via ijson pode ler transitoriamente valores de até 64 registros, razão adicional para execução exclusivamente privada.
- TUBE/2024: piloto de metodologia e equidade; recurso anual nacional com edição e checksum da autoridade ainda não confirmado; perda de seguimento e universo populacional não homologados.
- Outros agravos: índice de aliases é referência, não compromisso de dados anuais ou indicadores oficiais.

## P0. Integração controlada dos PRs

**Entregar:** revisão de dependências dos PRs, diff integral, testes Windows/Linux Python 3.11 e 3.12, extras opcionais (PDF/JSON/Pandera/PySUS), protocolos MCP atuais, isolamento entre público e administração, logs seguros e ausência de arquivos privados rastreados.

**Aceite:** integrar a pilha em ordem ou consolidar uma branch técnica aprovada, sem substituir o serviço público sintético, alterar flags de acesso a dados reais ou fazer deploy automático. Aprovação de código != aprovação epidemiológica.

## P1. Fontes/dicionários versionados por agravo e ano

**Entregar:** distribuições autorizadas com URLs e identificadores exatos, edição aplicável, data de corte, integridade, situação preliminar/final comprovada, formatos/transformações e dicionário conferido independentemente. Verificar checksum oficial quando disponibilizado e registrar a falta quando não há.

**Aceite:** cada recurso anual e edição documental passa por revisão, com divergências registradas. DENG/2024: apurar CLINC_CHIK, UF, CLINIC_CHIK, duplicação COUFINF, tipos impressos char()1 e domínio CLASSI_FIN. Nenhuma renomeação automática, nenhuma equivalência por aproximação.

## P2. Ingestão e controle de qualidade

**Entregar:** conectores locais PySUS, DATASUS e TABNET de acesso permitido, host/HTTPS controlados, cache, retries/timeout limitado, checksums, limpeza, logs sem PII. Distinguir registro, pessoa, caso e evento; identificar perdas no processamento, duplicações, missingness, validade de códigos, eixos temporais, outliers e reconciliação independente.

**Aceite:** testes adversariais e concordância explicada com tabelas oficiais de mesma fonte, data de corte, estratos e definições. Igualdade de contagem isolada não prova o correto.

## P3. Indicadores e protocolos específicos

**Entregar:** contrato para cada agravo/ano/indicador com definição de caso, elegibilidade, unidade observacional, eixo temporal, numerador, denominador, fonte externa, versão e revisão. TUBE: critérios de perda de seguimento e validação de equidade por subgrupos e período. DENG: classificação, gravidade, óbito e histórico não devem ser calculados antes de resolver CLASSI_FIN.

**Aceite:** implementação testada com bases sintéticas, seguida de reconciliação e parecer epidemiológico com dados reais em ambiente privado autorizado. Não afirmar suporte universal por haver um alias.

## P4. Governança, base legal e composição

**Entregar:** custódia, papéis de revisor, base legal e fluxo ético/institucional aplicável, minimização, prazo de retenção, retirada, resposta a incidentes, composição histórica entre regiões, anos, dimensões, revisões e releases auxiliares.

**Aceite:** parecer científico independente e de privacidade, verificação real de identidade, decisão institucional e limites de divulgação adequados. Limiar de célula 20, partição 100 e bloqueio por sobreposição são precauções, NÃO garantem anonimização/LGPD.

## P5. Infraestrutura, identidade e observabilidade

**Entregar:** eventual acesso privado remoto atrás de OIDC/OAuth confiável, issuer/audience/scopes, RBAC, TLS, rate limits, quotas, eventos de auditoria sem PII, segredo gerenciado, backups, isolamento, revogação, monitoramento e proteção contra consultas por diferença.

**Aceite:** pentest, carga, integração MCP, cenários negativos de autorização e revogação testados na infraestrutura final. Túnel de saída e hospedagem HTTPS não substituem autorização a dados de saúde.

## P6. Releases multiagravo controlados

**Entregar:** piloto DENG/2024 somente após P1-P5, expansão para CHIK/2024 e TUBE/2024 apenas depois de fontes e protocolos individuais verificados. Cada novo indicador exige novos testes e revisão cumulativa de privacidade; caso contrário responder sem dado validado.

**Aceite:** artefatos revisados, documentação operacional, rollback, monitoramento, testes e autorização explícita de publicação. A liberação real é decisão distinta do merge de código.

## Instrumentação local do roadmap — PR #10

O novo módulo de leitura local sinan_mcp/roadmap_readiness.py organiza as sete frentes, para qualquer alias do catálogo, sem abrir arquivos clínicos. Comandos:

    python -m sinan_mcp preparar-checklist-roadmap --agravo DENG --ano 2024 --resource-id 4cf2f7b8-9920-41b5-817a-1ffc13e0690c --saida ./data/deng-prontidao.json

    python -m sinan_mcp diagnosticar-checklist-roadmap --arquivo ./data/deng-prontidao.json

- O checklist é criado com todas as sete frentes PENDENTE.
- Estados declarativos aceitos: PENDENTE, EVIDENCIA_LOCAL_NAO_VALIDADA e PARECER_EXTERNO_DECLARADO_NAO_AUTENTICADO. Se houver evidência declarada, exige SHA-256 local de documento como referência, sem inserir documento bruto, pessoa, URL privada ou saúde.
- Mesmo se todas as sete forem marcadas com parecer, a saída mantém publicacao_autorizada=false, revisor_externo_autenticado_pelo_sistema=false e acesso_remoto_com_dados_reais_autorizado=false. Não existe comando automático para alterar isso.
- O operador pode preencher a checklist privada de modo responsável no próprio computador, mas não deve enviá-la ao GitHub, ChatGPT ou MCP. Todo parecer requer autenticação/revisão fora do programa.

## Dependências externas insubstituíveis

Confirmação da fonte e versão oficiais; evidência de consolidação; dicionário e regras epidemiológicas aplicáveis; coorte e denominadores; revisão de risco de identificação; instância institucional competente e base legal; identidade institucional e infraestrutura de acesso; testes na infraestrutura final. CI, LLM e hashes locais não conferem essas evidências.

## Definição de pronto, sem confusão

- **Código revisado e integrado**: implementação e testes na base correta, sem implantar dados reais.
- **Dados aptos para pesquisa local determinada**: fonte, ano, dicionário, qualidade, protocolos e autorização de tratamento verificados.
- **Agregados aptos para publicação**: etapa posterior com análise cumulativa de privacidade, pareceres, autorização e infraestrutura revisada.
- **Multiagravo**: cumprimento verificável da sequência acima por agravo/ano/indicador, não uma lista nominal de doenças.
