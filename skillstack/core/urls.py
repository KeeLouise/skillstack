from django.urls import path
from .views import home, dashboard, create_project, project_detail

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('create/', create_project, name='create_project'),
    path('<int:project_id>/', project_detail, name='project_detail'),
]