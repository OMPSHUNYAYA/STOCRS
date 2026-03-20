@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ==========================================
echo STOCRS VERIFY - Deterministic Verification
echo ==========================================
echo.

set "ROOT=%~dp0.."
pushd "%ROOT%" >nul

set "FAIL=0"

echo [1/4] Verifying demo script hashes...
call :check_hash "demo\stocrs_poc_demo.py" "5b898feac61cf858e4972991b697059495852fbaae4708c432ec624bdc85f4a6"
call :check_hash "demo\stocrs_canonical_demo.py" "f9d70522bfdacaa6059a75d52fbb1fc906c4c3772a3cbb96a44dfb30837de1a0"
call :check_hash "demo\stocrs_reconciliation_demo_v1_1.py" "88515a663a0ebf6eebadb1cde6e3cce0c0f0464e1a1839aae793563e565ffbf3"
echo.

echo [2/4] Verifying runtime hash...
call :check_hash "runtime\stocrs_engine_v1.py" "f39d8faeae8261452fc94d1b4cd06a960f5e78f0df4b565e69dc85a6ee4fe6fe"
echo.

echo [3/4] Verifying frozen reference artifact hashes...
call :check_hash "reference_outputs\reference_output.json" "790f43950beed800fda65ab580c42db13ed542c0c045063c2c7dd883f23f0486"
call :check_hash "reference_outputs\reference_run.txt" "bcfcfc137c75f8851c841073bb93b5e9a4377fb4d8b0779bf40003136e4390c7"
call :check_hash "reference_outputs\reconciliation_demo_v1_1.json" "b0b00c1df61076085422c114eb6b3d78278d449e485b9b34aae35017afd240fe"
call :check_hash "reference_outputs\stocrs_canonical_demo_v1.json" "cd13105934f203e5ac35cfb5578407ca0acb1b17d072f874aab96e0752dff5d1"
call :check_hash "reference_outputs\stocrs_conflict_demo_v1.json" "3d67dae5e6517a4e8973a26a07348e92f101ed89caf536bbac4d131a7c7d2dd6"
echo.

echo [4/4] Reproducing canonical and reconciliation outputs...
python demo\stocrs_canonical_demo.py --seed 101 --systems 5 --json > VERIFY\_tmp_canonical.json
if errorlevel 1 (
    echo FAIL: canonical demo execution failed
    set "FAIL=1"
) else (
    python -c "import json,sys; ref=json.load(open(r'reference_outputs\reference_output.json','r',encoding='utf-8')); cur=json.load(open(r'VERIFY\_tmp_canonical.json','r',encoding='utf-8')); ok=(cur.get('certificate')==ref.get('certificate') and cur.get('final_complete_ok')==ref.get('final_complete_ok') and cur.get('final_match_ok')==ref.get('final_match_ok') and cur.get('final_node_count')==ref.get('final_node_count') and cur.get('final_e1')==ref.get('final_e1') and cur.get('conflict_story',{}).get('certificate')==ref.get('conflict_story',{}).get('certificate') and cur.get('conflict_story',{}).get('stable_ok')==ref.get('conflict_story',{}).get('stable_ok') and cur.get('conflict_story',{}).get('conflict_ok')==ref.get('conflict_story',{}).get('conflict_ok') and cur.get('conflict_story',{}).get('recovery_ok')==ref.get('conflict_story',{}).get('recovery_ok')); sys.exit(0 if ok else 1)"
    if errorlevel 1 (
        echo FAIL: canonical JSON semantic verification failed
        set "FAIL=1"
    ) else (
        echo PASS: canonical JSON semantic verification passed
    )
)

python demo\stocrs_reconciliation_demo_v1_1.py --seed 101 --json > VERIFY\_tmp_reconciliation.json
if errorlevel 1 (
    echo FAIL: reconciliation demo execution failed
    set "FAIL=1"
) else (
    python -c "import json,sys; ref=json.load(open(r'reference_outputs\reconciliation_demo_v1_1.json','r',encoding='utf-8')); cur=json.load(open(r'VERIFY\_tmp_reconciliation.json','r',encoding='utf-8')); ok=(cur.get('certificate')==ref.get('certificate') and cur.get('all_match')==ref.get('all_match') and cur.get('final_complete')==ref.get('final_complete') and cur.get('no_logs')==ref.get('no_logs') and cur.get('no_timestamps')==ref.get('no_timestamps') and cur.get('no_order_required')==ref.get('no_order_required') and cur.get('final_values')==ref.get('final_values')); sys.exit(0 if ok else 1)"
    if errorlevel 1 (
        echo FAIL: reconciliation JSON semantic verification failed
        set "FAIL=1"
    ) else (
        echo PASS: reconciliation JSON semantic verification passed
    )
)

if exist VERIFY\_tmp_canonical.json del /q VERIFY\_tmp_canonical.json >nul 2>&1
if exist VERIFY\_tmp_reconciliation.json del /q VERIFY\_tmp_reconciliation.json >nul 2>&1

echo.
if "%FAIL%"=="0" (
    echo ==========================================
    echo VERIFY RESULT: PASS
    echo Deterministic reproduction confirmed.
    echo ==========================================
) else (
    echo ==========================================
    echo VERIFY RESULT: FAIL
    echo One or more hashes or outputs did not match.
    echo ==========================================
)

popd >nul
exit /b %FAIL%

:check_hash
set "FILE=%~1"
set "EXPECTED=%~2"

if not exist "%FILE%" (
    echo FAIL: missing file "%FILE%"
    set "FAIL=1"
    exit /b 0
)

set "ACTUAL="
for /f "skip=1 delims=" %%L in ('certutil -hashfile "%FILE%" SHA256') do (
    set "LINE=%%L"
    set "LINE=!LINE: =!"
    if not "!LINE!"=="" (
        if /I not "!LINE:~0,8!"=="CertUtil" (
            if /I not "!LINE:~0,7!"=="SHA256h" (
                set "ACTUAL=!LINE!"
                goto :compare_hash
            )
        )
    )
)

echo FAIL: could not compute hash for "%FILE%"
set "FAIL=1"
exit /b 0

:compare_hash
if /I "!ACTUAL!"=="%EXPECTED%" (
    echo PASS: %FILE%
) else (
    echo FAIL: %FILE%
    echo       expected: %EXPECTED%
    echo       actual:   !ACTUAL!
    set "FAIL=1"
)
exit /b 0