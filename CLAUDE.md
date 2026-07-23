# CLAUDE.md

Instruções operacionais para qualquer agente Claude Code trabalhando
neste repositório. Ver `.specify/memory/constitution.md` para princípios
e `DECISOES_PROJETO.md` para o histórico de decisões — este arquivo é só
para atalhos operacionais que, sem isso, cada sessão nova redescobriria do
zero.

## Databricks CLI já está disponível — não pule pra "não tenho acesso"

O aviso automático de sessão ("Databricks CLI is not on PATH") é sobre o
`PATH`, não sobre instalação: o CLI **está instalado** (via WinGet) e
autenticado (profile `DEFAULT`). Antes de assumir que falta configurar,
localize e adicione ao `PATH` desta sessão:

**PowerShell:**
```powershell
$dbx = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter "databricks.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
$env:PATH += ";$(Split-Path $dbx)"
databricks --version
databricks auth profiles
```

O `PATH` **não persiste** entre chamadas de shell nesta ferramenta — repita
o bloco acima a cada novo comando PowerShell/Bash que precise do CLI (ou
chame o executável pelo caminho completo).

Depois disso, use as skills `databricks-core` (auth, exploração de dados)
e `databricks-jobs` (upload de notebook via `databricks workspace import`,
execução via `databricks jobs submit`, output via
`databricks jobs get-run-output`) normalmente — é o mecanismo de execução
usado por todas as features deste case (ver `research.md` de cada
feature, seção "Execution mechanism").
