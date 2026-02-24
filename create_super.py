import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'moneybridge.settings'
os.environ['DATABASE_URL'] = 'postgresql://postgres:CmrLFWsNTHTpIlKKnLbgWIAKoQRaduqF@ballast.proxy.rlwy.net:26868/railway'
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser(
    username='admin',
    email='babacartsn@gmail.com',
    password='Test1234!'
)
print('Superuser créé !')