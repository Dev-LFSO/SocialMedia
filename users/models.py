import re
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


def validate_cpf(value):
    cpf = re.sub(r'\D', '', value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')

    def calc_digit(partial):
        weights = list(range(len(partial) + 1, 1, -1))
        total = sum(int(d) * w for d, w in zip(partial, weights))
        rest = (total * 10) % 11
        return rest if rest < 10 else 0

    d1 = calc_digit(cpf[:9])
    d2 = calc_digit(cpf[:9] + str(d1))
    if cpf[-2:] != f'{d1}{d2}':
        raise ValidationError('CPF inválido.')


def profile_picture_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'profile_pictures/user_{instance.pk or "new"}.{ext}'


UF_CHOICES = [
    ('', 'Escolha uma opção'), ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
    ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'),
    ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'),
    ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
    ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'), ('PE', 'Pernambuco'),
    ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
    ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'),
    ('SC', 'Santa Catarina'), ('SP', 'São Paulo'), ('SE', 'Sergipe'),
    ('TO', 'Tocantins'),
]


class User(AbstractUser):
    name = models.CharField('Nome completo', max_length=150, blank=True)
    email = models.EmailField('Email', max_length=254, unique=True)
    bio = models.TextField('Bio', max_length=280, blank=True)
    cpf = models.CharField(
        'CPF', max_length=14, unique=True, null=True, blank=True,
        validators=[validate_cpf],
    )
    country = models.CharField('País', max_length=60, blank=True, default='Brasil')
    state = models.CharField('UF', max_length=2, choices=UF_CHOICES, blank=True)
    city = models.CharField('Cidade', max_length=100, blank=True)
    profile_picture = models.ImageField(
        'Foto de perfil', upload_to=profile_picture_path, blank=True, null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.name or self.username