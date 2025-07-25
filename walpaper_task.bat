@echo off
setlocal

REM --- Configurações ---
set "UPDATER_EXE_PATH=C:\wallpaper_updater.exe" REM Substitua pelo caminho real do seu executável

REM Verifica se o arquivo existe antes de adicionar ao registro
if not exist "%UPDATER_EXE_PATH%" (
    echo Erro: O arquivo "%UPDATER_EXE_PATH%" nao foi encontrado.
    echo Certifique-se de que o executavel esta no caminho correto.
    pause
    exit /b 1
)

REM Adiciona o executavel ao registro de inicializacao do usuario atual
REG ADD "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "WallpaperUpdater" /t REG_SZ /d "%UPDATER_EXE_PATH%" /f

if %ERRORLEVEL% equ 0 (
    echo "WallpaperUpdater" adicionado com sucesso a inicializacao.
) else (
    echo Erro ao adicionar "WallpaperUpdater" a inicializacao.
)

pause
endlocal