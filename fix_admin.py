from django.apps import apps
import os

app_list = ['accounts', 'banking', 'transactions', 'wallets', 'payments', 'exchange']

for app in app_list:
    path = f'{app}/admin.py'
    with open(path, 'w') as f:
        f.write(f'''from django.contrib import admin
from django.apps import apps

for model in apps.get_app_config("{app}").get_models():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
''')
    print(f'{app} OK')