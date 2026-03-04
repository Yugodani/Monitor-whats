# build.sh
#!/usr/bin/env bash
set -o errexit

echo "🚀 Build iniciado"

# Instalar dependências
pip install -r requirements.txt

# Coletar estáticos
python manage.py collectstatic --no-input

# Aplicar migrações
python manage.py migrate

# 🔴 CRIAR SUPERUSUÁRIO (REMOVA DEPOIS!)
echo "🔄 Criando superusuário..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username='admin',
        email='thiago.olimpio.oliveira@gmail.com',
        password='Nota102030@',
        company='THO Company'
    )
    print('✅ Superusuário criado!')
else:
    print('⚠️ Superusuário já existe')
END

echo "✅ Build concluído"