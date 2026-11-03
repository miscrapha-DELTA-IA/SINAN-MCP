# ZIKA — descoberta administrativa do recurso de dicionário no CKAN

**Fronteira:** esta etapa identifica somente metadados de uma ficha PDF listada
pelo Portal SUS. Não certifica versão, conteúdo do documento, aplicação
ao arquivo ZIKA/2024, integridade de microdados, corte ou autorização.

## Evidência e limitação atual

O [conjunto oficial Sinan/Vírus Zika](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus)
lista o item **"Dicionário de dados - Zika Vírus"**, com atualização
**14/07/2025**. No acesso de pesquisa disponível nesta etapa, a página
HTML do conjunto mostrou o título e a data, mas **não forneceu
o UUID/URL individual do recurso**, e o endpoint CKAN não pôde ser
consultado deste ambiente. Portanto o código NÃO contém um UUID ou PDF
inventado, e o catálogo específico permanece com 12 dicionários
históricos e 5 distribuições anuais (2 DENG, 1 CHIK, 2 ZIKA).

O [Ministério da Saúde também indica](https://www.gov.br/saude/pt-br/acesso-a-informacao/sic/dados-em-transparencia-ativa/svsa/arbovirus)
o arquivo **Docs_TAB_SINAN.zip** na modalidade *Documentação* do
portal DATASUS, que pode servir de fonte alternativa para localizar
a edição e a descrição dos campos.

## Diagnóstico local controlado (Windows PowerShell 5.1)

```powershell
py -3.11 -m sinan_mcp identificar-dicionario-zika-ckan
```

Esse comando tenta apenas uma leitura de **metadados JSON** do endereço
fixo `https://ckan-dadosabertos.saude.gov.br/api/3/action/package_show?id=arboviroses-zika-virus`.
O endpoint é um **candidato de descoberta** e não foi confirmado
acessível neste ambiente. O programa limita a 8 segundos e 2 MiB,
nega redirecionamentos, exige HTTPS e valida o ID exato do conjunto,
o título, a unicidade, o formato PDF e o UUID do recurso.

Se o servidor CKAN estiver inacessível, o comando encerra com
**erro de descoberta**, sem supor um identificador. A saída agora informa
uma **categoria de causa**, nunca texto bruto da resposta do servidor:
`DNS_NAO_RESOLVE`, `TIMEOUT`, `TLS_CERTIFICADO_OU_CONEXAO`,
`HTTP_403`, `HTTP_404`, `HTTP_429`, `REDIRECIONAMENTO_HTTP_BLOQUEADO`,
`RESPOSTA_NAO_JSON`, `RECURSO_AUSENTE_OU_AMBIGUO`,
`PACOTE_CKAN_DIVERGENTE` ou outra categoria fechada.

Isso é uma distinção essencial: falha HTTP/DNS/TLS indica impedimento de
consulta, **não ausência do dicionário**. Já uma resposta CKAN estruturada
sem recurso correspondente pode indicar mudança do catálogo, nome distinto
ou identificador de conjunto divergente. O estado anterior de dicionário
específico Zika **listado, PDF ainda não auditado** permanece inalterado.

Para comprovação local **sem usar métodos de contorno ou contatar o
servidor com frequência**, se a categoria indicar DNS ou rede, conferir
os seguintes comandos nativos no Windows:

```powershell
Resolve-DnsName ckan-dadosabertos.saude.gov.br -ErrorAction SilentlyContinue |
    Select-Object Name, Type, IPAddress
Test-NetConnection ckan-dadosabertos.saude.gov.br -Port 443 -InformationLevel Quiet
```

A confirmação de DNS/porta **não** implica resposta válida do endpoint
CKAN, e `Test-NetConnection` pode falhar por configuração local,
proxy, firewall ou serviço indisponível. Não desativar verificação TLS,
não configurar proxies desconhecidos e não recorrer a scraping de
terceiros como prova oficial. O usuário pode
consultar diretamente a
[página do conjunto oficial](https://dadosabertos.saude.gov.br/dataset/arboviroses-zika-virus)
e usar a modalidade documental do DATASUS. **Não execute scripts de
sites terceiros para obter links; não forneça credenciais ao programa.**

Caso o comando encontre o recurso, ele mostra a **página oficial
derivada do UUID**. A URL de download candidata só é mostrada quando
a API retornar caminho HTTPS estritamente permitido do S3 oficial:
`/ckan.saude.gov.br/SINAN/Zikavirus/pdf/<arquivo>.pdf`.
URLs com hosts não permitidos, redirecionamentos, formatos diferentes,
codificações ambíguas, travessia ou queries são rejeitados.
Mesmo uma URL que passe a validação **não prova que o PDF foi obtido,
aberto, interpretado ou que se aplique a ZIKA/2024**.

## Aprovação e transparência

O comando importa utilitários de rede apenas na execução explícita da
CLI administrativa. Não é exportado como tool MCP, não é acionado pelo
diagnóstico `planejar-confronto-documental-2024`, não lê ZIPs e não
altera o registro aprovado. Nenhuma contagem epidemiológica é produzida.
Os testes usam **respostas JSON simuladas**, sem solicitar o endpoint
remoto no GitHub Actions.

O passo seguinte requer inspeção independente do PDF realmente obtido
por via oficial (páginas, versão, nome e definição dos campos),
identificação do corte do arquivo de 2024, e só então eventual
confronto privado autorizado de esquemas. Não marcar `SIM` em nenhum
gate científico por sucesso dessa chamada CKAN.


## Correção do DNS e novo acesso pelo HTML oficial (03/11/2026)

O Windows confirmou `DNS_ERROR_RCODE_NAME_ERROR` para
`ckan-dadosabertos.saude.gov.br`: esse host não deve continuar sendo
considerado uma API pública obrigatória. O portal usa frontend Next.js;
integrações independentes descrevem recursos em JSON dentro do HTML
de `dadosabertos.saude.gov.br/dataset/...`, sem API CKAN clássica.

**Novo comando preferencial:**

```powershell
py -3.11 -m sinan_mcp identificar-dicionario-zika-portal
```

O comando anterior `identificar-dicionario-zika-ckan` é mantido
como **alias de compatibilidade**, mas também consulta a página HTML
oficial, não o subdomínio que não resolve. A implementação usa uma única
requisição HTTPS GET de até 3 MiB e 10 segundos, sem redirecionamentos,
HTML de host/caminho fixos, sem execução de JavaScript e sem download
de PDFs ou ZIPs.

O parser aceita apenas referências vinculadas à lista de recursos que
inclua também ao menos um UUID ZIKA/2024 já comprovado. O título do
recurso deve ser exatamente "Dicionário de dados - Zika Vírus" (com
normalização de acentos) e o UUID precisa seguir formato estrito. Somente
uma URL S3 oficial cujo caminho passe pela allowlist pode ser exibida;
mesmo assim o PDF não é baixado nem auditado.

**Limitação:** caso o site gere os dados exclusivamente no navegador
ou em um formato HTML não reconhecido, o comando informa
`HTML_SEM_UUID_DOCUMENTAL_VERIFICAVEL`; isso **não** significa que o
dicionário não exista. Use o catálogo oficial no navegador e o pacote
`Docs_TAB_SINAN.zip` da modalidade Documentação, sem atribuir validade
a dados reais nem inventar UUID. A existência de um item no portal
continua diferente da auditoria do PDF ou da compatibilidade com 2024.

Fonte técnica para a decisão arquitetural:
[documentação de fonte oficial do projeto independente MCP CNES](https://github.com/kevyn-castelo/mcp-cnes/blob/main/docs/fontes.md).
