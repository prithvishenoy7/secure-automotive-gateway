# Quick Test Script for CAN Gateway MQTT Publisher (PowerShell)

Write-Host "=== Docker Container Status ===" -ForegroundColor Cyan
docker-compose ps

Write-Host "`n=== Health Check ===" -ForegroundColor Cyan
$health = Invoke-RestMethod -Uri http://localhost:5000/health -Method GET
$health | ConvertTo-Json -Depth 3

Write-Host "`n=== Manual Publish Test ===" -ForegroundColor Cyan
$testPayload = @{
    test = "verification"
    timestamp = [int][double]::Parse((Get-Date -UFormat %s))
} | ConvertTo-Json

$publishResult = Invoke-RestMethod -Uri http://localhost:5000/publish -Method POST -ContentType "application/json" -Body $testPayload
$publishResult | ConvertTo-Json -Depth 3

Write-Host "`n=== Recent Logs ===" -ForegroundColor Cyan
docker-compose logs --tail=20

Write-Host "`n=== Instructions ===" -ForegroundColor Yellow
Write-Host "1. Check AWS IoT Console MQTT test client"
Write-Host "2. Subscribe to: vehicle/can-gateway/telemetry"
Write-Host "3. You should see the test message above"
