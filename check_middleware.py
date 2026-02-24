f = open('moneybridge/settings.py').read()
idx = f.find('MIDDLEWARE')
print(f[idx:idx+300])