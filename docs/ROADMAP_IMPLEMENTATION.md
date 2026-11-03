# Roadmap de produção responsável — estado executável

Este documento descreve o que efetivamente está no código e o que continua
**bloqueado**. O SINAN-MCP é software independente do Ministério da Saúde e do
DATASUS; não certifica dados epidemiológicos, anonimização ou legalidade.

## Estado por etapa

| Frente | Estado | Implementação verificável |
|---|---|---|
| Descoberta de 14 aliases internos | Disponível (referência apenas) | query_planner, official_sources; nenhum dado real |
| Ingestão local PySUS | Piloto TUBE/DENG, sem garantia por ano | pysus_gateway, catalog_import; origem explicitada |
| Transporte PySUS/FTP espelho | Endurecido | host fixo HTTPS, rejeição prévia de redirecionamento, tentativa limitada, limite de tamanho, checksum, limpeza de falhas |
| Proveniência por agravo e ano | Implementado **para conferência local declarada** | provenance: manifesto estrito, hash, horário, dicionário, método, ano e status |
| Linhagem arquivo -> SQLite | Implementado **para CSV local** | verificar-linhagem: compara hash de bytes com hash do snapshot; não serve para digest composto PySUS |
| Qualidade por doença/ano | Implementado **para projeção importada** | quality_gate: completude, consistência de contagem, formato, tuplas idênticas |
| Reconciliação com tabela | Implementado **como comparação não certificada** | reconciliation: mesmo agravo/UF/ano do arquivo/dimensão, categorias exatas, recusa célula pequena |
| Planejamento de protocolos por agravo/ano | Disponível somente como proposta | indicator_protocols e planejar-indicador; TB exploratória e DENG contagem descritiva, sem cálculo real |
| Indicadores específicos oficiais | **Bloqueado** | ainda exige definições epidemiológicas aprovadas por agravo/ano, deduplicação e denominadores |
| Revisão de composição entre releases | Bloqueio conservador disponível | release_composition nega agravo+UF repetido mesmo em anos/versões diferentes |
| OAuth, autorização institucional e API de microdados | **Não implementado e não habilitado** | sem identidade institucional confiável, não publicar dados privados |
| CI e prevenção de commits de dados | Implementado | workflow Linux/Windows; script para negar arquivos de saúde/credenciais rastreados |
| Publicação de dados reais | **Não autorizada** | nenhum comando novo publica valores ou faz deploy |

Mesmo um relatório com *contagens iguais* não prova equivalência de definições,
códigos ou coorte. O ano do arquivo não é necessariamente ano de notificação,
diagnóstico ou encerramento.

## Ferramentas administrativas (executar apenas no computador autorizado)

PowerShell 5.1, Python 3.11+:

    cd "$HOME\Downloads\SINAN-MCP-GitHub"
    git fetch origin
    py -3.11 -m pip install -e ".[dev]"
    py -3.11 -m pytest -q

**Verificação de origem/linhagem.** O operador deve criar um manifesto JSON
na convenção abaixo e trocar todos os campos pelos valores de sua evidência
documental local; nenhum metadado declarado é automaticamente certificado:

    {
      "schema_version": "sinan-source-evidence-v1",
      "agravo": "TUBE",
      "ano_arquivo": 2024,
      "tipo_ano": "ano_arquivo",
      "codigo_download_declarado": "TUBE",
      "metodo": "csv-local",
      "url_fonte": "https://www.gov.br/saude/pt-br/",
      "url_dicionario": "https://portalsinan.saude.gov.br/tuberculose",
      "versao_dicionario": "VERSAO_DE_EXEMPLO_NAO_VALIDADA",
      "situacao_declarada": "desconhecido",
      "extraido_em_utc": "2026-11-02T18:00:00Z",
      "arquivo_nome": "arquivo-local.csv",
      "arquivo_bytes": 1000,
      "arquivo_sha256": "INSERIR_SHA256_REAL_DE_64_HEXADECIMAIS",
      "observacao_metodologica": "Exemplo de estrutura; nunca usar sem validar fonte"
    }

Com os arquivos reais **sob controle institucional**, faça:

    py -3.11 -m sinan_mcp verificar-proveniencia .\data\manifesto.json .\data\arquivo-local.csv
    py -3.11 -m sinan_mcp --db .\data\sinan.sqlite3 verificar-linhagem .\data\manifesto.json .\data\arquivo-local.csv
    py -3.11 -m sinan_mcp --db .\data\sinan.sqlite3 auditar-qualidade --agravo TUBE --ano 2024

O hash compara bytes locais e pode identificar alteração do arquivo. É uma
**verificação de integridade**, não confirmação de origem governamental,
liberdade de divulgação ou validade de indicador.

**Métodos específicos por agravo/ano, apenas metadados:**

    py -3.11 -m sinan_mcp planejar-indicador --agravo TUBE --ano 2024
    py -3.11 -m sinan_mcp planejar-indicador --agravo DENG --ano 2024
    py -3.11 -m sinan_mcp planejar-indicador --agravo HEPA --ano 2024

TB apresenta apenas a metodologia exploratória já documentada; dengue
somente contagem descritiva, não incidência. Para HEPA e outros agravos, a
ausência de protocolo devolve estado sem_protocolo_especifico, nunca valores
inventados ou definição clínica extrapolada.

**Comparação com tabela TABNET declarada** (separada e privada):

    py -3.11 -m sinan_mcp --db .\data\sinan.sqlite3 confrontar-tabnet .\data\tabela-declarada.json

A ferramenta exige ano_arquivo, UF específica, ano único, dimensão única,
todas as categorias do snapshot e limites mínimos. Recusa comparar valores
locais pequenos. Retorna apenas o estado de concordância e quantas categorias
divergem, não os valores de cada categoria. O hash declarado da tabulação
não autentica sua origem; o operador precisa reconciliar com documentos
oficiais de forma independente.

**Composição de releases já aprovados em arquivos locais:**

    py -3.11 -m sinan_mcp verificar-composicao --pacote .\data\a.json SHA_A --pacote .\data\b.json SHA_B

Os SHA_A / SHA_B são os SHA-256 reais, não placeholders. Releases com mesmo
agravo+UF são recusados independentemente de dimensão e ano. Mesmo um conjunto
sem bloqueio continua com publicacao_autorizada=false. Não existe comando
"aprovar" ou "publicar" nesta etapa.

## Proteções e premissas operacionais

- **Nada é enviado a serviços externos** pelos novos validadores. A ingestão
  PySUS só baixa após comando administrativo explícito e origem selecionada.
- Não usar Git, issue, PR, chat, integração pública nem artefato de CI para
  armazenar CSV, DBC, Parquet, SQLite, manifestos privados ou dados pessoais.
- O scanner de arquivos rastreados pela CI só verifica nomes/extensões:
  não substitui revisão de diffs ou detector de segredos.
- Hash de manifesto, fonte e "final" **declarados pelo operador** não provam
  a autenticidade documental. Requer fonte exata auditada independentemente.
- Dicionário e interpretação dos indicadores variam por agravo e ano;
  códigos de outros agravos não devem reutilizar a interpretação TUBE.
- A auditoria de qualidade mede apenas a projeção: códigos inválidos podem
  ter sido descartados no pré-processamento e não aparecerão como inválidos.
- Identidade de tuplas na projeção NÃO prova duplicação de pessoas.
- Threshold 20/100 e bloqueio por agravo+UF são medidas conservadoras:
  não constituem privacidade diferencial, anonimização nem garantia LGPD.
- O serviço de demonstração HTTP permanece totalmente sintético. O candidato
  de TB/PI anteriormente não aprovado permanece fora da publicação.

## Requisitos explícitos para a próxima decisão de produção

1. Revisão científica de dicionários reais e coortes de pelo menos um agravo/ano
   com fonte e reconciliação verificáveis e parecer registrado.
2. Governança de acesso e proteção de informações sensíveis, com avaliação
   legal/ética, minimização, retenção, revogação e responsáveis identificados.
3. Para acesso institucional privado remoto: provedor de identidade confiável,
   OAuth/OIDC gerenciado com validação de issuer/audience/token, autorização
   por escopo, telemetria sem dados clínicos, rate limiting e política de logs.
4. Avaliação cumulativa contra todas as publicações e fontes auxiliares;
   revisão humana independente para cada versão/dimensão e plano de retirada.
5. Testes de carga, segurança e integrações com a infraestrutura real antes
   de qualquer implantação que não seja a simulação pública.

Sem essas comprovações o produto não deve expor dados reais por MCP remoto.
