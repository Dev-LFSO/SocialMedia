from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, authenticate
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.contrib import messages
from posts.models import Post
from .forms import UserRegisterForm, ProfileUpdateForm
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from .tokens import email_verification_token

User = get_user_model()

POSTS_POR_PAGINA = 10

def _enviar_email_confirmacao(request, user):
    current_site = get_current_site(request)
    subject = 'Confirme seu e-mail - Social Media'
    context = {
        'user': user,
        'domain': current_site.domain,
        'protocol': 'https' if request.is_secure() else 'http',
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': email_verification_token.make_token(user),
    }
    html_message = render_to_string('email_verification_email.html', context)
    plain_message = strip_tags(html_message)

    email = EmailMultiAlternatives(subject, plain_message, to=[user.email])
    email.attach_alternative(html_message, "text/html")
    email.send()

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            _enviar_email_confirmacao(request, user)

            return render(request, 'email_verification_sent.html', {'email': user.email})
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def login_view(request):
    if request.user.is_authenticated:
        if request.GET.get('next'):
            return redirect(request.GET.get("next"))
        return redirect('home')
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                if request.user.is_authenticated:
                    if request.GET.get('next'):
                        return redirect(request.GET.get("next"))
                    return redirect('home')
            if User.objects.filter(email=email, is_active=False).exists():
                return render(request, 'login.html', {
                    'error': 'Sua conta ainda não foi confirmada. Verifique seu e-mail.',
                    'email': email,
                    'show_resend': True,
                })
            return render(request, 'login.html', {'error': 'Senha inválida', 'email': email})
        except User.DoesNotExist:
            return render(request, 'login.html', {'error': 'Credencias inválidas'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    if request.GET.get('next'):
        return redirect(request.GET.get("next"))
    return redirect('home')

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, 'E-mail confirmado com sucesso! Bem-vindo(a).')
        return redirect('home')

    return render(request, 'email_verification_invalid.html')

@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def resend_verification_email(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            user = User.objects.get(email=email, is_active=False)
            _enviar_email_confirmacao(request, user)
        except User.DoesNotExist:
            pass  # não revela se o e-mail existe ou não, por segurança
        return render(request, 'email_verification_sent.html', {'email': email})
    return render(request, 'resend_verification.html')

def search_user(request):
    query = request.GET.get('q', '').strip()
    users_data = []

    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | Q(name__icontains=query)
        ).exclude(id=request.user.id)[:10]

        for u in users:
            users_data.append({
                'username': u.username,
                'name': u.name or u.username,
                'avatar': u.profile_picture.url if u.profile_picture else None
            })

    return JsonResponse({'users': users_data})

@never_cache
@login_required(login_url='users:login')
def get_user(request, username):
    user = get_object_or_404(User, username=username)
    likes_do_usuario = Post.likes.through.objects.filter(
        post_id=OuterRef('pk'), user_id=request.user.id
    )
    user_posts = Post.objects.filter(user=user).select_related('user').annotate(
        num_likes=Count('likes', distinct=True),
        is_liked=Exists(likes_do_usuario),
    )  # ordering já vem do Meta.ordering do modelo, não precisa repetir order_by
    data = {
        'profile_user': user,
        'user_posts': user_posts,
    }
    return render(request, 'user.html', data)

@login_required(login_url='users:login')
def my_user(request):
    user = request.user

    posts_list = Post.objects.filter(user=user).order_by('-data_posted', '-id')
    paginator = Paginator(posts_list, POSTS_POR_PAGINA)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('users:my_user')
    else:
        form = ProfileUpdateForm(instance=request.user)

    data = {
        'form': form,
        'user': user,
        'posts': posts,
    }
    return render(request, 'my_user.html', data)

@login_required
@require_POST
def remove_profile_picture(request):
    usuario_ou_perfil = request.user

    if usuario_ou_perfil.profile_picture:
        usuario_ou_perfil.profile_picture.delete(save=True)
        return JsonResponse({'status': 'success', 'message': 'Foto removida!'})

    return JsonResponse({'status': 'error', 'message': 'Nenhuma foto encontrada'}, status=400)