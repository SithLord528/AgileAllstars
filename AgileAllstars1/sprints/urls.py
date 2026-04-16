from django.urls import path
from . import views

urlpatterns = [
    path('project/<int:project_id>/invite/', views.invite_collaborator, name='invite_collaborator'),
]
