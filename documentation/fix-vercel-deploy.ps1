# Push deployment configuration

Write-Host "🚀 Pushing deployment setup..." -ForegroundColor Yellow
Write-Host ""

# Add all changes
Write-Host "📝 Staging changes..." -ForegroundColor Cyan
git add .

# Commit
Write-Host "💾 Committing..." -ForegroundColor Cyan
git commit -m "Setup separate deployments: Frontend (Vercel) + Backend (Railway)

- Add .vercelignore to exclude heavy files (venv, data)
- Move vercel.json to frontend/ directory
- Add SIMPLE_DEPLOYMENT.md with step-by-step guide
- Update README.md with deployment info
- Frontend: Vercel (React/Vite)
- Backend: Railway (FastAPI)"

# Push
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Cyan
git push

Write-Host ""
Write-Host "✅ Configuration pushed!" -ForegroundColor Green
Write-Host ""
Write-Host "📖 Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Deploy FRONTEND to Vercel:" -ForegroundColor Cyan
Write-Host "   → Go to: https://vercel.com/new" -ForegroundColor White
Write-Host "   → Import: Mettice/Node-AI" -ForegroundColor White
Write-Host "   → Root: frontend/" -ForegroundColor White
Write-Host "   -> Deploy OK" -ForegroundColor White
Write-Host ""
Write-Host "2. Deploy BACKEND to Railway:" -ForegroundColor Cyan
Write-Host "   → Go to: https://railway.app/new" -ForegroundColor White
Write-Host "   → Import: Mettice/Node-AI" -ForegroundColor White
Write-Host "   → Add env vars (see SIMPLE_DEPLOYMENT.md)" -ForegroundColor White
Write-Host "   -> Deploy OK" -ForegroundColor White
Write-Host ""
Write-Host "📖 Full guide: SIMPLE_DEPLOYMENT.md" -ForegroundColor Magenta
Write-Host ""
Write-Host "Time: ~10 minutes total" -ForegroundColor Gray

