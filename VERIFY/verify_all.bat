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
call :check_hash_from_freeze "demo\stocrs_poc_demo.py" "VERIFY\FREEZE_DEMO_SHA256.txt"
call :check_hash_from_freeze "demo\stocrs_canonical_demo_v1_2.py" "VERIFY\FREEZE_DEMO_SHA256.txt"
call :check_hash_from_freeze "demo\stocrs_reconciliation_demo_v1_1.py" "VERIFY\FREEZE_DEMO_SHA256.txt"
echo.

echo [2/4] Verifying runtime hash...
call :check_hash_from_freeze "runtime\stocrs_engine_v1_1.py" "VERIFY\FREEZE_RUNTIME_SHA256.txt"
echo.

echo [3/4] Verifying frozen reference artifact hashes...
call :check_hash_from_freeze "reference_outputs\reference_output.json" "VERIFY\FREEZE_REFERENCE_OUTPUTS_SHA256.txt"
call :check_hash_from_freeze "reference_outputs\reference_run.txt" "VERIFY\FREEZE_REFERENCE_OUTPUTS_SHA256.txt"
call :check_hash_from_freeze "reference_outputs\reconciliation_demo_v1_1.json" "VERIFY\FREEZE_REFERENCE_OUTPUTS_SHA256.txt"
call :check_hash_from_freeze "reference_outputs\stocrs_canonical_demo_v1.json" "VERIFY\FREEZE_REFERENCE_OUTPUTS_SHA256.txt"
call :check_hash_from_freeze "reference_outputs\stocrs_conflict_demo_v1.json" "VERIFY\FREEZE_REFERENCE_OUTPUTS_SHA256.txt"
echo.

echo [4/4] Reproducing outputs and checking conflict semantics...
python demo\stocrs_canonical_demo_v1_2.py --seed 101 --systems 5 --json > VERIFY\_tmp_canonical.json
if errorlevel 1 (
    echo FAIL: canonical demo execution failed
    set "FAIL=1"
) else (
    python -c "import json,sys; ref=json.load(open(r'reference_outputs\reference_output.json','r',encoding='utf-8')); cur=json.load(open(r'VERIFY\_tmp_canonical.json','r',encoding='utf-8')); sys.exit(0 if cur==ref else 1)"
    if errorlevel 1 (
        echo FAIL: canonical JSON reproduction did not match the frozen reference
        set "FAIL=1"
    ) else (
        echo PASS: canonical JSON reproduction matched the frozen reference
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

python -c "import sys; from runtime.stocrs_engine_v1_1 import build_program,run_system; r=run_system('S1',build_program(),['X1','X2','A1'],1000.0,60.0,0.0,claims={'X1':[9,9,2],'X2':[3,3]}); ok=('X1' in r.get('conflicts',{}) and 'X1' not in r.get('values',{}) and 'A1' in r.get('unresolved',[])); sys.exit(0 if ok else 1)"
if errorlevel 1 (
    echo FAIL: conflicting claim multiplicity overrode declared structure
    set "FAIL=1"
) else (
    echo PASS: conflicting claim multiplicity cannot override declared structure
)

if exist VERIFY\_tmp_canonical.json del /q VERIFY\_tmp_canonical.json >nul 2>&1
if exist VERIFY\_tmp_reconciliation.json del /q VERIFY\_tmp_reconciliation.json >nul 2>&1

echo.
if "%FAIL%"=="0" (
    echo ==========================================
    echo VERIFY RESULT: PASS
    echo Deterministic reproduction confirmed within the declared reference cases.
    echo ==========================================
) else (
    echo ==========================================
    echo VERIFY RESULT: FAIL
    echo One or more hashes, outputs, or semantic checks did not match.
    echo ==========================================
)

popd >nul
exit /b %FAIL%

:check_hash_from_freeze
set "FILE=%~1"
set "FREEZE=%~2"

if not exist "%FILE%" (
    echo FAIL: missing file "%FILE%"
    set "FAIL=1"
    exit /b 0
)

if not exist "%FREEZE%" (
    echo FAIL: missing freeze file "%FREEZE%"
    set "FAIL=1"
    exit /b 0
)

python -c "import hashlib,pathlib,sys; f=pathlib.Path(sys.argv[1]); z=pathlib.Path(sys.argv[2]); header='SHA256 hash of '+sys.argv[1]+':'; lines=z.read_text(encoding='utf-8',errors='replace').splitlines(); idx=next((i for i,x in enumerate(lines) if x.strip()==header),None); expected=(lines[idx+1].strip().lower() if idx is not None and idx+1<len(lines) else ''); actual=hashlib.sha256(f.read_bytes()).hexdigest(); ok=(len(expected)==64 and actual==expected); print(('PASS: ' if ok else 'FAIL: ')+sys.argv[1]); print(('      expected: '+expected+'\n      actual:   '+actual) if not ok else '',end=''); sys.exit(0 if ok else 1)" "%FILE%" "%FREEZE%"
if errorlevel 1 set "FAIL=1"
exit /b 0
