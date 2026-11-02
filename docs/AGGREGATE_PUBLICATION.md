# Publicação responsável de agregados reais — SINAN MCP

**Estado:** implementação técnica da etapa de geração/revisão. Nenhum agregado real foi publicado automaticamente. O serviço Render atual continua **100% sintético**.

Os registros individuais já divulgados pelo Ministério da Saúde para uso local não são equivalentes a uma autorização para criar uma API irrestrita. A ANPD destaca que anonimização e acesso devem ser analisados pelo risco contextual de reidentificação. Este projeto **não declara que sua regra de contagem mínima é anonimização formal**.

Referências:
- [Ministério da Saúde — Dados sobre agravos de notificação](https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/svsa/agravos-de-notificacoes/agravos-de-notificacoes)
- [ANPD — Tratamento de dados pessoais para fins acadêmicos e estudos e pesquisas](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-orientativo-tratamento-de-dados-pessoais-para-fins-academicos-e-para-a-realizacao-de-estudos-e-pesquisas)
- [CNS 738/2024 — Uso de bancos de dados para pesquisa](https://bvsms.saude.gov.br/bvs/saudelegis/cns/2025/res_0738_22_01_2025.html)

## Camadas distintas

```text
[DATASUS/PySUS: microdados locais]
       |  READ-ONLY, nenhuma chamada MCP
       v
[preparar-agregado: candidato privado no data/ ignorado pelo Git]
       |  validação científica + risco de divulgação + pareceres independentes
       |  SEM liberação automática
       v
[artefato aprovado separado, JSON fixo + SHA-256 travado]
       |  ONLY after explicit deployment choice
       v
[sinan_mcp.approved_server: MCP público sem SQLite/PySUS]
```

**IMPORTANTE:** O serviço `sinan_mcp.public_server` em `sinan-mcp-public-preview.onrender.com` **não foi alterado** nem tem acesso ao gerador de agregados ou a SQLite.

## 1. Produzir um candidato local (nunca público)

Em Windows PowerShell, depois de atualizar o clone e executar os testes:

```powershell
cd "$HOME\Downloads\SINAN-MCP-GitHub"
git pull origin main
py -3.11 -m pip install -e ".[dev,ingest]"
py -3.11 -m pytest -q

# Exemplo de candidato específico para arquivo TUBE 2024 / PI, por raça/cor
py -3.11 -m sinan_mcp --db ".\data\sinan.sqlite3" preparar-agregado --agravo TUBE --ano 2024 --uf PI --por raca_cor
```

**Se qualquer grupo presente tiver menos de 20 registros, ou a partição tiver menos de 100, o comando recusa toda a tabela sem revelar contagens pequenas.** Não bypassar esta regra para publicar resultados. O limiar é um bloqueio conservador inicial, não uma prova de proteção suficiente.

O arquivo fica em `data/review-packages/<agravo>-<ano>-<uf>-<dimensao>-<digest>.candidate.json`. Ele contém apenas contagens candidatas, nunca identificadores ou linhas individuais, mas **ainda deve ser tratado como privado** até revisão. `data/` já está no `.gitignore`. O comando não faz `git add`, `git push`, upload ou chamada ao MCP.

A versão inicial intencionalmente permite **uma única UF, um único ano de ARQUIVO, uma única dimensão (`sexo` OU `raca_cor`) e apenas contagem demográfica**. Não suporta município, cruzamento de raça com sexo, idade, datas, situação de encerramento nem taxa de abandono; isso requer análise separada de ataque por diferença.

## 2. Revisão humana antes da publicação

O gerador produce `stage = UNAPPROVED_RESEARCH_CANDIDATE`. Um avaliador não pode concluir que o pacote é anônimo apenas porque passou pelo código.

O responsável científico deve verificar: dicionário do agravo e ano, versão dos dados (preliminar/final), procedência do arquivo, interpretação de `ano_do_arquivo`, completude dos atributos, duplicações, categorias e comparações com tabulações oficiais.

A revisão de privacidade deve examinar: usos pretendidos, relação com TODAS as tabelas e versões já publicadas, valores indiretos recuperáveis por diferença, risco de combinação com outras bases, política de retenção, integridade, supervisão institucional e processo de contestação/retirada.

**O estado `desconhecido` da fonte bloqueia a validação de um pacote aprovado.** Não é permitido trocar o rótulo para `final` sem comprovação independente da versão original do arquivo.

Para gerar um artefato aprovado, operadores responsáveis devem elaborar manualmente um JSON com os campos exatos:

```json
{
  "stage": "APPROVED_PUBLIC_AGGREGATE",
  "candidate": "<OBJETO candidate original, inalterado>",
  "candidate_sha256": "<SHA-256 do JSON canônico do candidate>",
  "review": {
    "privacy_reviewer": "<revisor independente de privacidade>",
    "scientific_reviewer": "<revisor científico distinto>",
    "review_reference": "<referência institucional ao parecer existente>",
    "publication_authorized": true,
    "cross_release_comparison_reviewed": true
  }
}
```

Os valores entre `<...>` são indicações para preenchimento humano, **não um JSON implantável**. Esses campos registram uma declaração de avaliação; o software **não verifica** a identidade ou a efetividade do parecer. O responsável deve preservar o parecer fora do repositório público.

Obter o SHA-256 do arquivo aprovado:

```powershell
(Get-FileHash -Algorithm SHA256 ".\data\review-packages\arquivo-aprovado.json").Hash.ToLowerInvariant()
```

Verificar a estrutura sem publicar:

```powershell
py -3.11 -m sinan_mcp validar-pacote-aprovado ".\data\review-packages\arquivo-aprovado.json" --sha256 "<sha256-completo>"
```

O verificador exige dois revisores distintos, parecer, permissão de divulgação, análise de interações entre publicações, status de fonte `final`, SHA-256 do pacote **e** do candidato, nenhuma coluna adicional e células de contagem maiores/iguais a 20. Tais verificações **não substituem** avaliação legal, científica e de privacidade.

## 3. Servidor de agregados APROVADOS — separado

O servidor alternativo `sinan_mcp.approved_server` só inicia com:

- `SINAN_APPROVED_RELEASE_FILE` apontando ao JSON aprovado;
- `SINAN_APPROVED_RELEASE_SHA256` com SHA-256 exato dos bytes;
- `SINAN_PUBLIC_HOST` ou `RENDER_EXTERNAL_HOSTNAME` válido.

Ele expõe somente `sobre_o_servidor`, `listar_agregados` e `consultar_agregado`, sem SQL, filtros flexíveis, microdados ou importações. **Não executar/publicar esse servidor antes dos pareceres e da conferência de segurança.** Implantação e compartilhamento são operações distintas e exigem nova autorização explícita. Não substituir a instância sintética atual.

## 4. Riscos ainda não resolvidos

- `K_MIN=20` e `PARTITION_MIN=100` são conservadores, mas não constituem privacidade diferencial nem garantia de anonimização.
- Adições/correções de um mesmo arquivo, anos diferentes, publicações externas, fontes auxiliares e outras dimensões podem permitir inferências. O código não mede sozinho esse risco.
- O modelo atual usa **ano do arquivo**, não coorte de diagnóstico. Não reportar incidência, cobertura, risco de perda de seguimento ou taxas oficiais.
- Não existem mecanismos de autenticação e perfil institucional para acesso a microdados, nem parecer CEP/Conep, quando aplicável.
- A revisão humana deve confirmar legalidade e adequação ao contexto de pesquisa; controles automáticos não substituem essa decisão.

## 5. Etapas científicas posteriores

Após validação da origem e do dicionário SINAN-TB por ano, podem ser definidos indicadores oficiais de coorte, com regras de desfecho, tipo de entrada e deduplicação. Isso ocorrerá num módulo *separado*, validado contra tabulações de referência e revisado antes da publicação.

A publicação pública de agregados reais deve conter metadados precisos e resultados auditáveis — jamais registros individuais.
