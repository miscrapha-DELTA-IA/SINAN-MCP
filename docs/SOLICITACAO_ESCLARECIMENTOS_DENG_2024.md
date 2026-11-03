# Solicitação técnica sobre a distribuição SINAN/Dengue 2024

**Rascunho institucional para revisão antes de enviar. Não inclui dados individuais, CSV, ZIP, cabeçalhos privados, hashes nem documentos de auditoria interna. Não foi enviado.**

## Destinatários sugeridos (publicamente divulgados)

- Coordenação-Geral de Vigilância de Arboviroses: `arboviroses@saude.gov.br` (contato divulgado no conjunto de dados [Arboviroses/Dengue](https://dadosabertos.saude.gov.br/dataset/arboviroses-dengue)).
- Suporte à utilização de bases de dados abertos SUS: `dadosabertos@saude.gov.br` (canal da página de [serviço do Governo Federal](https://www.gov.br/pt-br/servicos/obter-suporte-sobre-o-consumo-de-bases-de-dados-abertos-do-sus)).
- É possível iniciar pela coordenação e colocar o suporte em cópia, ou abrir o chamado pelo canal de suporte para obter protocolo institucional.

## Mensagem sugerida

**Assunto:** Esclarecimentos técnicos sobre versão, dicionário e classificação — recurso CSV SINAN/Dengue 2024

Prezada equipe da Vigilância de Arboviroses / Dados Abertos do SUS,

Estamos desenvolvendo um protocolo de avaliação da qualidade de dados epidemiológicos no âmbito de um projeto acadêmico de informática em saúde, atualmente restrito a verificações documentais e testes sintéticos. Para interpretar corretamente o recurso público **“Dengue – 2024” (CSV)**, solicitamos esclarecimentos técnicos sobre a versão da distribuição e seu dicionário.

**Identificador oficial do recurso:** `4cf2f7b8-9920-41b5-817a-1ffc13e0690c`  
**Página:** https://dadosabertos.saude.gov.br/dataset/arboviroses-dengue/resource/4cf2f7b8-9920-41b5-817a-1ffc13e0690c  
**Distribuição:** `DENGBR24.csv.zip`

Gostaríamos de confirmar:

1. **Versão e corte:** qual a edição do arquivo disponibilizado em outubro de 2026, sua data de extração/corte, a regra de atualização retroativa e a situação de consolidação epidemiológica? Existe checksum publicado pela autoridade ou histórico de snapshots para identificar a versão exata dos bytes?
2. **Dicionário aplicável:** qual documento/schema corresponde especificamente ao CSV DENG/2024, com tipos, códigos de ignorado, regras de transformação e origem do sistema de notificação? Há mapeamento oficial de diferenças entre edições do dicionário e versões do Sinan Online?
3. **Classificação final:** qual é o domínio exato do campo de classificação final nessa exportação? Há documentação da convivência de códigos históricos **5/10/11/12/13** do Sinan Online 3.0 (Nota Informativa nº 59/2016) com códigos **1/2/8** mostrados em tabela de outro dicionário disponibilizado no portal? Para esta distribuição, quais códigos devem ser empregados nas análises de casos prováveis, confirmados, graves e descartados?
4. **Campos e geografia:** existe documentação oficial dos campos adicionais/de apresentação clínica e de UF presentes em determinadas exportações, incluindo renomeações, campos derivados e distinção entre local de residência e local de notificação? Preferimos não inferir essas equivalências.
5. **Unidade e indicadores:** uma linha equivale a uma notificação, um episódio de doença ou um caso único? Existe procedimento recomendado para registros repetidos, atrasos de fechamento, definição temporal da coorte e reconciliação com TabNet/boletins que utilizem outra data de corte?

Se possível, solicitamos referências públicas, o dicionário/nota técnica versionado(a) ou o encaminhamento à equipe responsável pelas regras de exportação.

Não solicitamos acesso a dados identificáveis, não anexamos registros de pacientes e não estamos tratando o arquivo como epidemiologicamente homologado. A intenção é evitar mapeamentos e indicadores incorretos antes de qualquer análise formal.

Agradecemos a orientação.

Atenciosamente,  
Equipe responsável pelo projeto SINAN MCP  
[Nome, afiliação acadêmica e contato institucional a preencher antes do envio]

## Evidências públicas citadas

- [Recurso de dados Dengue/2024](https://dadosabertos.saude.gov.br/dataset/arboviroses-dengue/resource/4cf2f7b8-9920-41b5-817a-1ffc13e0690c): o portal informa atualização dos dados em 20/10/2026, mas essa data **não autentica o ZIP local nem prova consolidação**.
- [Conjunto Arboviroses/Dengue](https://dadosabertos.saude.gov.br/dataset/arboviroses-dengue): o portal descreve casos prováveis como casos suspeitos notificados, exceto descartados; recomenda locais de residência para incidência; informa possíveis divergências das bases com tabulações da coordenação e uso de séries congeladas conforme recorte.
- [Nota Informativa nº 59/2016, Sinan Online v3.0](https://portalsinan.saude.gov.br/images/documentos/Agravos/Dengue/Nota_Informativa_059.pdf): define categorias históricas de classificação para o sistema daquela época; não garante aplicabilidade à distribuição CSV/2024.
- [Serviço oficial de suporte a bases de dados abertos SUS](https://www.gov.br/pt-br/servicos/obter-suporte-sobre-o-consumo-de-bases-de-dados-abertos-do-sus).

## Governança e próximos passos

- Submeter este texto a revisão antes de enviar; **não anexar** o dossiê ou arquivo privado da estação local por padrão.
- Arquivar localmente número de protocolo, data do atendimento, documentos públicos recebidos e sua versão. Não registrar nomes/contatos pessoais ou credenciais no repositório.
- Quando vier uma resposta: separar **esclarecimento técnico** de **parecer independente e autorização institucional**, que exigem instâncias e validações distintas.
- **Status atual:** 7 questões científicas e 9 checkpoints de qualidade pendentes; 0 revisores autenticados; 5/7 frentes sem evidência; 2 evidências locais não validadas; nenhum dado real foi lido pelos módulos recentes e nenhuma publicação foi autorizada.
