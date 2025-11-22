# Quick script to commit TypeScript fixes

Write-Host "📝 Committing TypeScript fixes..." -ForegroundColor Yellow

git add .
git commit -m "Fix TypeScript errors for Vercel deployment

- Update ExecutionStep interface with missing properties
- Replace toast.info() with toast() (react-hot-toast fix)
- Disable noUnusedLocals/noUnusedParameters for build
- Fix test utils type imports (verbatimModuleSyntax)
- Update cacheTime to gcTime (React Query v5)"

git push

Write-Host "✅ Fixes pushed! Vercel will auto-redeploy." -ForegroundColor Green

