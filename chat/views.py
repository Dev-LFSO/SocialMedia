from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Prefetch
from .models import Conversation, Message

User = get_user_model()


@login_required(login_url='users:login')
def get_chat(request, conversation_id=None):
    conversations = (
        request.user.conversations
        .prefetch_related('participants')
        .prefetch_related(
            Prefetch('messages', queryset=Message.objects.select_related('sender').order_by('-timestamp'))
        )
    )

    # Prepara o outro participante para a lista do sidebar (agora sem query extra,
    # já que 'participants' foi prefetchado acima)
    for conv in conversations:
        conv.other_user = conv.get_other_user(request.user)
        # Usa o prefetch de messages já carregado, em vez de chamar last_message()
        # (que dispararia uma nova query)
        msgs_prefetched = list(conv.messages.all())
        conv.cached_last_message = msgs_prefetched[0] if msgs_prefetched else None

    active_conversation = None
    messages = []

    if conversation_id:
        active_conversation = get_object_or_404(
            Conversation.objects.prefetch_related('participants'),
            id=conversation_id, participants=request.user
        )
        active_conversation.other_user = active_conversation.get_other_user(request.user)

        active_conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        messages = active_conversation.messages.select_related('sender').all()

    data = {
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages': messages,
    }

    return render(request, 'chat.html', data)

@login_required
def start_chat(request, username):
    target_user = get_object_or_404(User, username=username)

    if target_user == request.user:
        return redirect('chat:get_chat')

    conversation, _ = Conversation.objects.get_or_create_one_to_one(
        request.user, target_user
    )

    return redirect('chat:get_chat', conversation_id=conversation.id)

@login_required
@require_POST
def send_message(request, conversation_id):
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    content = request.POST.get('content', '').strip()

    if not content:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'A mensagem não pode estar vazia.'}, status=400)
        return redirect('chat:get_chat', conversation_id=conversation.id)

    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
    )

    conversation.save()

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

    return redirect('chat:get_chat', conversation_id=conversation.id)

@login_required
@require_POST
def delete_chat(request, conversation_id):
    conversation = get_object_or_404(
        Conversation, id=conversation_id, participants=request.user
    )
    conversation.delete()
    return JsonResponse({'success': True})