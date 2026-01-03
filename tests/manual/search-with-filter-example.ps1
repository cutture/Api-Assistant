# Example: Search with Filter in PowerShell
# This demonstrates how to properly perform a filtered search using PowerShell

$baseUrl = "http://localhost:8000"

# Build the request body as a PowerShell hashtable
$bodyObject = @{
    query = "user"
    mode = "vector"
    n_results = 5
    filter = @{
        field = "method"
        operator = "eq"
        value = "GET"
    }
}

# Convert to JSON with proper depth to handle nested objects
$jsonBody = $bodyObject | ConvertTo-Json -Depth 10

# Display the request for debugging
Write-Host "Sending POST request to /search" -ForegroundColor Cyan
Write-Host "Request Body:" -ForegroundColor Yellow
Write-Host $jsonBody -ForegroundColor Gray
Write-Host ""

# Send the request
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/search" `
        -Method Post `
        -ContentType "application/json" `
        -Body $jsonBody

    # Display the response
    Write-Host "Response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Yellow
    }
}
