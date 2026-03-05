# build.sh (adicione antes do final)
echo "🔄 Criando superusuário automaticamente..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@admin.com',
        password='admin123',
        company='Admin Company'
    )
    print('✅ Superusuário criado!')
else:
    print('⚠️ Superusuário já existe')
END