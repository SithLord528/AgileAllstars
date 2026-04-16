from django import forms

class InviteCollaboratorForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'colleague@example.com',
            'style': 'width: 100%; padding: 8px; margin-bottom: 10px;',
            'required': 'True'
        })
    )