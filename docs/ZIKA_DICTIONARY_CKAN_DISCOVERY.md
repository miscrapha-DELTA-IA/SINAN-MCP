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
**erro de descoberta**, sem supor um identificador. O usuário pode
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
