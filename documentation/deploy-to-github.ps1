# NodeAI - Deploy to GitHub Script
# Run this from the project root directory

Write-Host "🚀 NodeAI - GitHub Deployment Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path .git)) {
    Write-Host "📦 Initializing Git repository..." -ForegroundColor Yellow
    git init
    git branch -M main
    Write-Host "✅ Git initialized" -ForegroundColor Green
} else {
    Write-Host "✅ Git already initialized" -ForegroundColor Green
}

# Check if remote exists
$remoteUrl = git remote get-url origin 2>$null
if (-not $remoteUrl) {
    Write-Host "🔗 Adding GitHub remote..." -ForegroundColor Yellow
    git remote add origin https://github.com/Mettice/Node-AI.git
    Write-Host "✅ Remote added" -ForegroundColor Green
} else {
    Write-Host "✅ Remote already configured: $remoteUrl" -ForegroundColor Green
}

# Create .gitkeep files for empty directories
Write-Host ""
Write-Host "📁 Creating .gitkeep files..." -ForegroundColor Yellow

$directories = @(
    "backend\data\executions",
    "backend\data\uploads", 
    "backend\data\vectors",
    "uploads"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created directory: $dir" -ForegroundColor Gray
    }
    
    $gitkeepPath = Join-Path $dir ".gitkeep"
    if (-not (Test-Path $gitkeepPath)) {
        New-Item -ItemType File -Path $gitkeepPath -Force | Out-Null
        Write-Host "  Created: $gitkeepPath" -ForegroundColor Gray
    }
}

Write-Host "✅ .gitkeep files created" -ForegroundColor Green

# Stage files
Write-Host ""
Write-Host "📝 Staging files..." -ForegroundColor Yellow
git add .

# Show status
Write-Host ""
Write-Host "📊 Git Status:" -ForegroundColor Cyan
git status --short

# Commit
Write-Host ""
$commitMessage = Read-Host "Enter commit message (or press Enter for default)"
if ([string]::IsNullOrWhiteSpace($commitMessage)) {
    $commitMessage = "Initial commit: NodeAI v0.1.0 - Beta ready 🚀"
}

Write-Host "💾 Committing changes..." -ForegroundColor Yellow
git commit -m "$commitMessage"

# Push
Write-Host ""
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "⚠️  You may be prompted for GitHub credentials" -ForegroundColor Yellow
Write-Host ""

try {
    git push -u origin main
    Write-Host ""
    Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 Your repo is now at: https://github.com/Mettice/Node-AI" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Deploy frontend to Vercel (see DEPLOYMENT_GUIDE.md)" -ForegroundColor White
    Write-Host "2. Deploy backend to Railway (see DEPLOYMENT_GUIDE.md)" -ForegroundColor White
    Write-Host "3. Configure environment variables" -ForegroundColor White
    Write-Host "4. Test the deployment" -ForegroundColor White
} catch {
    Write-Host ""
    Write-Host "❌ Push failed. Common issues:" -ForegroundColor Red
    Write-Host "1. Not authenticated with GitHub - run: gh auth login" -ForegroundColor Yellow
    Write-Host "2. Repository doesn't exist - create it on GitHub first" -ForegroundColor Yellow
    Write-Host "3. No changes to commit" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Error details: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

