from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import Follow

User = get_user_model()


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_cadastro_cria_usuario_inativo(self):
        response = self.client.post(reverse('users:register'), {
            'username': 'novo_usuario',
            'email': 'novo@teste.com',
            'password1': 'senhaForte123!',
            'password2': 'senhaForte123!',
        })
        user = User.objects.get(username='novo_usuario')
        self.assertFalse(user.is_active)  # precisa confirmar e-mail antes

    def test_login_com_conta_inativa_mostra_erro(self):
        User.objects.create_user(
            username='inativo', email='inativo@teste.com', password='senha123forte',
            is_active=False,
        )
        response = self.client.post(reverse('users:login'), {
            'email': 'inativo@teste.com',
            'password': 'senha123forte',
        })
        self.assertContains(response, 'ainda não foi confirmada')


class FollowViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(
            username='usuario_a', email='a@teste.com', password='senha123forte'
        )
        self.user_b = User.objects.create_user(
            username='usuario_b', email='b@teste.com', password='senha123forte'
        )
        self.client.force_login(self.user_a)

    def test_seguir_usuario(self):
        response = self.client.post(reverse('users:toggle_follow', args=[self.user_b.username]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['following'])
        self.assertTrue(Follow.objects.filter(follower=self.user_a, following=self.user_b).exists())

    def test_deixar_de_seguir(self):
        self.client.post(reverse('users:toggle_follow', args=[self.user_b.username]))
        response = self.client.post(reverse('users:toggle_follow', args=[self.user_b.username]))
        data = response.json()
        self.assertFalse(data['following'])
        self.assertFalse(Follow.objects.filter(follower=self.user_a, following=self.user_b).exists())

    def test_nao_pode_seguir_a_si_mesmo(self):
        response = self.client.post(reverse('users:toggle_follow', args=[self.user_a.username]))
        self.assertEqual(response.status_code, 400)