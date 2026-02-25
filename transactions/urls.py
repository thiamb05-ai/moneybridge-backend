from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_transactions, name='list_transactions'),
    path('create/', views.send_money, name='send_money'),
    path('receive/', views.receive_money, name='receive_money'),
    path('withdraw/', views.withdraw_to_bank, name='withdraw'),
    path('fee/', views.calculate_fee, name='calculate_fee'),
]
