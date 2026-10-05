from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from SocialMedia.decorators import owner_required
from .models import Conversation, Message
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

@login_required(login_url='users:login')
def get_chat(request, conversation_id=None):
    try:
        conversations = (
            request.user.conversations
            .prefetch_related('participants')
            .prefetch_related(
                Prefetch('messages', queryset=Message.objects.select_related('sender').order_by('-timestamp'))
            )
        )

        for conv in conversations:
            conv.other_user = conv.get_other_user(request.user)
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
    except Exception as e:
        logger.error(f"Erro ao pegar char: {e}")

@login_required
def start_chat(request, username):
    try:
        target_user = get_object_or_404(User, username=username)

        if target_user == request.user:
            return redirect('chat:get_chat')

        conversation, _ = Conversation.objects.get_or_create_one_to_one(
            request.user, target_user
        )

        return redirect('chat:get_chat', conversation_id=conversation.id)
    except Exception as e:
        logger.error(f"Erro ao começar chat: {e}")

@login_required
@require_POST
def send_message(request, conversation_id):
    try:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )

        content = request.POST.get('content', '').strip()
        attachment = request.FILES.get('attachment')

        if not content and not attachment:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'A mensagem não pode estar vazia.'}, status=400)
            return redirect('chat:get_chat', conversation_id=conversation.id)

        message = Message(
            conversation=conversation,
            sender=request.user,
            content=content or None,
        )
        if attachment:
            message.attachment = attachment
        try:
            message.full_clean()
        except ValidationError as e:
            errors = e.message_dict.get('attachment', e.messages)
            error_msg = ' '.join(errors) if isinstance(errors, list) else str(errors)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': error_msg}, status=400)
            print(e)
            return redirect('chat:get_chat', conversation_id=conversation.id)

        message.save()

        conversation.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'timestamp': message.timestamp.strftime('%H:%M'),
                    'attachment_url': message.attachment.url if message.attachment else None,
                    'is_image': message.is_image(),
                    'is_read': message.is_read
                }
            })

        return redirect('chat:get_chat', conversation_id=conversation.id)
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")

@login_required
@owner_required(Message, pk_url_kwarg='message_id', owner_field='sender')
@require_POST
def delete_message(request, message_id):
    message = request.owned_object

    # Apaga o arquivo físico do anexo, se existir, antes de excluir o registro
    if message.attachment:
        message.attachment.delete(save=False)

    conversation_id = message.conversation_id
    message.delete()

    return JsonResponse({'success': True, 'conversation_id': conversation_id})

@login_required
@require_POST
def delete_chat(request, conversation_id):
    conversation = get_object_or_404(
        Conversation, id=conversation_id, participants=request.user
    )
    conversation.delete()
    return JsonResponse({'success': True})