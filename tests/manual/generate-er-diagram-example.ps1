# Example: Generate ER Diagram from GraphQL Schema in PowerShell
# This demonstrates how to generate ER diagrams with PowerShell

$baseUrl = "http://localhost:8000"

# Read the GraphQL schema file
$schemaPath = "examples/graphql/schema.graphql"

if (-not (Test-Path $schemaPath)) {
    Write-Host "Error: Schema file not found at $schemaPath" -ForegroundColor Red
    Write-Host "Please create a GraphQL schema file first or update the path." -ForegroundColor Yellow
    exit 1
}

$schemaContent = Get-Content $schemaPath -Raw

# Build the request body
$bodyObject = @{
    schema_content = $schemaContent
    include_types = @()  # Empty array means include all types
}

# Convert to JSON
$jsonBody = $bodyObject | ConvertTo-Json -Depth 10

# Display the request
Write-Host "Sending POST request to /diagrams/er" -ForegroundColor Cyan
Write-Host "Schema file: $schemaPath" -ForegroundColor Yellow
Write-Host ""

# Send the request
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/diagrams/er" `
        -Method Post `
        -ContentType "application/json" `
        -Body $jsonBody

    # Display the response
    Write-Host "Response:" -ForegroundColor Green
    Write-Host "Diagram Type: $($response.diagram_type)" -ForegroundColor Cyan
    Write-Host "Title: $($response.title)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Mermaid Code:" -ForegroundColor Yellow
    Write-Host $response.mermaid_code -ForegroundColor White
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    Write-Host "Status Description: $($_.Exception.Response.StatusDescription)" -ForegroundColor Yellow
}
