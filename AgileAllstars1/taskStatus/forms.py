from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status']
        
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g., Finalize 3D print file for the leaf cuvette',
                'style': 'width: 100%; padding: 8px; margin-bottom: 10px;'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3, 
                'style': 'width: 100%; padding: 8px; margin-bottom: 10px;'
            }),
            'status': forms.Select(attrs={
                'style': 'width: 100%; padding: 8px; margin-bottom: 15px;'
            }),
        }