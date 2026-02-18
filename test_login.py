import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'moneybridge.settings'
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.first()
print('Email:', u.email)
print('Username:', u.username)
print('Password OK:', u.check_password('Oscardonit11'))