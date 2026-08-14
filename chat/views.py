from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Conversation, Message
# Create your views here.

User = get_user_model()

@login_required(login_url='users:login')
def get_chat(request, conversation_id=None):
    conversations = request.user.conversations.all()
    
    # Prepara o outro participante para a lista do sidebar
    for conv in conversations:
        conv.other_user = conv.get_other_user(request.user)

    active_conversation = None
    messages = []

    # Se um ID de conversa foi passado na URL
    if conversation_id:
        active_conversation = get_object_or_404(
            Conversation, id=conversation_id, participants=request.user
        )
        active_conversation.other_user = active_conversation.get_other_user(request.user)
        
        # Marca mensagens como lidas
        active_conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        messages = active_conversation.messages.all()

    data = {
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages': messages,
    }

    for conversation in conversations:
        print(conversation.last_message())

    # Renderiza a página
    return render(request, 'chat.html', data)

@login_required
def start_chat(request, username):
    """
    Inicia ou redireciona para a conversa 1x1 com o usuário informado.
    """
    target_user = get_object_or_404(User, username=username)

    # Impede conversa com você mesmo
    if target_user == request.user:
        return redirect('chat:get_chat')

    # Garante que só existe 1 conversa entre esses dois usuários
    conversation, _ = Conversation.objects.get_or_create_one_to_one(
        request.user, target_user
    )

    # Redireciona para a tela do chat com o ID da conversa
    return redirect('chat:get_chat', conversation_id=conversation.id)

@login_required
@require_POST
def send_message(request, conversation_id):
    """
    Cria uma nova mensagem na conversa especificada.
    """
    # 1. Busca a conversa garantindo que o usuário logado é um dos participantes (Segurança)
    conversation = get_object_or_404(
        Conversation, 
        id=conversation_id, 
        participants=request.user
    )

    # 2. Captura o conteúdo do texto e do anexo (se houver)
    content = request.POST.get('content', '').strip()

    # 3. Validação: impede o envio de mensagens vazias
    if not content:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'A mensagem não pode estar vazia.'}, status=400)
        return redirect('chat:get_chat', conversation_id=conversation.id)

    # 4. Salva a mensagem no Banco de Dados
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
    )

    # 5. Atualiza o `updated_at` da conversa para ela subir ao topo no sidebar
    conversation.save()

    # 6. RESPOSTA PARA REQUISIÇÕES AJAX (Envio instantâneo sem refresh)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'attachment_url': message.attachment.url if message.attachment else None,
                'is_read': message.is_read
            }
        })

    # 7. RESPOSTA PADRÃO (Redirecionamento normal de formulário HTML)
    return redirect('chat:get_chat', conversation_id=conversation.id)

@login_required
@require_POST
def delete_chat(request, conversation_id):
    """
    Exclui uma conversa garantindo que o usuário pertence a ela.
    """
    conversation = get_object_or_404(
        Conversation, id=conversation_id, participants=request.user
    )
    conversation.delete()
    return JsonResponse({'success': True})