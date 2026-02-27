#!/usr/bin/env bash
set -o errexit

echo "🚀 Build iniciado em $(date)"

# Instalar dependências
pip install -r requirements.txt

# Coletar arquivos estáticos
python manage.py collectstatic --no-input

# 🔴 FORÇAR MIGRAÇÕES EM ORDEM
echo "🔄 Aplicando migrações em ordem..."

# Lista de apps na ordem correta de dependência
APPS=("accounts" "devices" "calls" "sms_messages" "whatsapp" "mobile_api")

for app in "${APPS[@]}"; do
    echo "   Migrando $app..."
    python manage.py migrate $app --no-input || true
done

# Migração geral
echo "   Migrando todo o projeto..."
python manage.py migrate --no-input

# Verificar resultado
echo "🔍 Verificando tabelas..."
python -c "
import django; django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public';\")
    tables = cursor.fetchall()
    print(f'Tabelas criadas: {len(tables)}')
"

echo "✅ Build concluído!"