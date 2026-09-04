#!/usr/bin/env bash
set -euo pipefail

# Script para rodar dentro do WSL (Ubuntu) e gerar um executável Linux "onefile"
# Uso: wsl bash -c "./build_linux.sh"

echo "Verificando ambiente..."
if ! grep -qi microsoft /proc/version 2>/dev/null; then
  echo "Aviso: este script parece não estar rodando dentro do WSL. Execute via 'wsl bash -c \"./build_linux.sh\"' a partir do Windows." >&2
fi

echo "Atualizando repositórios e instalando dependências do sistema (sudo poderá pedir senha)..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv python3-tk build-essential

echo "Criando e ativando ambiente virtual em .venv-linux..."
python3 -m venv .venv-linux
source .venv-linux/bin/activate

echo "Atualizando pip e instalando dependências Python..."
python -m pip install --upgrade pip
python -m pip install customtkinter pillow requests pyinstaller

echo "Executando PyInstaller (onefile, windowed) para main.py..."
python -m PyInstaller --noconfirm --onefile --windowed main.py

echo "Ajustando permissões do binário gerado (se existir)..."
if [ -f dist/main ]; then
  chmod +x dist/main
  echo "Build concluído: dist/main"
  ls -l dist/main
else
  echo "Erro: binário dist/main não encontrado. Verifique a saída do PyInstaller acima." >&2
  exit 1
fi

# desative o venv opcionalmente
# deactivate

echo "Fim do script."