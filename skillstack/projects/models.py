from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator 

class Project(models.Model):
    CATEGORY_CHOICES = [
        ('web', 'Web Development'),
        ('mobile', 'Mobile Development'),
        ('backend', 'Backend Development'),
        ('frontend', 'Frontend Development'),
        ('fullstack', 'Full-Stack Development'),
        ('data', 'Data Science / AI'),
        ('devops', 'DevOps / Infrastructure'),
        ('qa', 'QA / Testing'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=50, choices=[
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ])
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')

    collaborators = models.ManyToManyField(User, blank=True, related_name='collaborations')

    def __str__(self):
        return self.title
    
class Invitation(models.Model):
    email = models.EmailField()
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite: {self.email} -> {self.project.title}"
    
def project_attachment_upload_to(instance, filename):
    return f"projects/{instance.project_id}/attachments/{filename}"

class ProjectAttachment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(
        upload_to=project_attachment_upload_to,
        validators=[FileExtensionValidator(allowed_extensions=[
            "pdf", "doc", "docx", "xls", "xlsx", "csv",
            "png", "jpg", "jpeg", "gif", "webp",
            "zip", "txt", "ppt", "pptx"
        ])]
    )
    original_name = models.CharField(max_length=255, blank=True)
    size = models.PositiveBigIntegerField(null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="project_uploads")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_name or (self.file.name if self.file else "Attachment")