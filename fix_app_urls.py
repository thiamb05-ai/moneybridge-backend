apps = ['accounts', 'banking', 'transactions', 'wallets', 'payments', 'exchange']

content = '''from django.urls import path

urlpatterns = []
'''

for app in apps:
    with open(f'{app}/urls.py', 'w') as f:
        f.write(content)
    print(f'{app}/urls.py OK')