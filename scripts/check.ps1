# Run the same checks as CI: tests, then lint. Usage: .\scripts\check.ps1
python -m pytest -q
if ($LASTEXITCODE -ne 0) { Write-Host "Tests failed" -ForegroundColor Red; exit 1 }
python -m flake8 streamlit_app tests benchmark --count --statistics
if ($LASTEXITCODE -ne 0) { Write-Host "Lint failed" -ForegroundColor Red; exit 1 }
Write-Host "All checks passed" -ForegroundColor Green
