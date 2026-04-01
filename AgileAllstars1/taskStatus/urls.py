from django.urls import path
from . import views
from django.urls import include

urlpatterns = [
    path("", views.index, name="index"),
    path('backlog/', views.backlog, name='backlog'),
    path('backlog/add-task/', views.add_task, name='add_task'),
    path('backlog/start-sprint/', views.start_sprint, name='start_sprint'),
    path('backlog/task/<int:task_id>/delete/', views.delete_task, name='delete_task'),
]