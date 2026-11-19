# SINAN-TB 2019 — evidência de concordância restrita (quatro campos)

**Estado: êxito técnico relatado pelo operador em execução local, não homologação epidemiológica nem autorização de publicação.**

## Identidade dos artefatos

| Artefato | Identificação | SHA-256 |
|---|---|---|
| DBC recebido via FTP DATASUS, `FINAIS/TUBEBR19.dbc` | 5.289.464 bytes; MDTM `20251015195757` | `7a00e29a5a309b794e21f1a650d3b04b9d3cb05fcc6ef8c9feefab3a961c9144` |
| Parquet espelho PySUS, `public/data/ftp/sinan/TUBE/2019/_/BR/TUBEBR19.parquet` | 3.603.114 bytes no catálogo | `7c599143671bb8bd895e2dbd39a325682b12d9fd5a024fcec101bb76ed0fc277` |

O DBC foi observado em `/dissemin/publicos/SINAN/DADOS/FINAIS/`. O FTP oficial não autentica criptograficamente o conteúdo. O SHA-256 calculado fixa os bytes recebidos pelo operador, mas não substitui um checksum oficial autenticado. O checksum do Parquet foi verificado pelo utilitário de download do projeto.

## Procedimento executado e resultado

No Windows com Python 3.11, usando o código da branch `audit/tb-edition-provenance-20261118`:

```powershell
.\.venv\Scripts\python.exe -m scripts.avaliar_equivalencia_tb2019 --etapa comparar
```

**Saída textual relatada pelo operador** (apenas campos de auditoria, sem registros):

```json
{
  "stage": "FOUR_COLUMN_RESEARCH_COMPARISON_NOT_HOMOLOGATED",
  "campos_comparados": ["ID_MN_RESI", "CS_SEXO", "CS_RACA", "SITUA_ENCE"],
  "multiconjunto_4_campos_igual": true,
  "equivalencia_integral_verificada": false,
  "status_final_homologado": false,
  "publicacao_autorizada": false
}
```

O comparador normaliza valores ausentes e representação de números inteiros com `.0`; compara o **multiconjunto integral de linhas das quatro colunas** com suas multiplicidades (repetições preservadas), sem imprimir linhas, valores ou contagens de células. Portanto: existe concordância das quatro colunas *sob a normalização usada*, sem prova de equivalência da tabela completa, sem autenticação forte da origem e sem validação científica do significado das variáveis.

Os hashes são identificadores de bytes; não devem ser usados para inferir que os formatos DBC e Parquet devam ter o mesmo SHA-256.

## Próximos gates

1. **Reprodutibilidade independente:** reexecutar com ambiente, dependências, versões e commit fixados; obter atestado de revisão técnica do método de normalização e da seleção da versão.
2. **Validação científico-epidemiológica:** cotejar com o dicionário SINAN-TB aplicável ao arquivo 2019; revisar códigos e rótulos de `SITUA_ENCE`, definição de unidade de registro, ano do arquivo versus coorte de notificação/diagnóstico, variáveis ausentes, interpretação de raça/cor e sexo, diferenças de interpretação de encerramento.
3. **Segurança da divulgação:** preparar somente em ambiente local um agregado de dimensão única e UF única, sem cruzamentos; revisar limite de células pequenas, potencial de inferência por diferenças, publicações sobrepostas e condições aplicáveis à divulgação. Não enviar candidato não aprovado.
4. **Contrato de publicação:** corrigir a vulnerabilidade metodológica em que a string `status_informado = final` é suficiente para passar a checagem de versão; exigir documentação verificável de origem e decisões de revisão independente. Parecer registrado por texto no JSON não garante identidade do revisor.
5. **Escopo público:** serviço público e túnel seguem sintéticos. Um serviço opcional, isolado, pode receber **somente o agregado estático aprovado** depois das revisões.

## Interpretação e limites

**Conclusão suportada:** as quatro colunas concordam, incluindo multiplicidades, para os snapshots com os hashes acima, segundo a ferramenta e saída local relatadas.  
**Não concluído:** equivalência de todas as variáveis, homologação científica, status final verificado por órgão responsável, autorização de dados reais ou ausência de risco de reidentificação.

Nenhum registro individual foi adicionado a este repositório.
