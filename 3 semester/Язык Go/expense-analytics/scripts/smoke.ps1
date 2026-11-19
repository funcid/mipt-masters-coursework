$ErrorActionPreference = 'Stop'
$base = 'http://localhost:8080'

Write-Host "== ping =="
Invoke-RestMethod "$base/ping" | ConvertTo-Json -Compress

$email = "demo+$([guid]::NewGuid().ToString('N').Substring(0,8))@example.com"
$authBody = @{ email = $email; password = 'secret123'; name = 'Demo' } | ConvertTo-Json
Write-Host "== register $email =="
$reg = Invoke-RestMethod -Method Post -Uri "$base/api/auth/register" -ContentType 'application/json' -Body $authBody
$token = $reg.access_token
$headers = @{ Authorization = "Bearer $token" }

Write-Host "== budget =="
Invoke-RestMethod -Method Post -Uri "$base/api/budgets" -Headers $headers -ContentType 'application/json' `
  -Body (@{ category = 'food'; limit_amount = 1000; period = 'monthly' } | ConvertTo-Json) | ConvertTo-Json -Compress

Write-Host "== transaction ok =="
Invoke-RestMethod -Method Post -Uri "$base/api/transactions" -Headers $headers -ContentType 'application/json' `
  -Body (@{ amount = 400; category = 'food'; description = 'lunch'; date = '2024-05-01' } | ConvertTo-Json) | ConvertTo-Json -Compress

Write-Host "== transaction over budget (expect 409) =="
try {
  Invoke-RestMethod -Method Post -Uri "$base/api/transactions" -Headers $headers -ContentType 'application/json' `
    -Body (@{ amount = 700; category = 'food'; description = 'dinner'; date = '2024-05-02' } | ConvertTo-Json)
} catch {
  Write-Host "status:" ([int]$_.Exception.Response.StatusCode)
}

Write-Host "== report miss/hit =="
$r1 = Invoke-RestMethod -Uri "$base/api/reports/summary?from=2024-05-01&to=2024-05-31" -Headers $headers
$r2 = Invoke-RestMethod -Uri "$base/api/reports/summary?from=2024-05-01&to=2024-05-31" -Headers $headers
Write-Host "first cache_hit=$($r1.cache_hit) total=$($r1.total_spent)"
Write-Host "second cache_hit=$($r2.cache_hit) total=$($r2.total_spent)"
Write-Host "SMOKE OK"
