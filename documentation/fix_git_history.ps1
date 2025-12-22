# PowerShell script to remove user workflow from git history
# This will remove the file with the API key from all commits

Write-Host "Removing user workflow from git history..." -ForegroundColor Yellow
Write-Host "This will rewrite git history. Make sure you're on the correct branch!" -ForegroundColor Red

# Remove the file from all commits in history
git filter-branch --force --index-filter `
  "git rm --cached --ignore-unmatch backend/data/workflows/a118eef6-45e8-4a0a-888d-3e6e61452b0c.json" `
  --prune-empty --tag-name-filter cat -- ui

Write-Host "`nCleaning up git references..." -ForegroundColor Yellow
git reflog expire --expire=now --all
git gc --prune=now --aggressive

Write-Host "`nDone! Now you can force push:" -ForegroundColor Green
Write-Host "  git push origin ui --force" -ForegroundColor Cyan
Write-Host "`n⚠️  WARNING: Force push rewrites history. Coordinate with your team!" -ForegroundColor Red
Write-Host "⚠️  IMPORTANT: Rotate the exposed API key immediately!" -ForegroundColor Red

