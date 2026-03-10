# Quick Railway health check script for Windows
# Usage: .\check_railway.ps1 https://your-railway-url

param(
    [Parameter(Mandatory=$true)]
    [string]$RailwayUrl
)

Write-Host "🔍 Testing Railway Backend: $RailwayUrl" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
Write-Host "Endpoint: $RailwayUrl/healthz"
try {
    $healthResponse = Invoke-RestMethod -Uri "$RailwayUrl/healthz" -Method Get
    Write-Host "Response: $($healthResponse | ConvertTo-Json -Compress)"
    
    if ($healthResponse.status -eq "ok") {
        Write-Host "✅ Health check PASSED" -ForegroundColor Green
    } else {
        Write-Host "❌ Health check FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Health check FAILED: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Database connection
Write-Host "Test 2: Database Connection" -ForegroundColor Yellow
Write-Host "Endpoint: $RailwayUrl/api/health/db"
try {
    $dbResponse = Invoke-RestMethod -Uri "$RailwayUrl/api/health/db" -Method Get
    Write-Host "Response: $($dbResponse | ConvertTo-Json -Compress)"
    
    if ($dbResponse.database -eq "connected") {
        Write-Host "✅ Database connection PASSED" -ForegroundColor Green
    } else {
        Write-Host "❌ Database connection FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Database connection FAILED: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Chat endpoint
Write-Host "Test 3: Chat Endpoint" -ForegroundColor Yellow
Write-Host "Endpoint: $RailwayUrl/api/chat/stream"
Write-Host "Question: What is a contract?"
try {
    $body = @{
        question = "What is a contract?"
        country = "US"
    } | ConvertTo-Json
    
    $chatResponse = Invoke-RestMethod -Uri "$RailwayUrl/api/chat/stream" -Method Post -Body $body -ContentType "application/json"
    
    if ($chatResponse) {
        Write-Host "✅ Chat endpoint RESPONDING" -ForegroundColor Green
        $preview = $chatResponse.Substring(0, [Math]::Min(100, $chatResponse.Length))
        Write-Host "Response preview: $preview..."
    }
} catch {
    Write-Host "❌ Chat endpoint ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ Railway backend validation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next step: Deploy to Vercel" -ForegroundColor Cyan
Write-Host "  1. Go to https://vercel.com"
Write-Host "  2. Import your GitHub repo"
Write-Host "  3. Set root directory to 'frontend'"
Write-Host "  4. Add environment variable:"
Write-Host "     NEXT_PUBLIC_BACKEND_URL=$RailwayUrl" -ForegroundColor Yellow
Write-Host "  5. Deploy!"
