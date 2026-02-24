content = '''from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
]
'''

with open('accounts/urls.py', 'w') as f:
    f.write(content)
print('OK')