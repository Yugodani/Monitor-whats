#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando build em $(date)"

echo "📦 Versão do Python: $(python --version)"

echo "📦 Instalando dependências..."
pip install -r requirements.txt

echo "📊 Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

echo "🔄 Verificando configuração do banco de dados..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'empresa_monitor.settings')
django.setup()
from django.conf import settings
print(f'DEBUG: {settings.DEBUG}')
print(f'DATABASE ENGINE: {settings.DATABASES[\"default\"][\"ENGINE\"]}')
print(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
"

echo "🔄 Aplicando migrações..."
python manage.py migrate --no-input

echo "🔍 Verificando sistema..."
python manage.py check --deploy

echo "✅ Build concluído com sucesso em $(date)"