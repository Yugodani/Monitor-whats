#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "📦 Instalando dependências..."
pip install -r requirements.txt

echo "📊 Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

echo "🔄 Aplicando migrações..."
python manage.py migrate

echo "✅ Build concluído com sucesso!"