#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "🚀 Iniciando build..."

echo "📦 Instalando dependências..."
pip install -r requirements.txt

echo "📊 Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

echo "🔄 Verificando banco de dados..."

# Verificar se DATABASE_URL está configurada
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  WARNING: DATABASE_URL não configurada. Usando SQLite."
else
    echo "✅ DATABASE_URL encontrada. Usando PostgreSQL."
fi

echo "🔄 Aplicando migrações..."
python manage.py migrate --no-input

echo "✅ Build concluído com sucesso!"