from django.contrib import admin

# Register your models here.
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    # 1. Remova 'get_other_user' do list_display e use 'display_participants'
    list_display = ('id', 'display_participants', 'updated_at')

    # 2. Crie uma função para listar os participantes no painel admin
    def display_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    
    # Nome da coluna no cabeçalho da tabela do Django Admin
    display_participants.short_description = 'Participantes'

# Register your models here.
admin.site.register(Conversation)
admin.site.register(Message)