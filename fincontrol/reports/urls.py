 
from django.urls import path
from . import views

urlpatterns = [
    path("transactions/<str:fmt>/", views.export_transactions, name="export_transactions"),
]
