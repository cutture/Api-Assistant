# Example: Generate Sequence Diagram in PowerShell
# This demonstrates the two-step process: upload document, then generate diagram

$baseUrl = "http://localhost:8000"

Write-Host "Step 1: Upload OpenAPI file to get document ID" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# File to upload
$filePath = "examples/sample-openapi.json"

if (-not (Test-Path $filePath)) {
    Write-Host "Error: File not found at $filePath" -ForegroundColor Red
    Write-Host "Please ensure you're running this from the project root directory." -ForegroundColor Yellow
    exit 1
}

# Construct multipart/form-data for file upload
$boundary = [System.Guid]::NewGuid().ToString()
$fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $filePath).Path)
$fileName = Split-Path $filePath -Leaf
$LF = "`r`n"
$bodyLines = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"files`"; filename=`"$fileName`"",
    "Content-Type: application/json",
    "",
    [System.Text.Encoding]::UTF8.GetString($fileBytes),
    "--$boundary--"
) -join $LF

try {
    # Upload the file
    Write-Host "Uploading: $filePath" -ForegroundColor Yellow
    $uploadResponse = Invoke-RestMethod -Uri "$baseUrl/documents/upload" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $bodyLines

    # Get the first document ID
    $documentId = $uploadResponse.document_ids[0]
    Write-Host "Success! Document uploaded." -ForegroundColor Green
    Write-Host "Document ID: $documentId" -ForegroundColor Cyan
    Write-Host "Total documents uploaded: $($uploadResponse.count)" -ForegroundColor Gray
    Write-Host ""
}
catch {
    Write-Host "Error uploading file: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Step 2: Generate sequence diagram using document ID" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# Build request for sequence diagram
$body = @{
    endpoint_id = $documentId
} | ConvertTo-Json -Depth 10

try {
    Write-Host "Generating sequence diagram..." -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "$baseUrl/diagrams/sequence" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body

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
    Write-Host "Error generating diagram: $_" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    Write-Host "Status Description: $($_.Exception.Response.StatusDescription)" -ForegroundColor Yellow
}
