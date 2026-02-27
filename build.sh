#!/usr/bin/env bash
set -o errexit

echo "🚀 Build iniciado em $(date)"

# Instalar dependências
pip install -r requirements.txt

# Coletar arquivos estáticos
python manage.py collectstatic --no-input

# 🔴 EXECUTAR MIGRAÇÕES - VERSÃO COMPLETA
echo "🔄 Executando migrações do Django..."

# Primeiro as migrações padrão do Django
python manage.py migrate contenttypes --no-input
python manage.py migrate auth --no-input
python manage.py migrate admin --no-input
python manage.py migrate sessions --no-input
python manage.py migrate messages --no-input
python manage.py migrate staticfiles --no-input

# Depois as migrações dos seus apps
python manage.py migrate accounts --no-input
python manage.py migrate devices --no-input
python manage.py migrate calls --no-input
python manage.py migrate sms_messages --no-input
python manage.py migrate whatsapp --no-input
python manage.py migrate mobile_api --no-input

# Finalmente, garantir que tudo está migrado
python manage.py migrate --no-input

echo "✅ Migrações concluídas!"

# Verificar resultado
python -c "
import django; django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public';\")
    tables = [row[0] for row in cursor.fetchall()]
    print(f'Tabelas criadas: {len(tables)}')
    if 'django_session' in tables:
        print('✅ django_session OK')
    else:
        print('❌ django_session NÃO encontrada!')
"

echo "✅ Build concluído!"