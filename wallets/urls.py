from django.urls import path
from . import views

urlpatterns = [
    path("my-wallet/", views.my_wallet, name="my-wallet"),
]
