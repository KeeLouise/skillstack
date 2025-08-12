from django.urls import path
from .views import (
    create_project, project_detail, edit_project, delete_project,
    upload_project_attachments, download_project_attachment, delete_project_attachment
)

urlpatterns = [
    path('create/', create_project, name='create_project'),
    path('<int:pk>/', project_detail, name='project_detail'),
    path('<int:pk>/edit/', edit_project, name='edit_project'),
    path('<int:pk>/delete/', delete_project, name='delete_project'),

    path('<int:pk>/attachments/upload/', upload_project_attachments, name='project_attachments_upload'),
    path('attachments/<int:att_pk>/download/', download_project_attachment, name='project_attachment_download'),
    path('attachments/<int:att_pk>/delete/', delete_project_attachment, name='project_attachment_delete'),
]