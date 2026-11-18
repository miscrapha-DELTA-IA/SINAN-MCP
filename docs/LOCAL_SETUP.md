# Instalação local | SINAN MCP

**Guia para desenvolvedores e avaliadores técnicos.** A instalação descrita nesta página cria somente uma **base fictícia** de testes.

[Visão geral](../README.md) · [Documentação](README.md) · [Segurança](../SECURITY.md)

## Requisitos

- Python **3.11 ou superior**;
- Git;
- acesso a um terminal;
- ambiente virtual isolado recomendado.

Não é necessário baixar um arquivo SINAN, consultar o PySUS ou possuir credenciais de saúde para executar a demonstração.

## Windows (PowerShell)

```powershell
git clone https://github.com/miscrapha-DELTA-IA/SINAN-MCP.git
cd SINAN-MCP
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m sinan_mcp demo
.\.venv\Scripts\python.exe -m pytest -q
```

Para iniciar o servidor MCP local com a base fictícia:

```powershell
.\.venv\Scripts\python.exe -m sinan_mcp --db ./data/sinan-demo.sqlite3 servir
```

O modo local utiliza **stdio**: aguarda comunicação de um cliente MCP e não deve ser exposto à internet. Para configurar um túnel de desenvolvimento no Windows, consulte o [procedimento técnico específico](operations/CHATGPT_TUNNEL_WINDOWS.md) e suas restrições de privacidade.

## macOS ou Linux

```bash
git clone https://github.com/miscrapha-DELTA-IA/SINAN-MCP.git
cd SINAN-MCP
python3.11 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m sinan_mcp demo
.venv/bin/python -m pytest -q
```

Servidor MCP local:

```bash
.venv/bin/python -m sinan_mcp --db ./data/sinan-demo.sqlite3 servir
```

## Piloto local com o arquivo real de tuberculose de 2024

O comando abaixo baixa uma versão específica de `TUBEBR24.parquet` do espelho público do PySUS. A importação confere o tamanho e o SHA-256 observado nessa versão antes de abrir o Parquet. Ela lê apenas município de residência, sexo, raça/cor e situação de encerramento, grava a projeção em SQLite e remove o Parquet temporário. A consolidação epidemiológica do arquivo permanece desconhecida.

Na raiz do repositório, com o ambiente virtual ativo, execute:

```powershell
python -m pip install -e . "pyarrow>=17,<25"
python -m sinan_mcp --db ./data/piloto-tb-2024.sqlite3 importar-piloto-tb-2024
python scripts/verificar_piloto_tb.py --db ./data/piloto-tb-2024.sqlite3
```

Use um banco dedicado. Uma nova importação substitui a carga anterior de TUBE/2024 nesse banco dentro de uma transação. O verificador inicia o servidor privado por stdio, confere a origem no catálogo e consulta a partição PI por sexo. A opção de leitura real vale apenas para o processo filho. Uma resposta suprimida confirma que a consulta passou pela política de divulgação. O teste relata o estado sem imprimir as células. Nenhum túnel é necessário.

## Demonstração pública

A instância externa está em [`/mcp`](https://sinan-mcp-public-preview.onrender.com/mcp); seu estado pode ser consultado em [`/health`](https://sinan-mcp-public-preview.onrender.com/health). O primeiro endereço é uma interface **MCP/HTTP para aplicativos compatíveis**, não um site de navegação.

A instância pública não consulta bases privadas, não importa arquivos e não apresenta estatísticas reais de agravos. As contagens da demonstração são exclusivamente sintéticas.

## Verificação e problemas

1. A instalação de dependências e a suíte de testes devem terminar sem erros; falhas ou testes omitidos devem ser registrados como tais.
2. A base criada pelo comando `demo` é destinada apenas a testes e não comprova integração com dados SINAN reais.
3. Para falhas reprodutíveis, abra uma [issue no repositório](https://github.com/miscrapha-DELTA-IA/SINAN-MCP/issues), informando sistema operacional, versão Python, comando e mensagem de erro **sem segredos, identificadores pessoais ou registros clínicos**.

O uso de dados reais exige uma arquitetura e um processo de autorização separados. Consulte a [política de segurança](../SECURITY.md).
