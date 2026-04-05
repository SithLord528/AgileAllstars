from django.contrib import admin
from .models import Project, Sprint, BacklogItem


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner_id', 'created_at')
    search_fields = ('name',)


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'project')


@admin.register(BacklogItem)
class BacklogItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'priority', 'sprint', 'updated_at')
    list_filter = ('status', 'priority', 'project')
    search_fields = ('title', 'description')
