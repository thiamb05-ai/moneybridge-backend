content = open('moneybridge/settings.py').read()
print('CSRF présent:', 'CSRF_TRUSTED_ORIGINS' in content)
print('SESSION_COOKIE_SECURE présent:', 'SESSION_COOKIE_SECURE' in content)