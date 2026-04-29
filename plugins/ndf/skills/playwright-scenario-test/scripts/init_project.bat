@echo off
rem scenario-test ランタイムを利用者プロジェクトに埋め込む初期化スクリプト (Windows 版)。
rem
rem 使い方:
rem   scripts\init_project.bat <PROJECT_ROOT> [--runtime-dir <name>] [--dry-run]
rem
rem 例:
rem   scripts\init_project.bat C:\path\to\your-app
rem   scripts\init_project.bat C:\path\to\your-app --runtime-dir e2e
rem
rem 動作: scripts/init_project.sh と同じ内容を xcopy ベースで Windows 上にて実施。

setlocal EnableExtensions EnableDelayedExpansion

set "PROJECT_ROOT="
set "RUNTIME_DIR_NAME=scenario-test"
set "DRY_RUN=0"

:parse_args
if "%~1"=="" goto :validate_args
if "%~1"=="--runtime-dir" (
  if "%~2"=="" (
    echo [init] --runtime-dir に値が必要です
    exit /b 1
  )
  set "RUNTIME_DIR_NAME=%~2"
  shift
  shift
  goto :parse_args
)
if "%~1"=="--dry-run" (
  set "DRY_RUN=1"
  shift
  goto :parse_args
)
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help
if "%~1:~0,1%"=="-" (
  echo [init] unknown option: %~1
  exit /b 1
)
if not "%PROJECT_ROOT%"=="" (
  echo [init] PROJECT_ROOT は 1 つだけ指定してください ^(既: %PROJECT_ROOT%, 追加: %~1^)
  exit /b 1
)
set "PROJECT_ROOT=%~1"
shift
goto :parse_args

:show_help
echo 使い方: scripts\init_project.bat ^<PROJECT_ROOT^> [--runtime-dir ^<name^>] [--dry-run]
exit /b 0

:validate_args
if "%PROJECT_ROOT%"=="" (
  echo [init] PROJECT_ROOT は必須です
  exit /b 1
)

rem Skill ディレクトリ (このスクリプトの 1 つ上)
for %%i in ("%~dp0..") do set "SKILL_DIR=%%~fi"

rem ランタイム配置先
set "RUNTIME_DIR=%PROJECT_ROOT%\%RUNTIME_DIR_NAME%"

echo [init] Skill ディレクトリ : %SKILL_DIR%
echo [init] プロジェクトルート : %PROJECT_ROOT%
echo [init] ランタイム配置先   : %RUNTIME_DIR%
if "%DRY_RUN%"=="1" echo [init] (dry-run モード)

if not exist "%PROJECT_ROOT%" (
  echo [init] PROJECT_ROOT が存在しません: %PROJECT_ROOT%
  exit /b 1
)

if "%DRY_RUN%"=="0" (
  if not exist "%RUNTIME_DIR%\tests" mkdir "%RUNTIME_DIR%\tests"
)

rem ---------- 1) playwright_kit / scripts / uv.lock を xcopy ----------
echo [init] [1/4] playwright_kit / scripts / uv.lock をコピー
if "%DRY_RUN%"=="0" (
  xcopy /E /I /Y /Q "%SKILL_DIR%\playwright_kit" "%RUNTIME_DIR%\playwright_kit" >nul
  xcopy /E /I /Y /Q "%SKILL_DIR%\scripts"        "%RUNTIME_DIR%\scripts" >nul
  copy /Y "%SKILL_DIR%\uv.lock" "%RUNTIME_DIR%\uv.lock" >nul
) else (
  echo     xcopy %SKILL_DIR%\playwright_kit -^> %RUNTIME_DIR%\playwright_kit
  echo     xcopy %SKILL_DIR%\scripts        -^> %RUNTIME_DIR%\scripts
  echo     copy  %SKILL_DIR%\uv.lock        -^> %RUNTIME_DIR%\uv.lock
)

rem ---------- 2) runtime テンプレート (上書き) ----------
echo [init] [2/4] runtime テンプレート
call :copy_overwrite "%SKILL_DIR%\templates\pyproject.toml.runtime" "%RUNTIME_DIR%\pyproject.toml"
call :copy_overwrite "%SKILL_DIR%\templates\run.sh"                  "%RUNTIME_DIR%\run.sh"
call :copy_overwrite "%SKILL_DIR%\templates\run.bat"                 "%RUNTIME_DIR%\run.bat"
call :copy_overwrite "%SKILL_DIR%\templates\runtime-gitignore"       "%RUNTIME_DIR%\.gitignore"
call :copy_overwrite "%SKILL_DIR%\templates\runtime-README.md"       "%RUNTIME_DIR%\README.md"

rem ---------- 3) 利用者編集物 (上書きしない) ----------
echo [init] [3/4] 利用者編集物 (scenario.config.yaml / tests/) — 既存があれば skip
call :copy_if_absent "%SKILL_DIR%\templates\scenario.config.yaml" "%RUNTIME_DIR%\scenario.config.yaml"
call :copy_if_absent "%SKILL_DIR%\templates\conftest.py.template" "%RUNTIME_DIR%\tests\conftest.py"
for %%t in (test_auth test_list test_form test_dashboard) do (
  call :copy_if_absent "%SKILL_DIR%\templates\%%t.py.template" "%RUNTIME_DIR%\tests\%%t.py"
)

rem ---------- 4) 初回 uv sync + playwright install ----------
if "%DRY_RUN%"=="1" (
  echo [init] [4/4] dry-run のためスキップ
  echo [init] dry-run 完了
  exit /b 0
)

echo [init] [4/4] uv sync + playwright install chromium
where uv >nul 2>&1
if errorlevel 1 (
  echo [init] WARN: uv が見つかりません。https://docs.astral.sh/uv/ からインストールしてください。
  echo [init]       run.bat 起動時に初回 uv sync が走ります。
) else (
  pushd "%RUNTIME_DIR%"
  uv sync
  uv run playwright install chromium
  popd
)

echo.
echo [done] 初期化完了。次回以降は以下のコマンドで実行できます:
echo        cd %RUNTIME_DIR% ^&^& run.bat
exit /b 0

:copy_overwrite
if "%DRY_RUN%"=="1" (
  echo     cp ^(overwrite^): %~1 -^> %~2
  exit /b 0
)
copy /Y "%~1" "%~2" >nul
exit /b 0

:copy_if_absent
if exist "%~2" (
  echo     skip ^(exists^): %~2
  exit /b 0
)
if "%DRY_RUN%"=="1" (
  echo     cp ^(new^): %~1 -^> %~2
  exit /b 0
)
copy /Y "%~1" "%~2" >nul
exit /b 0
