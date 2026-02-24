content = open('moneybridge/settings.py').read()

if 'CSRF_TRUSTED_ORIGINS' not in content:
    with open('moneybridge/settings.py', 'a') as f:
        f.write("""
CSRF_TRUSTED_ORIGINS = ['https://moneybridge-backend-production.up.railway.app']
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
""")
    print('CSRF OK')
else:
    print('CSRF déjà présent')