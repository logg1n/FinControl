# dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("analytics-block/", views.analytics_block, name="analytics_block"),
]
