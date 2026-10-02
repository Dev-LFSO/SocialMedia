"""
Comando para popular o banco com usuários de teste.

Como usar:

1. Coloque este arquivo em:
   users/management/commands/seed_users.py

   Crie as pastas "management" e "commands" se não existirem.
   Cada uma precisa de um arquivo vazio __init__.py dentro:

   users/
   ├── management/
   │   ├── __init__.py
   │   └── commands/
   │       ├── __init__.py
   │       └── seed_users.py  <-- este arquivo

2. Rode no terminal (dentro do ambiente virtual do projeto):

   python manage.py seed_users

   Isso cria 10 usuários (padrão).

   Para escolher outra quantidade:

   python manage.py seed_users --count 100

   Para apagar os usuários de teste antes de gerar novos:

   python manage.py seed_users --count 10 --flush
"""

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


User = get_user_model()


FIRST_NAMES = [
    "João",
    "Maria",
    "Carlos",
    "Ana",
    "Pedro",
    "Lucas",
    "Julia",
    "Gabriel",
    "Beatriz",
    "Rafael",
    "Mariana",
    "Felipe",
    "Larissa",
    "Bruno",
    "Camila",
    "Gustavo",
    "Amanda",
    "Matheus",
    "Isabela",
    "Daniel",
]

LAST_NAMES = [
    "Silva",
    "Santos",
    "Oliveira",
    "Souza",
    "Costa",
    "Pereira",
    "Rodrigues",
    "Almeida",
    "Nascimento",
    "Lima",
    "Carvalho",
    "Gomes",
    "Martins",
    "Ribeiro",
    "Fernandes",
]


class Command(BaseCommand):
    help = "Cria usuários de teste."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Quantidade de usuários a criar (padrão: 10).",
        )

        parser.add_argument(
            "--flush",
            action="store_true",
            help="Apaga os usuários de teste existentes antes de criar novos.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        flush = options["flush"]

        if count <= 0:
            self.stdout.write(
                self.style.ERROR(
                    "A quantidade de usuários deve ser maior que zero."
                )
            )
            return

        if flush:
            deleted, _ = User.objects.filter(
                username__startswith="testuser_"
            ).delete()

            self.stdout.write(
                self.style.WARNING(
                    f"{deleted} usuário(s) de teste removido(s)."
                )
            )

        users_created = []

        for i in range(count):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)

            username = f"testuser_{i + 1}"

            user = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=f"{username}@example.com",
            )

            user.set_password("12345678")

            users_created.append(user)

        User.objects.bulk_create(users_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} usuário(s) criado(s) com sucesso."
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Senha padrão dos usuários: 12345678"
            )
        )