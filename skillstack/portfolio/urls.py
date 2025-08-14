from django.urls import path
from . import views

urlpatterns = [
    path('', views.portfolio_gallery, name='portfolio_gallery'),
    path('new/', views.portfolio_create, name='portfolio_create'),
    path('p/<str:username>/', views.portfolio_public, name='portfolio_public'),
]