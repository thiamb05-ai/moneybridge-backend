import os

content = open('moneybridge/settings.py').read()

if 'CORS_ALLOW_ALL_ORIGINS' not in content:
    with open('moneybridge/settings.py', 'a') as f:
        f.write('''
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
''')
    print('CORS ajouté OK')
else:
    print('CORS déjà présent')