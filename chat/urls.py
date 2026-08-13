from django.urls import path
from .views import get_chat, start_chat, send_message, delete_chat

app_name = 'chat'

urlpatterns = [
    path('', get_chat, name='get_chat'),
    path('<int:conversation_id>', get_chat, name='get_chat'),
    path('start_chat/<str:username>/', start_chat, name='start_chat'),
    path('send_message/<int:conversation_id>', send_message, name='send_message'),
    path('delete_chat/<int:conversation_id>', delete_chat, name='delete_chat')
]