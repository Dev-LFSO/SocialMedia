from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
import os
import uuid
from django.utils.text import slugify

MAX_ATTACHMENT_SIZE_MB = 50
ALLOWED_ATTACHMENT_TYPES = [
    'image/jpeg', 'image/png', 'image/webp', 'image/gif',
    'application/pdf', 'video/mp4', 'audio/mp3'
]
ALLOWED_ATTACHMENT_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.pdf', '.mp4', '.mp3']

def validate_attachment(file):
    max_size_bytes = MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
    if file.size > max_size_bytes:
        raise ValidationError(
            f'O anexo não pode ultrapassar {MAX_ATTACHMENT_SIZE_MB}MB '
            f'(tamanho atual: {file.size / (1024 * 1024):.1f}MB).'
        )

    content_type = getattr(file, 'content_type', None)
    if content_type and content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise ValidationError(
            'Formato de arquivo inválido. Envie uma imagem (JPG, PNG, WEBP, GIF) ou um PDF.'
        )

    nome = file.name.lower()
    if not any(nome.endswith(ext) for ext in ALLOWED_ATTACHMENT_EXTENSIONS):
        raise ValidationError(
            'Extensão de arquivo inválida.'
        )

def attachment_path(instance, filename):
    name, ext = os.path.splitext(filename)
    safe_name = slugify(name) or 'file'
    unique_id = uuid.uuid4().hex[:8]
    clean_filename = f"{safe_name}_{unique_id}{ext.lower()}"
    return f"chat_attachments/conversation_{instance.conversation_id}/{clean_filename}"

class ConversationManager(models.Manager):
    def get_or_create_one_to_one(self, user1, user2):
        if user1 == user2:
            raise ValueError("Um usuário não pode iniciar um chat consigo mesmo.")

        conversation = self.filter(participants=user1).filter(participants=user2).first()

        if conversation:
            return conversation, False

        new_conversation = self.create()
        new_conversation.participants.add(user1, user2)
        return new_conversation, True


class Conversation(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ConversationManager()

    class Meta:
        ordering = ['-updated_at']

    def get_other_user(self, current_user):
        return self.participants.exclude(id=current_user.id).first()

    def unread_count_for(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def last_message(self):
        return self.messages.order_by('-timestamp').first()

    def __str__(self):
        participants_names = ", ".join([u.username for u in self.participants.all()])
        return f"Conversa #{self.id} ({participants_names})"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField(blank=True, null=True)
    attachment = models.FileField(
        upload_to=attachment_path, blank=True, null=True,
        validators=[validate_attachment],
    )
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def is_image(self):
        if not self.attachment:
            return False
        return self.attachment.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))

    @property
    def attachment_filename(self):
        if not self.attachment:
            return ''
        return os.path.basename(self.attachment.name)

    def __str__(self):
        return f'{self.sender.username}: {self.content[:30] if self.content else "Anexo"}'