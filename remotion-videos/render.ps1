param(
    [Parameter(Mandatory=$true)]
    [string]$CompositionName
)

Write-Host "Rendering Remotion video: $CompositionName" -ForegroundColor Cyan
npx remotion render $CompositionName --codec=h264 --crf=18 --pixel-format=yuv420p --output="output/$CompositionName.mp4"
Write-Host "Done! Video saved to output/$CompositionName.mp4" -ForegroundColor Green
