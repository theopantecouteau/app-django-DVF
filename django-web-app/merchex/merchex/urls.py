# ~/projects/django-web-app/merchex/merchex/urls.py

from django.contrib import admin
from django.urls import path
from listings import views

urlpatterns = [
path('', views.get_name, name='get_name'),
]