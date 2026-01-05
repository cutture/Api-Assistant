# Example: Generate ER Diagram from GraphQL Schema in PowerShell
# This demonstrates how to generate ER diagrams with PowerShell

$baseUrl = "http://localhost:8000"

# Read the GraphQL schema file
$schemaPath = "examples/graphql/schema.graphql"

if (-not (Test-Path $schemaPath)) {
    Write-Host "Error: Schema file not found at $schemaPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "A sample GraphQL schema file should exist at this path." -ForegroundColor Yellow
    Write-Host "Please ensure you're running this from the project root directory." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Current directory: $PWD" -ForegroundColor Cyan
    Write-Host "Expected file: $((Resolve-Path .).Path)\$schemaPath" -ForegroundColor Cyan
    exit 1
}

Write-Host "Reading GraphQL schema from: $schemaPath" -ForegroundColor Cyan
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
Write-Host "Schema length: $($schemaContent.Length) characters" -ForegroundColor Yellow
Write-Host ""

# Send the request
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/diagrams/er" `
        -Method Post `
        -ContentType "application/json" `
        -Body $jsonBody

    # Display the response
    Write-Host "Success!" -ForegroundColor Green
    Write-Host "Diagram Type: $($response.diagram_type)" -ForegroundColor Cyan
    Write-Host "Title: $($response.title)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Mermaid Code:" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host $response.mermaid_code -ForegroundColor White
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host ""
    Write-Host "You can paste this Mermaid code into:" -ForegroundColor Cyan
    Write-Host "- https://mermaid.live" -ForegroundColor Yellow
    Write-Host "- Any Markdown file with Mermaid support" -ForegroundColor Yellow
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    Write-Host "Status Description: $($_.Exception.Response.StatusDescription)" -ForegroundColor Yellow
}
