# Repo Scaffold — iFood Data Architecture Case

**Data:** 2026-07-22
**Status:** Aprovado e implementado

## Objetivo

Estruturar o repositório do case técnico de Data Architect (iFood) no formato
pedido no enunciado, estendido com as decisões já registradas em
`docs/DECISOES_PROJETO.md`, e publicá-lo no GitHub. Este spec cobre apenas o
*scaffold* inicial (estrutura de pastas, arquivos base, git/GitHub) — não a
arquitetura da pipeline de ingestão em si, que será tratada em spec(s)
separado(s) na fase Specify do fluxo SDD.

## Decisões

- **Diretório local:** mantido como `C:\Repos\Case_taxi` (working directory
  ativo da sessão). O nome `ifood-case` é usado apenas para o repositório
  remoto no GitHub — local e remoto não precisam ter o mesmo nome.
- **Visibilidade do repositório:** privado.
- **Estrutura de pastas:** a definida no enunciado do PDF (`src/`, `analysis/`,
  `README.md`, `requirements.txt`), estendida com `contracts/` e
  `.claude/specs/` (já previstas em `docs/DECISOES_PROJETO.md`), mais `docs/`
  (documentação e specs de design) e `data/` (landing local git-ignorada, para
  o plano B de ingestão caso o domínio da NYC TLC não esteja liberado na saída
  de internet do Databricks Free Edition).
- **PDF do enunciado:** não versionado (fica só local). O arquivo de decisões
  foi movido para `docs/DECISOES_PROJETO.md` (renomeado, sem o sufixo `-1`).
- **Pastas vazias:** populadas com `.gitkeep`, já que o git não versiona
  diretórios vazios.

## Estrutura final

```
ifood-case/                     (remoto; local = Case_taxi)
├─ src/
├─ analysis/
├─ contracts/
├─ docs/
│  ├─ DECISOES_PROJETO.md
│  └─ superpowers/specs/
├─ data/                        # git-ignorado, exceto .gitkeep
├─ .claude/specs/
├─ .gitignore
├─ README.md
└─ requirements.txt
```

## Fora de escopo (tratado em specs futuros)

- Arquitetura da pipeline de ingestão (bronze/silver, PySpark, Delta Lake)
- Contratos de dados (`contracts/nyc_taxi_silver.yaml`)
- Data profiling e regras de data quality
- Observability da pipeline
- Genie Space e agente custom de NL-to-SQL
