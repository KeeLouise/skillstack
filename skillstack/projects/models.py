from django.db import models
from django.contrib.auth.models import User

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

    def __str__(self):
        return self.title