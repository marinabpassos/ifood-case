# ifood-case — Data Architecture Case (NYC Yellow Taxi)

Case técnico de Data Architect para o iFood: ingestão, modelagem e disponibilização
via SQL dos dados de corridas de Yellow Taxi de NY (Jan–Mai 2023), seguindo um
fluxo de engenharia de dados agêntica com Claude Code.

> **Status:** em desenvolvimento. Este README será atualizado com instruções de
> execução conforme o pipeline for implementado.

## Estrutura do repositório

```
ifood-case/
├─ src/                    # Código fonte da solução (ingestão, transformação, quality)
├─ analysis/               # Scripts/notebooks com as respostas das perguntas analíticas
├─ contracts/              # Contratos de dados das tabelas da camada de consumo
├─ docs/
│  ├─ DECISOES_PROJETO.md  # Decisões de projeto tomadas antes do desenvolvimento
│  └─ superpowers/specs/   # Specs de design (fluxo de brainstorming)
├─ data/                   # Landing local (plano B), git-ignorado
├─ .claude/specs/          # Specs versionadas do fluxo SDD (Specify→Plan→Tasks→Implement)
├─ requirements.txt
└─ README.md
```

## Contexto e decisões de projeto

As decisões técnicas (plataforma, arquitetura de dados, contratos, observability,
metodologia de desenvolvimento) estão documentadas em
[`docs/DECISOES_PROJETO.md`](docs/DECISOES_PROJETO.md).

## Perguntas analíticas respondidas

1. Qual a média de valor total (`total_amount`) recebido em um mês, considerando
   todos os yellow táxis da frota?
2. Qual a média de passageiros (`passenger_count`) por cada hora do dia que
   pegaram táxi no mês de maio, considerando todos os táxis da frota?

As respostas estão em [`analysis/`](analysis/).

## Como executar

_A ser detalhado conforme a solução for implementada._
