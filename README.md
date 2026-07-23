# Case Técnico Data Architect — iFood

## Objetivo

Solução de engenharia de dados para o case técnico de Data Architect do
iFood: ingestão dos dados de corridas de táxi de NY (Yellow Taxi,
Jan-Mai/2023) em um Data Lake, disponibilização para consumo via SQL, e
resposta a duas perguntas analíticas sobre os dados. O detalhamento
completo das decisões técnicas está em [`DECISOES_PROJETO.md`](DECISOES_PROJETO.md).

## Arquitetura

Modelo em camadas (medalhão simplificado), processado em **PySpark** e
persistido em **Delta Lake**, catalogado via **Unity Catalog**
(Databricks Free Edition):

- **Landing / bronze**: arquivos parquet originais, como chegaram.
- **Consumo / silver**: tabela Delta gerenciada, tipada e limpa, com um
  contrato de dados formal versionado antes da escrita (ver `contracts/`).

Data profiling e regras de qualidade de dados são etapas obrigatórias na
transição bronze → silver, e cada execução do pipeline é instrumentada
(volume, schema, lineage) — ver `DECISOES_PROJETO.md` §5-§7 para o
detalhamento dessas regras.

## Estrutura do Repositório

| Pasta/Arquivo | Propósito | Origem |
|---|---|---|
| `src/` | Código fonte do pipeline (ingestão, transformação) | Exigido pelo enunciado do case |
| `analysis/` | Scripts/notebooks com as respostas às perguntas analíticas | Exigido pelo enunciado do case |
| `contracts/` | Contratos de dados versionados das tabelas da camada de consumo | Adição do projeto — formaliza o schema/regras de qualidade da silver antes da escrita, em vez de deixá-los implícitos no código (ver Constituição, Princípio II) |
| `data/` | Landing zone local (plano B de ingestão, caso o download direto via notebook não seja viável na Free Edition); conteúdo ignorado pelo git | Adição do projeto — mitigação de risco documentada em `DECISOES_PROJETO.md` §2 |
| `specs/` | Specs versionadas do fluxo Spec-Driven Development (Spec Kit) | Adição do projeto — evidencia o processo de desenvolvimento agêntico (ver `DECISOES_PROJETO.md` §9) |
| `.specify/` | Constituição do projeto, templates e configuração do Spec Kit | Gerado pelo Spec Kit |
| `README.md` | Este arquivo | Exigido pelo enunciado do case |
| `requirements.txt` | Dependências Python fixadas para o projeto | Exigido pelo enunciado do case |

## Stack Tecnológica

- **Processamento**: PySpark (obrigatório pelo case)
- **Formato de tabela**: Delta Lake
- **Metadados/catálogo**: Unity Catalog
- **Consumo final**: SQL via Databricks SQL Warehouse
- **Plataforma**: Databricks Free Edition

Ver `requirements.txt` para as versões fixadas e `DECISOES_PROJETO.md` §2-§3
para as restrições de ambiente e justificativas.

## Como Executar

_Placeholder — esta seção será preenchida quando a feature de ingestão for
implementada. Deverá conter: como configurar o ambiente/credenciais do
Databricks, como rodar o pipeline de ingestão bronze → silver, e como
consultar os resultados via SQL Warehouse._

## Perguntas Analíticas Respondidas

_Placeholder — esta seção linkará para os scripts em `analysis/` com as
respostas às duas perguntas do case (média de `total_amount` por mês, e
média de `passenger_count` por hora no mês de maio) assim que essa feature
for implementada._
