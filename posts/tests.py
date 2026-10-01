import io
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from posts.models import Post, Comment, PostReaction

User = get_user_model()


def gerar_imagem_valida():
    """Gera um arquivo de imagem JPEG válido em memória, pra testar upload."""
    buffer = io.BytesIO()
    Image.new('RGB', (10, 10), color='red').save(buffer, format='JPEG')
    buffer.seek(0)
    buffer.name = 'teste.jpg'
    return buffer


class PostModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='autor', email='autor@teste.com', password='senha123forte'
        )

    def test_post_str_retorna_titulo(self):
        post = Post.objects.create(title='Meu título', content='conteúdo', user=self.user)
        self.assertEqual(str(post), 'Meu título')

    def test_post_ordenado_por_data_decrescente(self):
        p1 = Post.objects.create(title='Primeiro', content='a', user=self.user)
        p2 = Post.objects.create(title='Segundo', content='b', user=self.user)
        posts = list(Post.objects.all())
        self.assertEqual(posts[0], p2)
        self.assertEqual(posts[1], p1)


class CreatePostViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='autor', email='autor@teste.com', password='senha123forte'
        )
        self.client.force_login(self.user)

    def test_criar_post_sem_login_redireciona(self):
        self.client.logout()
        response = self.client.get(reverse('posts:create_post'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('users:login'), response.url)

    def test_get_retorna_formulario(self):
        response = self.client.get(reverse('posts:create_post'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_post.html')

    def test_criar_post_com_sucesso(self):
        response = self.client.post(reverse('posts:create_post'), {
            'title': 'Post de teste',
            'content': 'Conteúdo de teste',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(title='Post de teste', user=self.user).exists())

    def test_criar_post_com_imagem_valida(self):
        imagem = gerar_imagem_valida()
        response = self.client.post(reverse('posts:create_post'), {
            'title': 'Com imagem',
            'content': 'Conteúdo',
            'image': imagem,
        })
        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(title='Com imagem')
        self.assertTrue(post.image)

    def test_criar_post_com_imagem_invalida_mostra_erro(self):
        arquivo_falso = io.BytesIO(b'conteudo qualquer')
        arquivo_falso.name = 'malicioso.exe'
        response = self.client.post(reverse('posts:create_post'), {
            'title': 'Imagem inválida',
            'content': 'Conteúdo',
            'image': arquivo_falso,
        })
        self.assertEqual(response.status_code, 200)  # não redireciona, volta com erro
        self.assertFalse(Post.objects.filter(title='Imagem inválida').exists())


class ToggleReactionViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.autor = User.objects.create_user(
            username='autor', email='autor@teste.com', password='senha123forte'
        )
        self.leitor = User.objects.create_user(
            username='leitor', email='leitor@teste.com', password='senha123forte'
        )
        self.post = Post.objects.create(title='Post', content='conteúdo', user=self.autor)
        self.client.force_login(self.leitor)

    def test_reagir_sem_login_retorna_redirect(self):
        self.client.logout()
        response = self.client.post(
            reverse('posts:toggle_reaction', args=[self.post.id]),
            {'reaction_type': 'like'}
        )
        self.assertEqual(response.status_code, 302)

    def test_curtir_post_cria_reacao(self):
        response = self.client.post(
            reverse('posts:toggle_reaction', args=[self.post.id]),
            {'reaction_type': 'like'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['user_reaction'], 'like')
        self.assertEqual(data['counts']['like'], 1)
        self.assertTrue(
            PostReaction.objects.filter(post=self.post, user=self.leitor, reaction_type='like').exists()
        )

    def test_clicar_na_mesma_reacao_remove(self):
        self.client.post(reverse('posts:toggle_reaction', args=[self.post.id]), {'reaction_type': 'like'})
        response = self.client.post(
            reverse('posts:toggle_reaction', args=[self.post.id]),
            {'reaction_type': 'like'}
        )
        data = response.json()
        self.assertIsNone(data['user_reaction'])
        self.assertEqual(data['counts']['like'], 0)

    def test_trocar_de_reacao_e_exclusivo(self):
        self.client.post(reverse('posts:toggle_reaction', args=[self.post.id]), {'reaction_type': 'like'})
        response = self.client.post(
            reverse('posts:toggle_reaction', args=[self.post.id]),
            {'reaction_type': 'laugh'}
        )
        data = response.json()
        self.assertEqual(data['user_reaction'], 'laugh')
        self.assertEqual(data['counts']['like'], 0)
        self.assertEqual(data['counts']['laugh'], 1)
        # garante que só existe UM registro de reação por usuário/post
        self.assertEqual(
            PostReaction.objects.filter(post=self.post, user=self.leitor).count(), 1
        )

    def test_tipo_de_reacao_invalido_retorna_400(self):
        response = self.client.post(
            reverse('posts:toggle_reaction', args=[self.post.id]),
            {'reaction_type': 'tipo_que_nao_existe'}
        )
        self.assertEqual(response.status_code, 400)


class SearchPostViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='buscador', email='buscador@teste.com', password='senha123forte'
        )
        self.client.force_login(self.user)
        Post.objects.create(title='Django é incrível', content='aprendendo framework', user=self.user)
        Post.objects.create(title='Python básico', content='outro assunto qualquer', user=self.user)

    def test_busca_sem_query_retorna_tudo(self):
        response = self.client.get(reverse('posts:search_post'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 2)

    def test_busca_por_titulo(self):
        response = self.client.get(reverse('posts:search_post'), {'q': 'Django'})
        posts = list(response.context['posts'])
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].title, 'Django é incrível')

    def test_busca_sem_resultado(self):
        response = self.client.get(reverse('posts:search_post'), {'q': 'termo_inexistente_xyz'})
        self.assertEqual(len(response.context['posts']), 0)


class PaginationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='autor', email='autor@teste.com', password='senha123forte'
        )
        self.client.force_login(self.user)
        for i in range(35):  # mais que POSTS_POR_PAGINA (30), força 2 páginas
            Post.objects.create(title=f'Post {i}', content='conteúdo', user=self.user)

    def test_primeira_pagina_tem_30_posts(self):
        response = self.client.get(reverse('posts:all_posts'))
        self.assertEqual(len(response.context['posts']), 30)

    def test_segunda_pagina_tem_o_restante(self):
        response = self.client.get(reverse('posts:all_posts'), {'page': 2})
        self.assertEqual(len(response.context['posts']), 5)

    def test_pagina_invalida_retorna_ultima_pagina(self):
        response = self.client.get(reverse('posts:all_posts'), {'page': 999})
        self.assertEqual(response.status_code, 200)  # Paginator.get_page não lança erro


class CommentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='comentarista', email='comentarista@teste.com', password='senha123forte'
        )
        self.client.force_login(self.user)
        self.post = Post.objects.create(title='Post', content='conteúdo', user=self.user)

    def test_adicionar_comentario(self):
        response = self.client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            {'content': 'Ótimo post!'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(post=self.post, content='Ótimo post!').exists())

    def test_comentario_vazio_retorna_erro(self):
        response = self.client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            {'content': ''},
        )
        self.assertEqual(response.status_code, 400)

    def test_excluir_comentario_de_outro_usuario_retorna_404(self):
        outro_usuario = User.objects.create_user(
            username='outro', email='outro@teste.com', password='senha123forte'
        )
        comentario_alheio = Comment.objects.create(post=self.post, user=outro_usuario, content='não é meu')

        response = self.client.post(reverse('posts:delete_comment', args=[comentario_alheio.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Comment.objects.filter(id=comentario_alheio.id).exists())


class DeletePostPermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dono = User.objects.create_user(
            username='dono', email='dono@teste.com', password='senha123forte'
        )
        self.outro = User.objects.create_user(
            username='outro', email='outro@teste.com', password='senha123forte'
        )
        self.post = Post.objects.create(title='Post', content='conteúdo', user=self.dono)

    def test_dono_pode_excluir(self):
        self.client.force_login(self.dono)
        self.client.post(reverse('posts:delete_post', args=[self.post.id]))
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_outro_usuario_nao_pode_excluir(self):
        self.client.force_login(self.outro)
        response = self.client.post(reverse('posts:delete_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())