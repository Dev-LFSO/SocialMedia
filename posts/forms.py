from django import forms
from django.core.exceptions import ValidationError

from .models import Post


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content"]
        labels = {
            "title": "Título",
            "content": "Conteúdo",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Do que você quer falar?",
                    "autocomplete": "off",
                    "maxlength": 200,
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "placeholder": "Escreva o que estiver pensando...",
                    "rows": 8,
                }
            ),
        }
        error_messages = {
            "title": {
                "required": "Escreva um título para a publicação.",
                "max_length": "O título pode ter no máximo 200 caracteres.",
            },
            "content": {
                "required": "Escreva algo no conteúdo do post antes de publicar.",
            },
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()

        if not title:
            raise ValidationError("O título não pode conter apenas espaços.")

        return title

    def clean_content(self):
        content = self.cleaned_data["content"].strip()

        if not content:
            raise ValidationError("O conteúdo não pode conter apenas espaços.")

        return content