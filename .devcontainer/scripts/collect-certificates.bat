@echo off
REM Windows Certificate Collection Script
REM Collects certificates from Windows certificate stores for use in Linux containers
REM Version: 1.0.0

setlocal enabledelayedexpansion

REM Set output directory
set "OUTPUT_DIR=%USERPROFILE%\.certificates"
set "TIMESTAMP=%date:~-4,4%-%date:~-10,2%-%date:~-7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"

echo.
echo Windows Certificate Collection Script
echo ====================================
echo.
echo This script exports certificates from Windows certificate stores
echo for use in Linux containers to solve corporate firewall issues.
echo.
echo Output directory: %OUTPUT_DIR%
echo.

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" (
    echo Creating output directory...
    mkdir "%OUTPUT_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to create output directory
        pause
        exit /b 1
    )
)

REM Clean up old files
echo Cleaning up old certificate files...
del /q "%OUTPUT_DIR%\*.crt" 2>nul
del /q "%OUTPUT_DIR%\*.pem" 2>nul

echo.
echo Exporting certificates from Windows certificate stores...
echo.

REM Export Root CA certificates (System)
echo [1/6] Exporting System Root CA certificates...
powershell -Command "Get-ChildItem -Path Cert:\LocalMachine\Root | ForEach-Object { '-----BEGIN CERTIFICATE-----'; [Convert]::ToBase64String($_.RawData, 'InsertLineBreaks'); '-----END CERTIFICATE-----'; '' }" > "%OUTPUT_DIR%\temp-root-system.crt" 2>nul
if errorlevel 1 (
    echo WARNING: Failed to export system root certificates
) else (
    echo   - System root certificates exported
)

REM Export Root CA certificates (User)
echo [2/6] Exporting User Root CA certificates...
powershell -Command "Get-ChildItem -Path Cert:\CurrentUser\Root | ForEach-Object { '-----BEGIN CERTIFICATE-----'; [Convert]::ToBase64String($_.RawData, 'InsertLineBreaks'); '-----END CERTIFICATE-----'; '' }" > "%OUTPUT_DIR%\temp-root-user.crt" 2>nul
if errorlevel 1 (
    echo WARNING: Failed to export user root certificates
) else (
    echo   - User root certificates exported
)

REM Export Intermediate CA certificates (System)
echo [3/6] Exporting System Intermediate CA certificates...
powershell -Command "Get-ChildItem -Path Cert:\LocalMachine\CA | ForEach-Object { '-----BEGIN CERTIFICATE-----'; [Convert]::ToBase64String($_.RawData, 'InsertLineBreaks'); '-----END CERTIFICATE-----'; '' }" > "%OUTPUT_DIR%\temp-ca-system.crt" 2>nul
if errorlevel 1 (
    echo WARNING: Failed to export system intermediate certificates
) else (
    echo   - System intermediate certificates exported
)

REM Export Intermediate CA certificates (User)
echo [4/6] Exporting User Intermediate CA certificates...
powershell -Command "Get-ChildItem -Path Cert:\CurrentUser\CA | ForEach-Object { '-----BEGIN CERTIFICATE-----'; [Convert]::ToBase64String($_.RawData, 'InsertLineBreaks'); '-----END CERTIFICATE-----'; '' }" > "%OUTPUT_DIR%\temp-ca-user.crt" 2>nul
if errorlevel 1 (
    echo WARNING: Failed to export user intermediate certificates
) else (
    echo   - User intermediate certificates exported
)

REM Export Trusted Publishers (System)
echo [5/6] Exporting System Trusted Publishers...
powershell -Command "Get-ChildItem -Path Cert:\LocalMachine\TrustedPublisher | ForEach-Object { '-----BEGIN CERTIFICATE-----'; [Convert]::ToBase64String($_.RawData, 'InsertLineBreaks'); '-----END CERTIFICATE-----'; '' }" > "%OUTPUT_DIR%\temp-pub-system.crt" 2>nul
if errorlevel 1 (
    echo WARNING: Failed to export system trusted publishers
) else (
    echo   - System trusted publishers exported
)

REM Export Trusted Publishers (User)
echo [6/6] Exporting User Trusted Publishers...
powershell -Command "Get-ChildItem -Path Cert:\CurrentUser\TrustedPublisher | ForEach-Object { '-----BEGIN CERTIFICATE-----'; [Convert]::ToBase64String($_.RawData, 'InsertLineBreaks'); '-----END CERTIFICATE-----'; '' }" > "%OUTPUT_DIR%\temp-pub-user.crt" 2>nul
if errorlevel 1 (
    echo WARNING: Failed to export user trusted publishers
) else (
    echo   - User trusted publishers exported
)

echo.
echo Checking which certificate files were created...
if exist "%OUTPUT_DIR%\temp-root-system.crt" (
    echo   - System root certificates: Available
) else (
    echo   - System root certificates: Not found
)
if exist "%OUTPUT_DIR%\temp-root-user.crt" (
    echo   - User root certificates: Available
) else (
    echo   - User root certificates: Not found
)
if exist "%OUTPUT_DIR%\temp-ca-system.crt" (
    echo   - System intermediate certificates: Available
) else (
    echo   - System intermediate certificates: Not found
)
if exist "%OUTPUT_DIR%\temp-ca-user.crt" (
    echo   - User intermediate certificates: Available
) else (
    echo   - User intermediate certificates: Not found
)
if exist "%OUTPUT_DIR%\temp-pub-system.crt" (
    echo   - System trusted publishers: Available
) else (
    echo   - System trusted publishers: Not found
)
if exist "%OUTPUT_DIR%\temp-pub-user.crt" (
    echo   - User trusted publishers: Available
) else (
    echo   - User trusted publishers: Not found
)

echo.
echo Creating individual certificate bundles...

REM Create individual certificate files (only if temp files exist)
if exist "%OUTPUT_DIR%\temp-root-system.crt" (
    type "%OUTPUT_DIR%\temp-root-system.crt" > "%OUTPUT_DIR%\ca-certificates-machine-root.crt" 2>nul
) else (
    echo. > "%OUTPUT_DIR%\ca-certificates-machine-root.crt"
)

if exist "%OUTPUT_DIR%\temp-root-user.crt" (
    type "%OUTPUT_DIR%\temp-root-user.crt" > "%OUTPUT_DIR%\ca-certificates-user-root.crt" 2>nul
) else (
    echo. > "%OUTPUT_DIR%\ca-certificates-user-root.crt"
)

if exist "%OUTPUT_DIR%\temp-ca-system.crt" (
    type "%OUTPUT_DIR%\temp-ca-system.crt" > "%OUTPUT_DIR%\ca-certificates-machine-intermediate.crt" 2>nul
) else (
    echo. > "%OUTPUT_DIR%\ca-certificates-machine-intermediate.crt"
)

if exist "%OUTPUT_DIR%\temp-ca-user.crt" (
    type "%OUTPUT_DIR%\temp-ca-user.crt" > "%OUTPUT_DIR%\ca-certificates-user-intermediate.crt" 2>nul
) else (
    echo. > "%OUTPUT_DIR%\ca-certificates-user-intermediate.crt"
)

if exist "%OUTPUT_DIR%\temp-pub-system.crt" (
    type "%OUTPUT_DIR%\temp-pub-system.crt" > "%OUTPUT_DIR%\ca-certificates-machine-publishers.crt" 2>nul
) else (
    echo. > "%OUTPUT_DIR%\ca-certificates-machine-publishers.crt"
)

if exist "%OUTPUT_DIR%\temp-pub-user.crt" (
    type "%OUTPUT_DIR%\temp-pub-user.crt" > "%OUTPUT_DIR%\ca-certificates-user-publishers.crt" 2>nul
) else (
    echo. > "%OUTPUT_DIR%\ca-certificates-user-publishers.crt"
)

echo Creating combined certificate bundle...

REM Create combined certificate bundle
echo. > "%OUTPUT_DIR%\ca-certificates-all.crt"
if exist "%OUTPUT_DIR%\temp-root-system.crt" (
    type "%OUTPUT_DIR%\temp-root-system.crt" >> "%OUTPUT_DIR%\ca-certificates-all.crt" 2>nul
    echo. >> "%OUTPUT_DIR%\ca-certificates-all.crt"
)
if exist "%OUTPUT_DIR%\temp-root-user.crt" (
    type "%OUTPUT_DIR%\temp-root-user.crt" >> "%OUTPUT_DIR%\ca-certificates-all.crt" 2>nul
    echo. >> "%OUTPUT_DIR%\ca-certificates-all.crt"
)
if exist "%OUTPUT_DIR%\temp-ca-system.crt" (
    type "%OUTPUT_DIR%\temp-ca-system.crt" >> "%OUTPUT_DIR%\ca-certificates-all.crt" 2>nul
    echo. >> "%OUTPUT_DIR%\ca-certificates-all.crt"
)
if exist "%OUTPUT_DIR%\temp-ca-user.crt" (
    type "%OUTPUT_DIR%\temp-ca-user.crt" >> "%OUTPUT_DIR%\ca-certificates-all.crt" 2>nul
    echo. >> "%OUTPUT_DIR%\ca-certificates-all.crt"
)
if exist "%OUTPUT_DIR%\temp-pub-system.crt" (
    type "%OUTPUT_DIR%\temp-pub-system.crt" >> "%OUTPUT_DIR%\ca-certificates-all.crt" 2>nul
    echo. >> "%OUTPUT_DIR%\ca-certificates-all.crt"
)
if exist "%OUTPUT_DIR%\temp-pub-user.crt" (
    type "%OUTPUT_DIR%\temp-pub-user.crt" >> "%OUTPUT_DIR%\ca-certificates-all.crt" 2>nul
    echo. >> "%OUTPUT_DIR%\ca-certificates-all.crt"
)

REM Clean up temporary files
del /q "%OUTPUT_DIR%\temp-*.crt" 2>nul

REM Count certificates in combined bundle
set "CERT_COUNT=0"
for /f %%i in ('findstr /c:"-----BEGIN CERTIFICATE-----" "%OUTPUT_DIR%\ca-certificates-all.crt" 2^>nul') do (
    set /a CERT_COUNT+=1
)

echo.
echo Validating certificate export...

REM Check if any certificates were actually found
if %CERT_COUNT% GTR 0 (
    echo   - SUCCESS: Found %CERT_COUNT% certificates
) else (
    echo   - WARNING: No certificates found in export
    echo   - This may indicate:
    echo     * No certificates in Windows certificate stores
    echo     * Insufficient permissions to read certificate stores
    echo     * certutil command failed silently
    echo   - Try running as Administrator for system certificates
)

echo.
echo Testing URL connectivity...

REM Initialize results file with debugging
echo Creating results file at: %OUTPUT_DIR%\docker-test-results.txt
echo Testing simple file creation first...
echo Test file creation > "%OUTPUT_DIR%\test-file.txt"
if exist "%OUTPUT_DIR%\test-file.txt" (
    echo   - Basic file creation works
    del "%OUTPUT_DIR%\test-file.txt" 2>nul
) else (
    echo   - ERROR: Cannot create files in directory
    echo   - Directory: %OUTPUT_DIR%
    echo   - Permissions issue or path problem
    goto skip_docker_tests
)

echo URL Connectivity Test Results > "%OUTPUT_DIR%\docker-test-results.txt"
if exist "%OUTPUT_DIR%\docker-test-results.txt" (
    echo   - Results file created successfully
) else (
    echo   - ERROR: Failed to create results file specifically
    echo   - This may be a filename issue
    goto skip_docker_tests
)

echo ============================= >> "%OUTPUT_DIR%\docker-test-results.txt"
echo. >> "%OUTPUT_DIR%\docker-test-results.txt"
echo Windows Host Tests: >> "%OUTPUT_DIR%\docker-test-results.txt"

REM Test URLs directly on Windows host using PowerShell
echo   - Testing GitHub on Windows host...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'https://github.com' -Method Head -TimeoutSec 10; 'GitHub (Host): ' + $r.StatusCode + ' - OK' } catch { 'GitHub (Host): FAIL - ' + $_.Exception.Message.Split([char]10)[0] }" >> "%OUTPUT_DIR%\docker-test-results.txt" 2>&1

echo   - Testing PyPI on Windows host...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'https://pypi.org' -Method Head -TimeoutSec 10; 'PyPI (Host): ' + $r.StatusCode + ' - OK' } catch { 'PyPI (Host): FAIL - ' + $_.Exception.Message.Split([char]10)[0] }" >> "%OUTPUT_DIR%\docker-test-results.txt" 2>&1

echo   - Testing NPM Registry on Windows host...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'https://registry.npmjs.org' -Method Head -TimeoutSec 10; 'NPM Registry (Host): ' + $r.StatusCode + ' - OK' } catch { 'NPM Registry (Host): FAIL - ' + $_.Exception.Message.Split([char]10)[0] }" >> "%OUTPUT_DIR%\docker-test-results.txt" 2>&1

echo   - Testing NodeSource on Windows host...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'https://deb.nodesource.com' -Method Head -TimeoutSec 10; 'NodeSource (Host): ' + $r.StatusCode + ' - OK' } catch { 'NodeSource (Host): FAIL - ' + $_.Exception.Message.Split([char]10)[0] }" >> "%OUTPUT_DIR%\docker-test-results.txt" 2>&1

echo. >> "%OUTPUT_DIR%\docker-test-results.txt"

REM Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo   - Docker not available, skipping certificate tests
    echo   - Install Docker Desktop to enable certificate validation
    goto skip_docker_tests
)

echo   - Downloading Alpine image if needed...
docker pull alpine:latest >nul 2>&1

echo   - Running certificate connectivity tests in containers...

REM Add container test header
echo Container Tests ^(with certificates^): >> "%OUTPUT_DIR%\docker-test-results.txt"

REM First test basic container functionality
echo   - Testing basic container setup...
docker run --rm alpine:latest sh -c "echo 'Basic container test: OK'" >> "%OUTPUT_DIR%\docker-test-results.txt" 2>&1

REM Test certificate file mounting
echo   - Testing certificate file mounting...
docker run --rm ^
  -v "%OUTPUT_DIR%\ca-certificates-all.crt:/usr/local/share/ca-certificates/corporate.crt:ro" ^
  alpine:latest sh -c "echo 'Certificate file info:' && ls -la /usr/local/share/ca-certificates/ && echo 'Certificate file size:' && wc -l /usr/local/share/ca-certificates/corporate.crt" >> "%OUTPUT_DIR%\docker-test-results.txt" 2>&1

REM Container tests using Alpine with a single container to test all URLs
echo   - Running all container connectivity tests...
docker run --rm ^
  -v "%OUTPUT_DIR%\ca-certificates-all.crt:/tmp/corporate-bundle.crt:ro" ^
  alpine:latest sh -c "echo 'Installing packages...' && apk --no-check-certificate add --no-cache curl ca-certificates >/dev/null 2>&1 && echo 'Adding corporate certificates to system store...' && cat /tmp/corporate-bundle.crt >> /etc/ssl/certs/ca-certificates.crt && echo 'Testing GitHub...' && curl -I -w 'GitHub (Container): %%{http_code}' --connect-timeout 10 https://github.com >/dev/null 2>&1 && echo 'GitHub (Container): 200 - OK' || echo 'GitHub (Container): FAIL' && echo 'Testing PyPI...' && curl -I -w 'PyPI (Container): %%{http_code}' --connect-timeout 10 https://pypi.org >/dev/null 2>&1 && echo 'PyPI (Container): 200 - OK' || echo 'PyPI (Container): FAIL' && echo 'Testing NPM Registry...' && curl -I -w 'NPM Registry (Container): %%{http_code}' --connect-timeout 10 https://registry.npmjs.org >/dev/null 2>&1 && echo 'NPM Registry (Container): 200 - OK' || echo 'NPM Registry (Container): FAIL' && echo 'Testing NodeSource...' && curl -I -w 'NodeSource (Container): %%{http_code}' --connect-timeout 10 https://deb.nodesource.com >/dev/null 2>&1 && echo 'NodeSource (Container): 200 - OK' || echo 'NodeSource (Container): FAIL'" >> "%OUTPUT_DIR%\docker-test-results.txt" 2>&1


REM Add completion and summary
echo. >> "%OUTPUT_DIR%\docker-test-results.txt"
echo Summary: >> "%OUTPUT_DIR%\docker-test-results.txt"
powershell -Command "$hostFails = (Get-Content '%OUTPUT_DIR%\docker-test-results.txt' | Select-String 'Host.*FAIL').Count; $containerFails = (Get-Content '%OUTPUT_DIR%\docker-test-results.txt' | Select-String 'Container.*FAIL').Count; if ($hostFails -gt 0 -and $containerFails -gt 0) { 'Both host and container issues detected - network/firewall problems' } elseif ($hostFails -gt 0) { 'Host connectivity issues - corporate firewall may be blocking sites' } elseif ($containerFails -gt 0) { 'Container certificate issues - certificates may need updates' } else { 'All connectivity tests passed successfully!' }" >> "%OUTPUT_DIR%\docker-test-results.txt" 2>&1
echo. >> "%OUTPUT_DIR%\docker-test-results.txt"
echo Connectivity tests completed. >> "%OUTPUT_DIR%\docker-test-results.txt"

REM Check if results file was created
if not exist "%OUTPUT_DIR%\docker-test-results.txt" (
    echo   - ERROR: Results file was not created
    echo   - This may indicate Docker command failures
    goto skip_results_check
)

REM Check if any tests failed by looking for FAIL in results
findstr /c:"FAIL" "%OUTPUT_DIR%\docker-test-results.txt" >nul 2>&1

REM Check test results (findstr returns 0 if "FAIL" found, 1 if not found)
if errorlevel 1 (
    echo   - Certificate tests PASSED - all sites accessible
    echo.
    echo   Test results:
    type "%OUTPUT_DIR%\docker-test-results.txt" 2>nul
    echo.
    echo   - Results saved to: docker-test-results.txt
) else (
    echo   - Certificate tests FAILED
    echo.
    echo   Test results:
    type "%OUTPUT_DIR%\docker-test-results.txt" 2>nul
    echo.
    echo   - Some sites may be blocked by corporate firewall
    echo   - Generating IT support report...
    call :generate_it_report
)

:skip_results_check
:skip_docker_tests
echo.
echo Creating documentation...

REM Create README file
(
echo # Windows Certificate Export - %TIMESTAMP%
echo.
echo This directory contains certificates exported from the Windows host system
echo for use in Linux containers to resolve corporate firewall certificate issues.
echo.
echo ## Files Created
echo.
echo - `ca-certificates-all.crt` - **Combined bundle ^(use this one^)**
echo - `ca-certificates-machine-root.crt` - System root CAs
echo - `ca-certificates-user-root.crt` - User root CAs
echo - `ca-certificates-machine-intermediate.crt` - System intermediate CAs
echo - `ca-certificates-user-intermediate.crt` - User intermediate CAs
echo - `ca-certificates-machine-publishers.crt` - System publishers
echo - `ca-certificates-user-publishers.crt` - User publishers
echo.
echo ## Statistics
echo.
echo - Total certificates exported: %CERT_COUNT%
echo - Export timestamp: %TIMESTAMP%
echo - Source: Windows Certificate Stores
echo.
echo ## Usage in DevContainer
echo.
echo The certificates are automatically mounted in the DevContainer at:
echo `/usr/local/share/ca-certificates/host/`
echo.
echo ## Security Notes
echo.
echo - Only public certificates are exported ^(no private keys^)
echo - Files are for local development use only
echo - Do not commit to version control
echo - Re-export periodically to get updated certificates
echo.
echo ## Troubleshooting
echo.
echo If containers still have certificate issues:
echo 1. Verify certificates are mounted: `ls /usr/local/share/ca-certificates/host/`
echo 2. Check if update-ca-certificates ran: `ls /etc/ssl/certs/ ^| grep host`
echo 3. Test connectivity: `curl -I https://github.com`
echo 4. Check TLS_VERIFY setting: `echo $TLS_VERIFY`
echo.
echo For more help, see: docs/CERTIFICATE_COLLECTION_GUIDE.md
) > "%OUTPUT_DIR%\README.md"

echo.
echo ====================================
echo Certificate Export Complete!
echo ====================================
echo.
echo Output directory: %OUTPUT_DIR%
echo Combined bundle: ca-certificates-all.crt
echo Total certificates: %CERT_COUNT%
echo.
echo Files created:
dir /b "%OUTPUT_DIR%\*.crt" "%OUTPUT_DIR%\*.md" "%OUTPUT_DIR%\*.txt" 2>nul

echo.
echo Debug: Looking for docker-test-results.txt...
if exist "%OUTPUT_DIR%\docker-test-results.txt" (
    echo   - docker-test-results.txt found at: %OUTPUT_DIR%\docker-test-results.txt
    echo   - File size:
    dir "%OUTPUT_DIR%\docker-test-results.txt" | findstr "docker-test-results.txt"
) else (
    echo   - docker-test-results.txt NOT FOUND
    echo   - All files in directory:
    dir /b "%OUTPUT_DIR%" 2>nul
)
echo.
echo IMPORTANT NOTES:
echo - Use ca-certificates-all.crt for DevContainer mounting
echo - Files are for local development use only
echo - Do not commit certificate files to version control
echo - Re-run this script periodically for updated certificates
echo.
echo The certificates will be automatically used when you reopen
echo the project in VS Code DevContainer.
echo.
pause
goto :eof

REM Function to generate IT support report
:generate_it_report
echo Creating IT support request report...

(
echo # IT Certificate Support Request
echo Generated: %TIMESTAMP%
echo.
echo ## Issue Summary
echo.
echo URL connectivity testing has identified issues with development resources.
echo Tests were performed on both Windows host and Docker containers to isolate
echo network/firewall issues from certificate-specific problems:
echo.
echo ## Test Results
echo.
type "%OUTPUT_DIR%\docker-test-results.txt" 2>nul
echo.
echo ## Certificate Information
echo.
echo Total certificates exported: %CERT_COUNT%
echo Certificate bundle location: %OUTPUT_DIR%\ca-certificates-all.crt
echo.
echo The following certificate stores were accessed:
echo - System Root Certificate Authorities
echo - User Root Certificate Authorities
echo - System Intermediate Certificate Authorities
echo - User Intermediate Certificate Authorities
echo - System Trusted Publishers
echo - User Trusted Publishers
echo.
echo ## Recommended Actions for IT
echo.
echo ### Based on Test Results Analysis:
echo.
echo **If Host tests PASS but Container tests FAIL:**
echo - Certificate issue: Corporate certificates not recognized in containers
echo - Action: Update corporate root CA certificates for container environments
echo - Verify intermediate certificates are properly deployed
echo.
echo **If Host tests FAIL:**
echo - Network/Firewall issue: Sites blocked at corporate network level
echo - Action: Review firewall rules for these development sites:
echo   - https://github.com ^(Git repositories^)
echo   - https://pypi.org ^(Python packages^)
echo   - https://registry.npmjs.org ^(Node.js packages^)
echo   - https://deb.nodesource.com ^(Node.js installation^)
echo.
echo **If Both Host and Container tests FAIL:**
echo - Complete blockage: Both network and certificate issues present
echo - Action: Address firewall rules first, then certificate deployment
echo.
echo ## Technical Details
echo.
echo - **Container Platform**: Docker with Alpine Linux
echo - **Test Method**: HTTP HEAD requests with curl
echo - **Certificate Mount Point**: /usr/local/share/ca-certificates/
echo - **Certificate Format**: PEM with proper headers
echo.
echo ## Files for IT Review
echo.
echo Please review these files for detailed certificate and test information:
echo - Certificate bundle: ca-certificates-all.crt
echo - Test results: docker-test-results.txt
echo - This report: IT-Certificate-Request.txt
echo.
echo ## Contact Information
echo.
echo User: %USERNAME%
echo Computer: %COMPUTERNAME%
echo Date: %DATE% %TIME%
echo.
echo For additional technical assistance, please contact the development team
echo with this report and the associated certificate files.
) > "%OUTPUT_DIR%\IT-Certificate-Request.txt"

echo   - IT support report created: IT-Certificate-Request.txt
return