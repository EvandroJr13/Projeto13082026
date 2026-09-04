#!/usr/bin/env bash
set -euo pipefail

# Script para automatizar git add/commit/push
# Uso: ./push.sh

if ! command -v git >/dev/null 2>&1; then
  echo "git não encontrado. Instale git e execute novamente." >&2
  exit 1
fi

# Verifica se estamos em um repositório git
if [ ! -d .git ]; then
  echo "Repositório git não inicializado. Inicializando..."
  git init
fi

# Mostra status e pede mensagem de commit
git status --porcelain
read -r -p "Mensagem do commit: " COMMIT_MSG
if [ -z "$COMMIT_MSG" ]; then
  COMMIT_MSG="Atualização automática"
fi

# Adiciona e comita
git add .
git commit -m "$COMMIT_MSG" || echo "Nada para commitar ou commit falhou." 

# Verifica se existe remote origin
if git remote get-url origin >/dev/null 2>&1; then
  REMOTE_URL=$(git remote get-url origin)
  echo "Remote origin configurado: $REMOTE_URL"
else
  read -r -p "URL do remote (ou Enter para pular): " REMOTE_URL
  if [ -n "$REMOTE_URL" ]; then
	git remote add origin "$REMOTE_URL"
	echo "Remote origin adicionado."
  fi
fi

# Define branch padrão
read -r -p "Nome do branch para push (default: main): " BRANCH
BRANCH=${BRANCH:-main}

# Cria branch local se não existir
if ! git rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
  git branch -M "$BRANCH"
fi

# Realiza push
if [ -n "${REMOTE_URL:-}" ]; then
  echo "Executando git push -u origin $BRANCH"
  git push -u origin "$BRANCH"
else
  echo "Nenhum remote configurado. Push ignorado." >&2
fi

echo "Operação concluída."