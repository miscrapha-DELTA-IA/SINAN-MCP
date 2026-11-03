# Pesquisa reproduzível: três PoCs científicas e MCP

**Escopo:** somente dados fictícios e metadados. Não usa nem publica microdados
SINAN. Os contratos TUBE/DENG são exemplos pedagógicos, NÃO dicionários
oficiais de 2024, e não autorizam a inferência de qualquer indicador clínico.

Este pacote implementa recomendações priorizadas na rodada 1 de Technology
Intelligence (novembro/2026), mantendo o serviço público de dados reais
DESATIVADO.

## 1. Camada semântica para desenho de estudos

Novas ferramentas somente de leitura na demonstração MCP:

- vocabulario_semantico: lista de unidades observacionais, eixos temporais,
  tipos de medidas, denominadores e referências pendentes.
- planejar_medida_epidemiologica: recebe um alias interno de agravo, ano
  do arquivo, unidade observacional, eixo temporal, medida pretendida,
  denominador e fonte do denominador, todos com vocabulários controlados.

A resposta sempre tem valor nulo e aceito_para_calculo_real=false.
Pedidos sem denominador ou conceito epidemiológico compatível recebem
um estado de recusa estruturado. Mesmo quando os campos estão completos,
o estado indica falta de fonte e método independentes validados para
aquele agravo/ano.

Apenas o módulo público (sem SQLite, PySUS, pandas ou Pandera) expõe essas
tools de planejamento; não executa cálculos reais. Os exemplos numéricos
sintéticos existentes agora incluem metadados sobre unidade fictícia,
eixo temporal, numerador, denominador e a inexistência de incidência/risco
epidemiológico.

## 2. Contratos de dados versionados — somente demonstração

Dois contratos JSON empacotados:

- sinan_mcp/contracts/TUBE_2024_EXAMPLE.json
- sinan_mcp/contracts/DENG_2024_EXAMPLE.json

Ambos são explicitamente DEMONSTRACAO_SINTETICA_NAO_VALIDADA.
Não devem ser usados para aprovar bases reais, nem conectados de modo
automático à ingestão PySUS.

Um módulo administrativo separado implementa:

1. Identificação por allowlist (sem carregar arquivos de contrato de origem
   arbitrária ou reinterpretar um alias como código oficial).
2. SHA-256 determinístico do contrato e comparação estrutural dos domínios
   e colunas entre dois exemplos.
3. Checagem Pandera opcional de CSV local, apenas para o cabeçalho ficcional
   especificado no contrato e com processamento por lotes limitados.
4. Falha fechada para colunas adicionais, cabeçalho duplicado, categorias
   desconhecidas, padrões inválidos e links simbólicos.
5. Exceções sem valores de linhas, nomes de pessoas, índices de registros
   ou caminhos privados.

Uso administrativo local em Windows PowerShell:

    py -3.11 -m pip install -e ".[dev,quality]"
    py -3.11 -m sinan_mcp listar-contratos-demo
    py -3.11 -m sinan_mcp comparar-contratos-demo DENG_2024_EXAMPLE TUBE_2024_EXAMPLE
    py -3.11 -m sinan_mcp validar-csv-demo .\ficticio.csv --contrato TUBE_2024_EXAMPLE
    py -3.11 -m pytest -q tests/test_schema_contracts.py tests/test_semantics.py

Para o último comando CLI, o usuário precisa criar **somente** um arquivo
artificial com as colunas ID_MN_RESI, CS_SEXO, CS_RACA e SITUA_ENCE.
Evite experimentar com dados pessoais, mesmo que sejam considerados
abertos. O relatório é local e não certifica o dicionário de ano algum.

A biblioteca Pandera é uma dependência opcional de pesquisa: a instalação
básica do servidor MCP continua leve, sem pandas/Pandera.

## 3. Compatibilidade e testes de contrato MCP

- Tests/test_public_mcp_contract.py mantém um snapshot manual dos nomes,
  descrições e nomes dos parâmetros das ferramentas públicas. Alterações
  inadvertidas exigirão revisão explícita.
- Tests/test_semantics.py confere negociação atual do SDK Python MCP na
  revisão 2026-07-28, sem sessão, além de recusa de medidas sem denominador.
- Os testes HTTP existentes continuam cobrindo o protocolo 2025-11-25
  de forma retrocompatível.
- A CI principal executa testes em Python 3.11/3.12 e Windows/Linux.
  A CI opcional Pandera, disparada em PR, executa regressões de esquema
  e ferramentas públicas com a dependência Pandera instalada.

Documentação técnica primária consultada:

- https://py.sdk.modelcontextprotocol.io/protocol-versions/
- https://pandera.readthedocs.io/en/latest/dataframe_schemas.html
- https://modelcontextprotocol.io/specification/2026-07-28

## O que ainda NÃO está aprovado

- Acesso remoto a microdados.
- Fontes e dicionários oficiais específicos por agravo/ano.
- Interpretação de dados como indivíduos/casos únicos.
- Coortes, incidência, prevalência, letalidade ou modelos de risco.
- Publicação de agregados sem revisão institucional e científica.
- Qualquer certificado de anonimização ou conformidade legal.

Os próximos passos técnicos são contratos com dicionários oficiais por
ano, a ser auditados por epidemiologistas; monitor de alterações de edição
de fonte; planos de estudo versionados; RO-Crate para dados já revisados;
e testes com clientes externos. Nenhuma dessas funções autoriza publicar
dados reais por padrão.
