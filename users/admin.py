from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdmin(BaseUserAdmin):
    # Tela de edição de um usuário já existente
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Perfil', {
            'fields': ('name', 'email', 'bio', 'cpf', 'country', 'state', 'city', 'profile_picture'),
        }),
        ('Status', {'fields': ('is_active','is_superuser')}),
    )

    # Tela de criação de um novo usuário
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Perfil', {
            'fields': ('name', 'email','bio', 'cpf', 'country', 'state', 'city', 'profile_picture'),
        }),
    )

    list_display = ('username', 'name', 'email', 'is_active', 'is_superuser')
    search_fields = ('username', 'name', 'cpf')


admin.site.register(User, UserAdmin)