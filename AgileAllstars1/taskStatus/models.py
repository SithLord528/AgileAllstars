from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    class Status(models.TextChoices):
        TODO = 'TODO', 'To Do'
        IN_PROGRESS = 'IN_PROG', 'In Progress'
        TESTING = 'TEST', 'Testing'
        COMPLETED = 'DONE', 'Completed'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.TODO,
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"