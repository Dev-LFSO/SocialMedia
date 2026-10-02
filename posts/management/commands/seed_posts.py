"""
Comando para popular o banco com posts de teste.

Como usar:
1. Coloque este arquivo em: posts/management/commands/seed_posts.py
   (crie as pastas "management" e "management/commands" se não existirem,
   cada uma precisa de um arquivo vazio __init__.py dentro)

   posts/
   ├── management/
   │   ├── __init__.py
   │   └── commands/
   │       ├── __init__.py
   │       └── seed_posts.py   <-- este arquivo

2. Rode no terminal (dentro do ambiente virtual do projeto):
   python manage.py seed_posts

   Isso cria 60 posts (padrão). Pra escolher outra quantidade:
   python manage.py seed_posts --count 100

   Pra apagar todos os posts antes de gerar novos:
   python manage.py seed_posts --count 60 --flush
"""
import random
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from posts.models import Post

User = get_user_model()

TITULOS = [
    "Reflexões sobre o dia a dia", "Uma novidade incrível", "Preciso desabafar",
    "Dica rápida pra vocês", "Meu fim de semana", "Alguém mais viu isso?",
    "Aprendi algo novo hoje", "Compartilhando uma conquista", "Pensamento aleatório",
    "Sobre produtividade", "Receita nova que testei", "Filme que recomendo",
    "Notícia que me marcou", "Progresso no projeto", "Dúvida pra comunidade",
    "Momento nostálgico", "Planejando as próximas semanas", "Livro que estou lendo",
    "Experiência de hoje", "Update rápido",
]

PARAGRAFOS = [
    "Hoje foi um dia produtivo, consegui organizar várias tarefas que estavam pendentes há um tempo.",
    "Estava pensando sobre como pequenas mudanças de hábito fazem diferença no longo prazo.",
    "Queria compartilhar essa experiência com vocês porque acho que pode ajudar alguém.",
    "Passei a tarde testando algumas ideias novas e o resultado surpreendeu bastante.",
    "Às vezes a gente esquece de parar e valorizar as pequenas conquistas do cotidiano.",
    "Depois de muito tempo tentando, finalmente consegui resolver aquele problema chato.",
    "Ando refletindo bastante sobre prioridades e para onde quero direcionar meu tempo.",
    "Foi um daqueles dias corridos, mas no final valeu muito a pena.",
    "Gostaria de saber a opinião de vocês sobre esse assunto, comentem aí embaixo!",
    "Uma conversa recente me fez repensar algumas coisas e queria registrar aqui.",
]


class Command(BaseCommand):
    help = "Cria posts de teste distribuídos entre usuários existentes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=60,
            help="Quantidade de posts a criar (padrão: 60).",
        )
        parser.add_argument(
            "--flush", action="store_true",
            help="Apaga todos os posts existentes antes de criar os novos.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        flush = options["flush"]

        users = list(User.objects.all())
        if not users:
            raise CommandError(
                "Nenhum usuário encontrado. Crie pelo menos um usuário "
                "(ex: python manage.py createsuperuser) antes de rodar este comando."
            )

        if flush:
            deleted, _ = Post.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"{deleted} post(s) removido(s)."))

        posts_criados = []
        for i in range(count):
            titulo = f"{random.choice(TITULOS)} #{i + 1}"
            conteudo = " ".join(random.sample(PARAGRAFOS, k=random.randint(1, 3)))
            autor = random.choice(users)

            posts_criados.append(
                Post(title=titulo, content=conteudo, user=autor)
            )

        Post.objects.bulk_create(posts_criados)

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} posts criados com sucesso, distribuídos entre {len(users)} usuário(s)."
            )
        )