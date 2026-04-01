from django.urls import path
from . import views
from django.urls import include

urlpatterns = [
    path('', views.index, name='index'),
    path('board/', views.task_board, name='task_board'),
    path('update_status/<int:task_id>/<str:new_status>/', views.update_task_status, name='update_status'),
]