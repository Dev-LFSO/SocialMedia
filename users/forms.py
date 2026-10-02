from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["email", "username"]
        labels = {
            "email": "E-mail",
            "username": "Nome de usuário",
        }
        error_messages = {
            "email": {
                "required": "Informe seu e-mail para criar a conta.",
                "invalid": "Digite um e-mail válido, como nome@exemplo.com.",
                "unique": "Já existe uma conta cadastrada com este e-mail.",
            },
            "username": {
                "required": "Escolha um nome de usuário.",
                "unique": "Este nome de usuário já está em uso. Tente outro.",
                "max_length": "O nome de usuário é muito longo.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].label = "Senha"
        self.fields["password1"].help_text = "Use pelo menos 8 caracteres."
        self.fields["password1"].error_messages["required"] = "Crie uma senha para sua conta."

        self.fields["password2"].label = "Confirme sua senha"
        self.fields["password2"].error_messages["required"] = "Confirme a senha informada."
        self.fields["password2"].error_messages["password_mismatch"] = (
            "As senhas não coincidem. Confira e tente novamente."
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Já existe uma conta cadastrada com este e-mail.")

        return email


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "name", "username", "email", "cpf",
            "bio", "city", "state", "country", "profile_picture",
        ]
        widgets = {
            "profile_picture": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp"}
            ),
        }
        error_messages = {
            "email": {
                "invalid": "Digite um e-mail válido.",
                "unique": "Este e-mail já está sendo usado por outra conta.",
            },
            "username": {
                "unique": "Este nome de usuário já está em uso.",
            },
            "cpf": {
                "unique": "Este CPF já está cadastrado em outra conta.",
            },
            "bio": {
                "max_length": "A biografia pode ter no máximo 280 caracteres.",
            },
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Este e-mail já está sendo usado por outra conta.")

        return email

class LoginForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={
                "class": "input-email",
                "autocomplete": "email",
                "placeholder": "nome@exemplo.com",
            }
        ),
        error_messages={
            "required": "Informe seu e-mail.",
            "invalid": "Digite um e-mail válido, como nome@exemplo.com.",
        },
    )

    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "input-password",
                "autocomplete": "current-password",
            }
        ),
        error_messages={
            "required": "Informe sua senha.",
        },
    )