with open('moneybridge/settings.py', 'r') as f:
    content = f.read()

old = "'django.middleware.security.SecurityMiddleware',"
new = "'django.middleware.security.SecurityMiddleware',\n    'whitenoise.middleware.WhiteNoiseMiddleware',"

if 'WhiteNoiseMiddleware' not in content:
    content = content.replace(old, new)
    with open('moneybridge/settings.py', 'w') as f:
        f.write(content)
    print('WhiteNoise ajouté OK')
else:
    print('WhiteNoise déjà présent')