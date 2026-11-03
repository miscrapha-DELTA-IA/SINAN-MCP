# Revisão documental de nove campos ausentes — DENG/2024 x Sinan Online 2015

Esta análise registra exclusivamente **nomes de campos públicos** presentes no dicionário PDF SINAN Online 3.0 de 2015 e ausentes no cabeçalho do arquivo CSV do ano rotulado 2024, conforme relatório de auditoria local do pesquisador. Não houve envio ou leitura do ZIP de notificações no GitHub/ChatGPT, nem análise de linhas.

Fonte primária: https://portalsinan.saude.gov.br/images/documentos/Agravos/Dengue/DIC_DADOS_ONLINE.pdf (27 páginas). As páginas listadas abaixo usam numeração iniciada em 1; as páginas foram conferidas visualmente.

| Nome extraído | Página PDF | Conferência documental | Resultado |
| --- | --- | --- | --- |
| DDD_HOSP | 8 | DDD do telefone da unidade de hospitalização, preenchimento condicionado à hospitalização | Nome DBF documentado, CSV ausente; motivo não confirmado |
| HOSPITAL | 8 | Identificação da unidade hospitalar, preenchimento condicionado à hospitalização | Nome DBF documentado, CSV ausente; motivo não confirmado |
| TEL_HOSP | 8 | Telefone da unidade hospitalar, preenchimento condicionado à hospitalização | Nome DBF documentado, CSV ausente; motivo não confirmado |
| CODISINF | 13 | Código do distrito provável de infecção | Nome DBF documentado, CSV ausente; motivo não confirmado |
| CO_BAINF | 13 | Código do bairro provável de infecção | Nome DBF documentado, CSV ausente; motivo não confirmado |
| NOBAIINF | 13 | Nome do bairro provável de infecção | Nome DBF documentado, CSV ausente; motivo não confirmado |
| A | 14 | Palavra isolada em parágrafo explicativo sobre cadastro de bairros; **não consta na coluna DBF** | **FALSO POSITIVO** do extrator por geometria |
| CLINIC_CHIK | 15 | Apresentação clínica de chikungunya, condicionada à classificação de chikungunya | Nome DBF documentado; possível diferença de escopo em exportação dengue, não comprovada |
| DS_OBS | 27 | Observações adicionais em texto livre | Nome DBF documentado, CSV ausente; hipótese de supressão de conteúdo sensível ainda não comprovada |

## Contagens e interpretação

Relatório inicial com **121** nomes de colunas em CSV: **87 candidatos documentais**, sendo **78 observados** e **9 ausentes**, com **43 nomes no CSV fora do rascunho**.

Conferência documental: **1 candidato é falso positivo confirmado (A, página 14)**, restando **86 candidatos**, sendo 78 observados e 8 nomes DBF de 2015 ausentes. **Os 43 nomes adicionais do CSV NÃO foram listados, examinados ou aprovados por esta revisão.** O documento de 2015 não descreve necessariamente o layout CSV de 2024.

O código foi corrigido com uma exclusão **específica da combinação (A, página 14)**; ela não exclui outros nomes de uma letra em documentos distintos. Após atualização do código, gerar novo contrato e novo relatório privados, sem sobrescrever os originais, para confirmar as novas contagens localmente. Não alterar manualmente relatórios antigos.

## Documentação posterior

O [Portal de Dados Abertos do SUS — Sinan/Dengue](https://dadosabertos.saude.gov.br/dataset/arboviroses-dengue) identifica outro recurso chamado **Dicionário de dados - Dengue**, com data de atualização **14/07/2025**. A simples data da página não prova que essa documentação corresponde ao ZIP obtido pelo pesquisador; antes de homologar um contrato 2024 será necessário obter a versão exata do novo dicionário, comparar todos os campos, registrar ETL e validar por revisão independente.

A ausência de variáveis de hospitalização, distrito/bairro, apresentação clínica de chikungunya ou texto livre pode resultar de diferenças de versão, escopo ou política de divulgação. **Essas são hipóteses e não conclusões sobre o Ministério da Saúde.**

## Requisitos de privacidade e ciência

Este documento não contém dados de pacientes, cabeçalhos desconhecidos do CSV, contagens de notificações ou resultados epidemiológicos. Não publicar o contrato/candidato privado, o parecer local, nem o ZIP no GitHub. Nenhuma variável real foi validada quanto a domínio, completude, origem, consolidação ou adequação científica. A autorização de uso e divulgação permanece bloqueada.
