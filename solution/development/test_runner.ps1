# Test Runner for Solution 2 (PowerShell)
# Run this from the repository root

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Box Box Box - Test Runner (Solution 2)            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$TEST_CASES_DIR = "data\test_cases\inputs"
$EXPECTED_OUTPUTS_DIR = "data\test_cases\expected_outputs"
$RUN_COMMAND_FILE = "solution2\run_command.txt"

# Read solution command
if (-not (Test-Path $RUN_COMMAND_FILE)) {
    Write-Host "Error: Run command file not found" -ForegroundColor Red
    exit 1
}

$SOLUTION_CMD = (Get-Content $RUN_COMMAND_FILE -Raw).Trim()
Write-Host "Solution Command: $SOLUTION_CMD" -ForegroundColor Yellow

# Get test files
$TEST_FILES = Get-ChildItem "$TEST_CASES_DIR\test_*.json" | Sort-Object Name
$TOTAL_TESTS = $TEST_FILES.Count
Write-Host "Test Cases Found: $TOTAL_TESTS" -ForegroundColor Yellow
Write-Host ""
Write-Host "Running tests..." -ForegroundColor Cyan
Write-Host ""

$PASSED = 0
$FAILED = 0
$ERRORS = 0
$HAS_ANSWERS = Test-Path $EXPECTED_OUTPUTS_DIR

foreach ($TEST_FILE in $TEST_FILES) {
    $TEST_NAME = $TEST_FILE.BaseName
    $TEST_ID = $TEST_NAME -replace 'test_', 'TEST_'
    
    try {
        $content = Get-Content $TEST_FILE -Raw
        
        # Run solution
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = "cmd.exe"
        $processInfo.Arguments = "/c `"$SOLUTION_CMD`""
        $processInfo.RedirectStandardInput = $true
        $processInfo.RedirectStandardOutput = $true
        $processInfo.RedirectStandardError = $true
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = $true
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $processInfo
        $process.Start() | Out-Null
        $process.StandardInput.WriteLine($content)
        $process.StandardInput.Close()
        $output = $process.StandardOutput.ReadToEnd()
        $process.WaitForExit()
        
        if ($process.ExitCode -eq 0) {
            try {
                $jsonOutput = $output | ConvertFrom-Json
                $PREDICTED = ($jsonOutput.finishing_positions -join ",")
                
                if ([string]::IsNullOrEmpty($PREDICTED)) {
                    Write-Host "✗ $TEST_ID - Invalid output format" -ForegroundColor Red
                    $FAILED++
                }
                elseif ($HAS_ANSWERS) {
                    $ANSWER_FILE = Join-Path $EXPECTED_OUTPUTS_DIR "${TEST_NAME}.json"
                    if (Test-Path $ANSWER_FILE) {
                        $expectedContent = Get-Content $ANSWER_FILE -Raw
                        $expectedJson = $expectedContent | ConvertFrom-Json
                        $EXPECTED = ($expectedJson.finishing_positions -join ",")
                        
                        if ($PREDICTED -eq $EXPECTED) {
                            Write-Host "✓ $TEST_ID" -ForegroundColor Green
                            $PASSED++
                        }
                        else {
                            Write-Host "✗ $TEST_ID - Incorrect prediction" -ForegroundColor Red
                            $FAILED++
                        }
                    }
                    else {
                        Write-Host "? $TEST_ID - No answer file" -ForegroundColor Yellow
                        $PASSED++
                    }
                }
                else {
                    Write-Host "? $TEST_ID - Format OK" -ForegroundColor Yellow
                    $PASSED++
                }
            }
            catch {
                Write-Host "✗ $TEST_ID - Invalid JSON" -ForegroundColor Red
                $FAILED++
            }
        }
        else {
            Write-Host "✗ $TEST_ID - Execution error" -ForegroundColor Red
            $ERRORS++
        }
    }
    catch {
        Write-Host "✗ $TEST_ID - Error: $($_.Exception.Message)" -ForegroundColor Red
        $ERRORS++
    }
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    Results                             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "Total Tests:    $TOTAL_TESTS" -ForegroundColor White
Write-Host "Passed:         $PASSED" -ForegroundColor Green
Write-Host "Failed:         $FAILED" -ForegroundColor Red
if ($ERRORS -gt 0) {
    Write-Host "Errors:         $ERRORS" -ForegroundColor Red
}

if ($TOTAL_TESTS -gt 0) {
    $PASS_RATE = [math]::Round(($PASSED * 100) / $TOTAL_TESTS, 1)
    Write-Host ""
    Write-Host "Pass Rate:      $PASS_RATE%" -ForegroundColor Green
}

Write-Host ""
if ($PASSED -eq $TOTAL_TESTS) {
    Write-Host "🏆 Perfect score! All tests passed!" -ForegroundColor Green
}
elseif ($PASSED -gt 0) {
    Write-Host "Keep improving! Check failed test cases." -ForegroundColor Yellow
}
else {
    Write-Host "No tests passed. Review your implementation." -ForegroundColor Red
}

Write-Host ""
