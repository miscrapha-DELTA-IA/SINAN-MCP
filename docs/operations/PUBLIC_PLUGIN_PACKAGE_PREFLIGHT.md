# Pacote portátil de pré-submissão — SINAN Lab Independente

**Estado em 05/11/2026:** pacote de **pré-validação técnica**, **não elegível ou aprovado para envio à revisão do diretório**. É uma preparação da versão pública estritamente sintética. O serviço privado de pesquisa, microdados SINAN, fluxos locais/SQLite/PySUS e qualquer dado clínico real **não fazem parte** deste pacote.

## Identidade e conteúdo

- Nome técnico imutável para este rascunho: `sinan-reference-lab`; versão inicial do pacote `0.1.0` (independente de `sinan_mcp.PUBLIC_VERSION`). Nome visual provisório: **SINAN Lab Independente**. Este nome e a categoria do portal precisam de revisão antes de uma candidatura pública; o nome não indica vínculo governamental.
- Responsável pessoa natural e contato publicamente autorizados: **Raphael Múcio Teixeira Cabral de Pina Bulhões Di Giorgio**, **miscrapha@gmail.com**.
- Configuração `plugin-package/plugin.json` segue o formato raiz Agent Plugins 1.0.0 e coloca os campos `interface`, `review` e `publication` em `extensions.com.openai`.
- `plugin-package/mcp.json` contém exatamente um servidor HTTPS remoto `streamable-http`, `sinan-reference`, configurado com `extensions.com.openai.auth.type=none`. Isso é válido **apenas porque** o serviço público não tem autenticação nem estado por usuário, escrita, prontuário ou base real.
- Imagem SVG vetorial original: `plugin-package/assets/icon.svg`, usada por `logo` e `composerIcon`; não utiliza brasão, logomarca oficial, marca OpenAI nem recurso externo.
- Os quatro links do usuário já foram verificados por HTTPS: [sobre](https://sinan-mcp-public-preview.onrender.com/sobre), [suporte](https://sinan-mcp-public-preview.onrender.com/suporte), [política LGPD](https://sinan-mcp-public-preview.onrender.com/privacidade), [termos](https://sinan-mcp-public-preview.onrender.com/termos). O MCP é [`/mcp`](https://sinan-mcp-public-preview.onrender.com/mcp), diferente de um site aberto no navegador.
- Há **5 casos positivos e 3 negativos** de revisão na configuração, baseados no contrato sintético. São **roteiros de revisão**, não prova de execução através do cliente ChatGPT em todas as superfícies.

## Como construir com segurança

Da raiz do repositório no PowerShell 5.1, com Python 3.11:

```powershell
py -3.11 scripts/build_public_plugin_zip.py --check
py -3.11 scripts/build_public_plugin_zip.py --out dist/sinan-reference-lab-preflight-0.1.0.zip
```

O ZIP resultante terá **somente**:
```text
plugin.json
mcp.json
assets/icon.svg
```

Não contém bancos, pacientes, arquivos de pesquisa, segredos, dados locais, scripts executáveis, aplicações `.app.json`, `.mcp.json`, hooks ou skills. O script usa apenas Python padrão, não faz chamadas de rede e produz hashes SHA-256 e bytes reproduzíveis; `--check` não escreve nada. O workflow [Agent Plugin ZIP preflight](../.github/workflows/plugin-package-preflight.yml) executa a validação e disponibiliza o ZIP como **artefato temporário de CI, por sete dias**. Esse artefato é para análise humana, não publicação automática.

## Portões obrigatórios que ainda faltam

- [x] Contrato independente do MCP sintético, ferramentas somente leitura, anotações explícitas e smoke HTTPS.
- [x] Quatro URLs públicas HTTPS; identidade e canal privado divulgados com autorização.
- [x] Dois manifestos raiz no formato portátil correto e ícone original, com lint estrito offline e testes sintéticos.
- [x] Cinco cenários positivos e três negativos **documentados** como candidatos.
- [ ] Testar os oito casos no cliente ChatGPT/Codex e registrar resultados para a equipe de revisão (somente dados fictícios). Não confundir com a suíte unitária do servidor.
- [ ] Criar **vídeo de demonstração real**, hospedar URL acessível à equipe de revisão e atualizar `review.demo_recording_url`. Não inventar o link nem tratá-lo como entregue.
- [ ] Selecionar no portal a **organização/projeto** com as permissões adequadas e concluir a **verificação da identidade de publisher**. A string `developerName` não comprova verificação.
- [ ] Obter do portal o token de desafio de domínio. Disponibilizar somente a string exata em `/.well-known/openai-apps-challenge` no hostname permitido, **sem gerar token falso**. Se o hostname compartilhado `.onrender.com` não permitir a verificação, avaliar com o proprietário um domínio próprio e ajustar Host/Origin e os quatro URLs em uma release específica. **Não criar ou modificar DNS sem autorização.**
- [ ] Executar **scanner oficial de ferramentas** e corrigir achados no portal, inclusive justificativas de anotações, sem mudar limites clínicos.
- [ ] Demonstrar **finalidade independente e valor não demonstrativo**. As [diretrizes OpenAI](https://developers.openai.com/plugins/plugin-guidelines) excluem plugins apenas de teste ou demonstração. O estado atual é deliberadamente `Research Alpha`, 14 agravos em catálogo documental e somente 120 registros fictícios de TUBE/2024/PI. Quatro URLs e um ZIP não substituem a utilidade e confiabilidade científica necessárias para publicação.
- [ ] Completar avaliação jurídica e segurança pendente (LGPD, transferências internacionais, monitoramento, suporte privado e disponibilidade). O plano Free pode suspender o servidor por inatividade.
- [ ] Só após resolver essas pendências: revisar textos e ícone, obter permissão para upload, escanear, preencher vídeo e credenciais (nenhum login na versão pública), pedir revisão e aguardar aprovação editorial.

## Referências verificadas

- [OpenAI — empacotar plugin portátil, MCP remoto, autenticação](https://developers.openai.com/plugins/build/plugins).
- [OpenAI — upload, manifestos, casos 5+3, vídeo e domínio](https://developers.openai.com/plugins/deploy/submission).
- [OpenAI — regras de qualidade e rejeição de demonstrações](https://developers.openai.com/plugins/plugin-guidelines).
- [OpenAI — erros do portal e limites do ZIP](https://developers.openai.com/plugins/deploy/submission-errors).
- [Contrato de software](public-mcp-contract-v1.json) e [anotações de ferramentas](PUBLIC_TOOL_ANNOTATIONS.md).
