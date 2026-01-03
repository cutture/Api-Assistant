# API Assistant - PowerShell API Testing Script
# Compatible with PowerShell 5.1 and 7.0+
#
# Usage:
#   1. Make sure backend is running: uvicorn src.api.app:app --reload --port 8000
#   2. Run individual test functions or the entire script
#   3. Update document IDs and file paths as needed

$baseUrl = "http://localhost:8000"

# Helper function to display test results
function Show-TestResult {
    param(
        [string]$TestName,
        [object]$Response
    )
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Test: $TestName" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    $Response | ConvertTo-Json -Depth 10
    Write-Host ""
}

# ============================================================================
# HEALTH & STATS TESTS
# ============================================================================

function Test-HealthCheck {
    Write-Host "Running: Health Check" -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "$baseUrl/health"
    Show-TestResult -TestName "Health Check" -Response $response
}

function Test-Stats {
    Write-Host "Running: Get Statistics" -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "$baseUrl/stats"
    Show-TestResult -TestName "Statistics" -Response $response
}

# ============================================================================
# DOCUMENT UPLOAD TESTS
# ============================================================================

function Test-UploadOpenAPI {
    param([string]$FilePath = "examples/sample-openapi.json")

    Write-Host "Running: Upload OpenAPI Specification" -ForegroundColor Yellow

    # PowerShell 7.0+ version (comment out if using PS 5.1)
    # $response = Invoke-RestMethod -Uri "$baseUrl/documents/upload" -Method Post -Form @{files = Get-Item $FilePath}

    # PowerShell 5.1 compatible version
    $boundary = [System.Guid]::NewGuid().ToString()
    $fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $FilePath).Path)
    $fileName = Split-Path $FilePath -Leaf
    $LF = "`r`n"
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"files`"; filename=`"$fileName`"",
        "Content-Type: application/json",
        "",
        [System.Text.Encoding]::UTF8.GetString($fileBytes),
        "--$boundary--"
    ) -join $LF

    $response = Invoke-RestMethod -Uri "$baseUrl/documents/upload" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $bodyLines

    Show-TestResult -TestName "Upload OpenAPI" -Response $response
    return $response
}

function Test-UploadPDF {
    param([string]$FilePath = "examples/test.pdf")

    Write-Host "Running: Upload PDF Document" -ForegroundColor Yellow

    if (-not (Test-Path $FilePath)) {
        Write-Host "Error: PDF file not found at $FilePath" -ForegroundColor Red
        return
    }

    $boundary = [System.Guid]::NewGuid().ToString()
    $fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $FilePath).Path)
    $fileName = Split-Path $FilePath -Leaf
    $LF = "`r`n"
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"files`"; filename=`"$fileName`"",
        "Content-Type: application/pdf",
        "",
        [System.Text.Encoding]::UTF8.GetString($fileBytes),
        "--$boundary--"
    ) -join $LF

    $response = Invoke-RestMethod -Uri "$baseUrl/documents/upload" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $bodyLines

    Show-TestResult -TestName "Upload PDF" -Response $response
    return $response
}

function Test-UploadText {
    param([string]$FilePath = "examples/sample-text.txt")

    Write-Host "Running: Upload Text File" -ForegroundColor Yellow

    $boundary = [System.Guid]::NewGuid().ToString()
    $fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $FilePath).Path)
    $fileName = Split-Path $FilePath -Leaf
    $LF = "`r`n"
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"files`"; filename=`"$fileName`"",
        "Content-Type: text/plain",
        "",
        [System.Text.Encoding]::UTF8.GetString($fileBytes),
        "--$boundary--"
    ) -join $LF

    $response = Invoke-RestMethod -Uri "$baseUrl/documents/upload" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $bodyLines

    Show-TestResult -TestName "Upload Text File" -Response $response
    return $response
}

function Test-UploadMarkdown {
    param([string]$FilePath = "examples/sample-markdown.md")

    Write-Host "Running: Upload Markdown File" -ForegroundColor Yellow

    $boundary = [System.Guid]::NewGuid().ToString()
    $fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $FilePath).Path)
    $fileName = Split-Path $FilePath -Leaf
    $LF = "`r`n"
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"files`"; filename=`"$fileName`"",
        "Content-Type: text/markdown",
        "",
        [System.Text.Encoding]::UTF8.GetString($fileBytes),
        "--$boundary--"
    ) -join $LF

    $response = Invoke-RestMethod -Uri "$baseUrl/documents/upload" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $bodyLines

    Show-TestResult -TestName "Upload Markdown" -Response $response
    return $response
}

function Test-UploadJSON {
    param([string]$FilePath = "examples/sample-data.json")

    Write-Host "Running: Upload Generic JSON" -ForegroundColor Yellow

    $boundary = [System.Guid]::NewGuid().ToString()
    $fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $FilePath).Path)
    $fileName = Split-Path $FilePath -Leaf
    $LF = "`r`n"
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"files`"; filename=`"$fileName`"",
        "Content-Type: application/json",
        "",
        [System.Text.Encoding]::UTF8.GetString($fileBytes),
        "--$boundary--"
    ) -join $LF

    $response = Invoke-RestMethod -Uri "$baseUrl/documents/upload" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $bodyLines

    Show-TestResult -TestName "Upload Generic JSON" -Response $response
    return $response
}

function Test-BatchUpload {
    param(
        [string[]]$FilePaths = @(
            "examples/sample-openapi.json",
            "examples/sample-text.txt",
            "examples/sample-markdown.md"
        )
    )

    Write-Host "Running: Batch Upload Multiple Files" -ForegroundColor Yellow

    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    $bodyLines = @()

    foreach ($filePath in $FilePaths) {
        if (-not (Test-Path $filePath)) {
            Write-Host "Warning: File not found - $filePath" -ForegroundColor Yellow
            continue
        }

        $fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $filePath).Path)
        $fileName = Split-Path $filePath -Leaf

        $contentType = switch ([System.IO.Path]::GetExtension($filePath)) {
            ".json" { "application/json" }
            ".txt"  { "text/plain" }
            ".md"   { "text/markdown" }
            ".pdf"  { "application/pdf" }
            default { "application/octet-stream" }
        }

        $bodyLines += "--$boundary"
        $bodyLines += "Content-Disposition: form-data; name=`"files`"; filename=`"$fileName`""
        $bodyLines += "Content-Type: $contentType"
        $bodyLines += ""
        $bodyLines += [System.Text.Encoding]::UTF8.GetString($fileBytes)
    }

    $bodyLines += "--$boundary--"
    $body = $bodyLines -join $LF

    $response = Invoke-RestMethod -Uri "$baseUrl/documents/upload" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $body

    Show-TestResult -TestName "Batch Upload" -Response $response
    return $response
}

# ============================================================================
# DOCUMENT MANAGEMENT TESTS
# ============================================================================

function Test-GetDocument {
    param([string]$DocumentId)

    Write-Host "Running: Get Document by ID" -ForegroundColor Yellow

    $response = Invoke-RestMethod -Uri "$baseUrl/documents/$DocumentId"
    Show-TestResult -TestName "Get Document" -Response $response
    return $response
}

function Test-DeleteDocument {
    param([string]$DocumentId)

    Write-Host "Running: Delete Document" -ForegroundColor Yellow

    $response = Invoke-RestMethod -Uri "$baseUrl/documents/$DocumentId" -Method Delete
    Show-TestResult -TestName "Delete Document" -Response $response
    return $response
}

function Test-BulkDelete {
    param([string[]]$DocumentIds)

    Write-Host "Running: Bulk Delete Documents" -ForegroundColor Yellow

    $bodyObject = @{
        document_ids = $DocumentIds
    }

    $jsonBody = $bodyObject | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod -Uri "$baseUrl/documents/bulk-delete" `
        -Method Post `
        -ContentType "application/json" `
        -Body $jsonBody

    Show-TestResult -TestName "Bulk Delete" -Response $response
    return $response
}

# ============================================================================
# SEARCH TESTS
# ============================================================================

function Test-VectorSearch {
    param(
        [string]$Query = "user authentication",
        [int]$NResults = 5
    )

    Write-Host "Running: Vector Search" -ForegroundColor Yellow

    $bodyObject = @{
        query = $Query
        mode = "vector"
        n_results = $NResults
    }

    $jsonBody = $bodyObject | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod -Uri "$baseUrl/search" `
        -Method Post `
        -ContentType "application/json" `
        -Body $jsonBody

    Show-TestResult -TestName "Vector Search" -Response $response
    return $response
}

function Test-HybridSearch {
    param(
        [string]$Query = "GET request users",
        [int]$NResults = 10
    )

    Write-Host "Running: Hybrid Search" -ForegroundColor Yellow

    $bodyObject = @{
        query = $Query
        mode = "hybrid"
        n_results = $NResults
    }

    $jsonBody = $bodyObject | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod -Uri "$baseUrl/search" `
        -Method Post `
        -ContentType "application/json" `
        -Body $jsonBody

    Show-TestResult -TestName "Hybrid Search" -Response $response
    return $response
}

function Test-KeywordSearch {
    param(
        [string]$Query = "authentication endpoint",
        [int]$NResults = 5
    )

    Write-Host "Running: Keyword Search" -ForegroundColor Yellow

    $bodyObject = @{
        query = $Query
        mode = "keyword"
        n_results = $NResults
    }

    $jsonBody = $bodyObject | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod -Uri "$baseUrl/search" `
        -Method Post `
        -ContentType "application/json" `
        -Body $jsonBody

    Show-TestResult -TestName "Keyword Search" -Response $response
    return $response
}

function Test-FacetedSearch {
    param(
        [string]$Query = "users",
        [string[]]$FacetFields = @("method", "format", "source"),
        [int]$NResults = 20
    )

    Write-Host "Running: Faceted Search" -ForegroundColor Yellow

    $bodyObject = @{
        query = $Query
        facet_fields = $FacetFields
        n_results = $NResults
    }

    $jsonBody = $bodyObject | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod -Uri "$baseUrl/search/faceted" `
        -Method Post `
        -ContentType "application/json" `
        -Body $jsonBody

    Show-TestResult -TestName "Faceted Search" -Response $response
    return $response
}

function Test-SearchWithFilter {
    param(
        [string]$Query = "user",
        [string]$Mode = "vector",
        [string]$Field = "method",
        [string]$Operator = "eq",
        [string]$Value = "GET",
        [int]$NResults = 5
    )

    Write-Host "Running: Search with Filter" -ForegroundColor Yellow

    $bodyObject = @{
        query = $Query
        mode = $Mode
        n_results = $NResults
        filter = @{
            field = $Field
            operator = $Operator
            value = $Value
        }
    }

    $jsonBody = $bodyObject | ConvertTo-Json -Depth 10

    Write-Host "Request Body:" -ForegroundColor Yellow
    Write-Host $jsonBody -ForegroundColor Gray

    $response = Invoke-RestMethod -Uri "$baseUrl/search" `
        -Method Post `
        -ContentType "application/json" `
        -Body $jsonBody

    Show-TestResult -TestName "Search with Filter" -Response $response
    return $response
}

# ============================================================================
# CHAT TESTS
# ============================================================================

function Test-ChatBasic {
    param([string]$Message = "What APIs are available?")

    Write-Host "Running: Basic Chat" -ForegroundColor Yellow

    # Chat endpoint expects multipart/form-data, not JSON
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    $bodyLines = @()

    # Add message field
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"message`""
    $bodyLines += ""
    $bodyLines += $Message

    # Add enable_url_scraping field
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"enable_url_scraping`""
    $bodyLines += ""
    $bodyLines += "false"

    # Add enable_auto_indexing field
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"enable_auto_indexing`""
    $bodyLines += ""
    $bodyLines += "false"

    $bodyLines += "--$boundary--"
    $body = $bodyLines -join $LF

    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/chat" `
            -Method Post `
            -ContentType "multipart/form-data; boundary=$boundary" `
            -Body $body

        Show-TestResult -TestName "Basic Chat" -Response $response
        return $response
    }
    catch {
        Write-Host "Error: $_" -ForegroundColor Red
        throw
    }
}

function Test-ChatWithContext {
    param(
        [string]$Message = "How do I authenticate?",
        [string]$SessionId = ""
    )

    Write-Host "Running: Chat with Context" -ForegroundColor Yellow

    # Chat endpoint expects multipart/form-data, not JSON
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    $bodyLines = @()

    # Add message field
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"message`""
    $bodyLines += ""
    $bodyLines += $Message

    # Add session_id field if provided
    if ($SessionId) {
        $bodyLines += "--$boundary"
        $bodyLines += "Content-Disposition: form-data; name=`"session_id`""
        $bodyLines += ""
        $bodyLines += $SessionId
    }

    # Add enable_url_scraping field
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"enable_url_scraping`""
    $bodyLines += ""
    $bodyLines += "true"

    # Add enable_auto_indexing field
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"enable_auto_indexing`""
    $bodyLines += ""
    $bodyLines += "true"

    $bodyLines += "--$boundary--"
    $body = $bodyLines -join $LF

    $response = Invoke-RestMethod -Uri "$baseUrl/chat" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $body

    Show-TestResult -TestName "Chat with Context" -Response $response
    return $response
}

function Test-ChatWithFileUpload {
    param(
        [string]$Message = "Explain this document",
        [string]$FilePath = "examples/sample-text.txt"
    )

    Write-Host "Running: Chat with File Upload" -ForegroundColor Yellow

    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    $bodyLines = @()

    # Add message field
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"message`""
    $bodyLines += ""
    $bodyLines += $Message

    # Add enable_auto_indexing field
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"enable_auto_indexing`""
    $bodyLines += ""
    $bodyLines += "true"

    # Add file
    if (Test-Path $FilePath) {
        $fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $FilePath).Path)
        $fileName = Split-Path $FilePath -Leaf
        $contentType = switch ([System.IO.Path]::GetExtension($FilePath)) {
            ".json" { "application/json" }
            ".txt"  { "text/plain" }
            ".md"   { "text/markdown" }
            ".pdf"  { "application/pdf" }
            default { "application/octet-stream" }
        }

        $bodyLines += "--$boundary"
        $bodyLines += "Content-Disposition: form-data; name=`"files`"; filename=`"$fileName`""
        $bodyLines += "Content-Type: $contentType"
        $bodyLines += ""
        $bodyLines += [System.Text.Encoding]::UTF8.GetString($fileBytes)
    }

    $bodyLines += "--$boundary--"
    $body = $bodyLines -join $LF

    $response = Invoke-RestMethod -Uri "$baseUrl/chat" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $body

    Show-TestResult -TestName "Chat with File Upload" -Response $response
    return $response
}

# ============================================================================
# SESSION MANAGEMENT TESTS
# ============================================================================

function Test-CreateSession {
    Write-Host "Running: Create Session" -ForegroundColor Yellow

    $bodyObject = @{
        title = "Test Session"
        agent_type = "general"
    }

    $jsonBody = $bodyObject | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod -Uri "$baseUrl/sessions" `
        -Method Post `
        -ContentType "application/json" `
        -Body $jsonBody

    Show-TestResult -TestName "Create Session" -Response $response
    return $response
}

function Test-ListSessions {
    param([int]$Limit = 10)

    Write-Host "Running: List Sessions" -ForegroundColor Yellow

    $response = Invoke-RestMethod -Uri "$baseUrl/sessions?limit=$Limit"
    Show-TestResult -TestName "List Sessions" -Response $response
    return $response
}

function Test-GetSession {
    param([string]$SessionId)

    Write-Host "Running: Get Session" -ForegroundColor Yellow

    $response = Invoke-RestMethod -Uri "$baseUrl/sessions/$SessionId"
    Show-TestResult -TestName "Get Session" -Response $response
    return $response
}

function Test-UpdateSession {
    param(
        [string]$SessionId,
        [string]$Title = "Updated Session Title"
    )

    Write-Host "Running: Update Session" -ForegroundColor Yellow

    $bodyObject = @{
        title = $Title
    }

    $jsonBody = $bodyObject | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod -Uri "$baseUrl/sessions/$SessionId" `
        -Method Patch `
        -ContentType "application/json" `
        -Body $jsonBody

    Show-TestResult -TestName "Update Session" -Response $response
    return $response
}

function Test-DeleteSession {
    param([string]$SessionId)

    Write-Host "Running: Delete Session" -ForegroundColor Yellow

    $response = Invoke-RestMethod -Uri "$baseUrl/sessions/$SessionId" -Method Delete
    Show-TestResult -TestName "Delete Session" -Response $response
    return $response
}

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

function Run-AllTests {
    Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  API Assistant - PowerShell Test Suite                    ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

    # Health & Stats
    Test-HealthCheck
    Test-Stats

    # Document Uploads
    Test-UploadOpenAPI
    Test-UploadText
    Test-UploadMarkdown
    Test-UploadJSON

    # Search
    Test-VectorSearch
    Test-HybridSearch

    # Chat
    Test-ChatBasic

    # Sessions
    $session = Test-CreateSession
    if ($session.session_id) {
        Test-GetSession -SessionId $session.session_id
        Test-UpdateSession -SessionId $session.session_id
    }

    Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  All Tests Completed!                                      ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green
}

# ============================================================================
# EXAMPLES - Uncomment to run specific tests
# ============================================================================

# Example 1: Run all tests
# Run-AllTests

# Example 2: Run individual tests
# Test-HealthCheck
# Test-UploadOpenAPI
# Test-HybridSearch -Query "GET request users" -NResults 10

# Example 3: Upload and then search
# $uploadResult = Test-UploadOpenAPI
# Test-VectorSearch -Query "authentication" -NResults 5

# Example 4: Bulk delete with specific IDs
# Test-BulkDelete -DocumentIds @("id1", "id2", "id3")

Write-Host "`nPowerShell API Test Suite Loaded!" -ForegroundColor Green
Write-Host "Run 'Run-AllTests' to execute all tests" -ForegroundColor Cyan
Write-Host "Or run individual test functions like 'Test-HealthCheck'" -ForegroundColor Cyan
Write-Host "Type 'Get-Command Test-*' to see all available test functions`n" -ForegroundColor Cyan
