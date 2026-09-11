from django.db import models
from django.conf import settings

# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    content = models.TextField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_posts', blank=True)
    data_posted = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-data_posted']

    def __str__(self) -> str:
        return self.title