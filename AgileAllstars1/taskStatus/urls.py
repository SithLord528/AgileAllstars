from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('project/<int:project_id>/', views.project_board, name='project_board'),
    path('project/<int:project_id>/add-item/', views.create_item, name='create_item'),
    path('project/<int:project_id>/add-sprint/', views.create_sprint, name='create_sprint'),
    path('sprint/<int:sprint_id>/activate/', views.activate_sprint, name='activate_sprint'),
    path('sprint/<int:sprint_id>/close/', views.close_sprint, name='close_sprint'),
    path('item/<int:item_id>/move/<str:new_status>/', views.update_item_status, name='update_item_status'),
    path('item/<int:item_id>/priority/<str:new_priority>/', views.update_item_priority, name='update_item_priority'),
    path('project/<int:project_id>/invite/', views.invite_collaborator, name='invite_collaborator'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('item/<int:item_id>/delete/', views.delete_item, name='delete_item'),
]
