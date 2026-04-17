from django import forms
from sprints.models import Project, Sprint, BacklogItem


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Project name',
                'style': 'width: 100%; padding: 8px; margin-bottom: 10px;',
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Brief description (optional)',
                'style': 'width: 100%; padding: 8px; margin-bottom: 10px;',
            }),
        }


class SprintForm(forms.ModelForm):
    class Meta:
        model = Sprint
        fields = ['name', 'goal', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Sprint 1',
                'style': 'width: 100%; padding: 8px; margin-bottom: 10px;',
            }),
            'goal': forms.TextInput(attrs={
                'placeholder': 'Sprint goal (optional)',
                'style': 'width: 100%; padding: 8px; margin-bottom: 10px;',
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'style': 'padding: 8px; margin-bottom: 10px; margin-right: 10px;',
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'style': 'padding: 8px; margin-bottom: 10px;',
            }),
        }


class BacklogItemForm(forms.ModelForm):
    class Meta:
        model = BacklogItem
        fields = ['title', 'description', 'priority', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g., Implement user login flow',
                'style': 'width: 100%; padding: 8px; margin-bottom: 10px;',
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Details (optional)',
                'style': 'width: 100%; padding: 8px; margin-bottom: 10px;',
            }),
            'priority': forms.Select(attrs={
                'style': 'width: 100%; padding: 8px; margin-bottom: 15px;',
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'style': 'width: 48%; padding: 8px; margin-bottom: 10px; margin-right: 4%;',
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'style': 'width: 48%; padding: 8px; margin-bottom: 10px;',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError('End date cannot be before start date.')
        return cleaned_data
