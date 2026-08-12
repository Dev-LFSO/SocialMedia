from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'username']
        labels = {
            'email': 'E-mail',
            'username': 'Nome de usuário',
            'name': 'Nome completo',
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'name', 'username', 'email', 'cpf', 
            'bio', 'city', 'state', 'country', 'profile_picture'
        ]
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            choices = list(self.fields['state'].choices)
            if choices and choices[0][0] == '':
                choices[0] = ('', 'Escolha uma opção')
                self.fields['state'].choices = choices