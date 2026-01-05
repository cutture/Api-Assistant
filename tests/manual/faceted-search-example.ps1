# Example: Faceted Search in PowerShell
# This demonstrates how to perform faceted search with PowerShell

$baseUrl = "http://localhost:8000"

# Build the request body
$bodyObject = @{
    query = "api"
    facet_fields = @("method", "format", "source")
    n_results = 20
}

# Convert to JSON
$jsonBody = $bodyObject | ConvertTo-Json -Depth 10

# Display the request
Write-Host "Sending POST request to /search/faceted" -ForegroundColor Cyan
Write-Host "Request Body:" -ForegroundColor Yellow
Write-Host $jsonBody -ForegroundColor Gray
Write-Host ""

# Send the request
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/search/faceted" `
        -Method Post `
        -ContentType "application/json" `
        -Body $jsonBody

    # Display the response
    Write-Host "Response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    Write-Host "Status Description: $($_.Exception.Response.StatusDescription)" -ForegroundColor Yellow
}
