$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -match 'uvicorn' }
foreach ($p in $procs) {
  try { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
}
# Ativar virtualenv e iniciar uvicorn
. .venv\Scripts\Activate
uvicorn backend.main:app --reload --port 8000
