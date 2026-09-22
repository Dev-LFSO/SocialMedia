from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, ImageOps
import io
from django.core.files.base import ContentFile

MAX_POST_IMAGE_SIZE_MB = 8
ALLOWED_POST_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
ALLOWED_POST_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
# Importe ValidationError e suas constantes conforme o seu projeto

MAX_WIDTH = 1080
MAX_HEIGHT = 1080

def validate_and_resize_post_image(file):
    # 1. Validações iniciais (Tamanho em MB, Content-Type e Extensão)
    max_size_bytes = MAX_POST_IMAGE_SIZE_MB * 1024 * 1024
    if file.size > max_size_bytes:
        raise ValidationError(
            f'A imagem não pode ultrapassar {MAX_POST_IMAGE_SIZE_MB}MB '
            f'(tamanho atual: {file.size / (1024 * 1024):.1f}MB).'
        )
    content_type = getattr(file, 'content_type', None)
    if content_type and content_type not in ALLOWED_POST_IMAGE_TYPES:
        raise ValidationError(
            'Formato de imagem inválido. Envie um arquivo JPG, PNG, WEBP ou GIF.'
        )

    nome = file.name.lower()
    if not any(nome.endswith(ext) for ext in ALLOWED_POST_IMAGE_EXTENSIONS):
        raise ValidationError(
            'Extensão de arquivo inválida. Use .jpg, .jpeg, .png, .webp ou .gif.'
        )

    # 2. Redimensionamento da Imagem
    try:
        img = Image.open(file)

        # Trata a rotação baseada nos dados EXIF da câmera/celular
        img = ImageOps.exif_transpose(img)

        # Não redimensiona GIFs animados para preservar as camadas/animação
        if img.format == 'GIF' and getattr(img, "is_animated", False):
            file.seek(0)
            return file

        # Aplica o redimensionamento apenas se ultrapassar os limites
        if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
            img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)

            img_format = img.format if img.format else 'JPEG'

            # Se for salvar em JPEG, qualquer modo diferente de RGB (RGBA, P, CMYK, LA) precisa ser convertido
            if img_format.upper() in ['JPG', 'JPEG'] and img.mode != 'RGB':
                img = img.convert('RGB')

            # Salva o arquivo ajustado em memória
            output_buffer = io.BytesIO()
            save_kwargs = {'format': img_format, 'optimize': True}
            
            # O parâmetro quality só se aplica a JPEG e WebP
            if img_format.upper() in ['JPG', 'JPEG', 'WEBP']:
                save_kwargs['quality'] = 85

            img.save(output_buffer, **save_kwargs)

            # Substitui os bytes do arquivo original para o Django
            file.file = ContentFile(output_buffer.getvalue())

    except Exception as e:
        print(e)
        raise ValidationError('Não foi possível processar ou redimensionar a imagem enviada.')

    file.seek(0)
    return file


def post_image_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'post_images/user_{instance.user_id}/{instance}.{ext}'


class Post(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    content = models.TextField()
    image = models.ImageField(
        'Imagem', upload_to=post_image_path, blank=True, null=True,
        validators=[validate_and_resize_post_image],
    )
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

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'{self.user.username}: {self.content[:30]}'