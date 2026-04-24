from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Add this import

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(success_url='/login/'), name='password_change'),
    path('accounts/', include('django.contrib.auth.urls')), 
    path('', include('taskStatus.urls')),
    path('', include('users.urls')),
]