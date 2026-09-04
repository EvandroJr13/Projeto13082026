@echo off
REM Build onefile exe for Windows using PyInstaller and place on Desktop
REM Execute este script no Windows (duplo clique ou via terminal)

:: Atualiza pip e instala PyInstaller localmente (user)
python -m pip install --upgrade pip
python -m pip install pyinstaller --user

:: Garante dependências do projeto (opcional)
python -m pip install -r requirements.txt --user 2>nul || (
	python -m pip install customtkinter --user
)

:: Executa PyInstaller em modo onefile usando o módulo Python e salva o .exe na Área de Trabalho do usuário
python -m PyInstaller --noconfirm --onefile --windowed --name Projeto13082026 "%~dp0\Projeto13082026.py" --distpath "%USERPROFILE%\Desktop" --log-level=DEBUG

if %ERRORLEVEL% equ 0 (
	echo Build concluido. Executavel salvo em %USERPROFILE%\Desktop\Projeto13082026.exe
) else (
	echo Erro no build. Verifique as mensagens acima.
)
pause
