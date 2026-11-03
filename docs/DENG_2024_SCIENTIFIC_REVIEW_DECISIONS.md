# DENG/2024 — decisões científicas antes da auditoria de valores (NÃO HOMOLOGADO)

**Estado: CANDIDATO DOCUMENTAL.** Este documento NÃO é parecer do Ministério da Saúde, não confere a identidade de revisores, não autentica a exportação DENG/2024, não permite acesso a microdados, não aprova indicadores ou divulgação. Elaborado para submeter hipóteses explícitas a epidemiologistas, custodiantes e especialistas em privacidade.

## Evidências públicas verificáveis e seu alcance

1. **Nota Informativa nº 59/2016 CGPNCD/DEVIT/SVS/MS**, SINAN online versão 3.0 (3 de maio de 2016), página 2, seção 2.5: campo "62-Classificação" com categorias **5 – Descartado, 10 – Dengue, 11 – Dengue com sinais de alarme, 12 – Dengue grave, 13 – Chikungunya**. Seção 2.6 define o campo "64 – Apresentação Clínica" como exclusivo para chikungunya e condicionado à classificação. Seção 2.7 define campos 68–71 para gravidade dengue. **Link oficial:** https://portalsinan.saude.gov.br/images/documentos/Agravos/Dengue/Nota_Informativa_059.pdf . Essa nota é normativa/documental HISTÓRICA; **não é checksum nem dicionário anual autenticado do ZIP DENG/2024**.
2. **Ministério da Saúde: Notificações de casos suspeitos de dengue**, página de contexto geral: suspeitas e confirmações são notificação compulsória, e notificações suspeitas são inseridas na ficha de notificação/investigação e SINAN. Link oficial: https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/d/dengue/casos-suspeitos . **Notificação não equivale automaticamente a caso confirmado ou pessoa única.**
3. **Ministério da Saúde: Boletim Epidemiológico vol. 55 nº 11, 04/07/2024**, seção métodos: analisa casos prováveis e óbitos notificados e inclui SINAN Online, e-SUS VS e GAL, com definições próprias e data de extração. Link oficial: https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/boletins/epidemiologicos/edicoes/2024/boletim-epidemiologico-volume-55-no-11.pdf/@@download/file . É exemplo de **universo e recorte**, não prova da identidade ou completude do ZIP local.
4. **Dicionário recente disponibilizado pelo operador** `dic_dados_dengue.pdf`, SHA-256 local `d15122f38b32c4b3caf58cca7e717065b24c888771ecad8e7a3ed02e0efd16a1`, 22 páginas, 121 entradas/120 nomes distintos; `CLASSI_FIN` com tabela 1/2/8 enquanto regras do próprio PDF apontam 11/12/13. O PDF também contém duplicação `coufinf` e tipo gráfico `char()1` em duas entradas. A existência de versões/documentos conflitantes **exige revisão, não combinação ad hoc**.
5. **Cabeçalho local DENG/2024** inspecionado sem acessar linhas de pacientes: 121 nomes; 119 correspondências literais com o PDF; `CLINIC_CHIK` documentado ausente da exportação; `CLINC_CHIK` presente na exportação e candidato à diferença de grafia; `UF` também no cabeçalho sem significado comprovado. Contagens e SHA do ZIP registrados em parecer privado não publicável.

## Matriz de decisões obrigatórias

| Tema | Evidência documental / hipótese | Decisão ainda exigida | Proibição até decisão |
|---|---|---|---|
| `CLASSI_FIN` | Nota oficial 2016: 5/10/11/12/13; PDF recente com 1/2/8 em tabela e 11/12/13 nas regras | Confirmar dicionário, versão da distribuição 2024, sistema de origem, tipo, domínio e valores de fato, sob acesso autorizado | Não classificar confirmados, descartados, casos graves, chikungunya ou construir denominadores |
| `CLINC_CHIK` vs. `CLINIC_CHIK` | Diferença nominal de um caractere; nota oficial 2016 prevê apresentação clínica condicionada a chikungunya | Evidência de layout de exportação e correspondência semântica para a versão 2024 | Não criar alias automático nem interpretar campo vazio |
| `UF` | Coluna adicional, ausente no PDF com nome idêntico; existem campos de UF de residência e notificação | Determinar origem, recodificação, critério territorial e tratamento de ignorados | Não inferir residência, notificação ou município |
| Ano de arquivo e datas | `DENGBR24.csv.zip` rotulado 2024; portais públicos podem republicar recurso | Definir ano de notificação vs. sintomas, janela de inclusão, data de extração e status de consolidação | Não dizer que recorte representa população final 2024 |
| Unidade observacional | Ficha de notificação e possíveis episódios de doença | Definir notificação, caso, indivíduo, coorte e chaves de unicidade, sob custódia e regras de minimização | Não deduplicar por igualdade de atributos nem afirmar prevalência/incidência |
| Completude e perdas | Auditor sintético verificou somente contagens artificiais | Estabelecer contrato de ingestão com linhas de origem, perdas, conversões e estatísticas revisadas localmente | Não usar projeção SQLite isoladamente para validar dados brutos |
| Denominadores/TabNet | Indicadores oficiais podem combinar SINAN, e-SUS VS, GAL e população IBGE | Fixar versão, sistema, filtros, região, estratos e data de corte para cada medida | Não usar totais discordantes ou populações arbitrárias |
| Divulgação e composição | Agregados e cruzamentos temporais podem permitir reconstrução de pequenas células | Avaliação de privacidade cumulativa, base legal, acesso, retenção e pareceres independentes | Não publicar tabelas nem estatísticas de auditoria sem revisão |

## Plano de verificação científica por fases

**Fase A — documentação sem microdados:** revisão independente da Nota 59/2016, dicionários que correspondam ao recurso CSV 2024 e prova da versão do recurso; atribuir responsáveis e fontes oficiais de confirmação, registrando a possibilidade de sistemas de vigilância distintos. **Não declarar status 'aprovado' no software.**

**Fase B — contrato sintético reproduzível:** especificar campos, tipos, placeholders, códigos de ignorados, datas e deduplicação hipotética; escrever testes sintéticos positivos, negativos e de incompatibilidade entre versões. Preservar unidade observacional como indeterminada até decisão do epidemiologista.

**Fase C — ambiente institucional privado e autorizado:** somente após avaliação das condições de custódia/legalidade e dos riscos, realizar leitura local auditável e limitada dos dados reais; comparar com referência epidemiológica da mesma versão e data de corte; não enviar dados a PR/MCP/cloud de testes/chat.

**Fase D — aceite independente:** submeter métricas, exclusões, variações temporais e protocolos de supressão/composição a revisão especializada. Publicação de agregados estáticos exige autorização distinta, mesmo que testes de software e auditorias locais passem.

## Estado de implementação no SINAN-MCP

- PR #11: plano privado DENG/2024 criado no Windows, 9 checkpoints pendentes.
- PR #12: ensaio CSV inteiramente sintético criado no Windows; **6 linhas artificiais, 4 entradas malformadas recusadas, 0 checkpoints científicos homologados, 0 dados SINAN lidos**, publicação negada.
- **Roadmap: 5 frentes sem evidência e 2 evidências locais NÃO homologadas; 0 revisões independentes autenticadas.** Este documento e as notas históricas são materiais para revisão científica, **não** comprovam que as frentes `qualidade_coorte` ou `indicador_denominador` estejam concluídas.
