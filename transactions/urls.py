from django.urls import path
from . import views

urlpatterns = [
    path("", views.my_transactions, name="my-transactions"),
    path("create/", views.create_transaction, name="create-transaction"),
]
