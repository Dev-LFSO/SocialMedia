from django.db import models
from django.conf import settings

class ConversationManager(models.Manager):
    def get_or_create_one_to_one(self, user1, user2):
        """
        Busca uma conversa existente entre user1 e user2.
        Se não existir, cria uma nova exatamente com os dois.
        """
        if user1 == user2:
            raise ValueError("Um usuário não pode iniciar um chat consigo mesmo.")

        # Busca conversas que contêm AMBOS os usuários
        conversation = self.filter(participants=user1).filter(participants=user2).first()

        if conversation:
            return conversation, False  # (conversa, criada_agora=False)

        # Se não existe, cria a conversa e adiciona os dois participantes
        new_conversation = self.create()
        new_conversation.participants.add(user1, user2)
        return new_conversation, True  # (conversa, criada_agora=True)

class Conversation(models.Model):
    """
    Representa o canal/thread de bate-papo entre os usuários.
    """
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
        """Helper para retornar o outro participante em chats 1x1"""
        return self.participants.exclude(id=current_user.id).first()

    def unread_count_for(self, user):
        """Retorna quantas mensagens não lidas o usuário tem nesta conversa"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()
    
    def last_message(self):
        """Retorna a última mensagem enviada no chat"""
        return self.messages.order_by('-timestamp').first()

    def __str__(self):
        participants_names = ", ".join([u.username for u in self.participants.all()])
        return f"Conversa #{self.id} ({participants_names})"


class Message(models.Model):
    """
    Representa cada mensagem enviada dentro de uma conversa.
    """
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
    
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'{self.sender.username}: {self.content[:30] if self.content else "Anexo"}'