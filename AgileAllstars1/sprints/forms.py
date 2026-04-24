from django import forms
from .models import Project, Sprint, BacklogItem

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description...'}),
        }

class SprintForm(forms.ModelForm): # FIXED: Changed models.ModelForm to forms.ModelForm
    class Meta:
        model = Sprint
        fields = ['name', 'goal', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sprint Name'}),
            'goal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sprint Goal'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class BacklogItemForm(forms.ModelForm):
    class Meta:
        model = BacklogItem
        fields = ['title', 'description', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Task description...'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }