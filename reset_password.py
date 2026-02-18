import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'moneybridge.settings'
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.first()
u.set_password('Test1234!')
u.save()
print('Mot de passe réinitialisé pour:', u.email)