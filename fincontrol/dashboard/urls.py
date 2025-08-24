# dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("dashboard-block/", views.dashboard_block, name="dashboard_block"),
]