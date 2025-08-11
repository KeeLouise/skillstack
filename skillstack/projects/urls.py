from django.urls import path
from .views import create_project, project_detail, delete_project, edit_project

urlpatterns = [
    path('create/', create_project, name='create_project'),
    path('<int:pk>/edit/', edit_project, name='edit_project'),
    path('<int:pk>/', project_detail, name='project_detail'),
    path('<int:pk>/delete/', delete_project, name='delete_project'),
]