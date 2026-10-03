import threading
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, authenticate
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, OuterRef, Subquery, CharField
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib import messages
from posts.models import Post, PostReaction
from .forms import LoginForm, ProfileUpdateForm, UserRegisterForm
from django_ratelimit.decorators import ratelimit
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .tokens import email_verification_token
from .models import Follow
import resend
from decouple import config

logger = logging.getLogger(__name__)
resend.api_key = config('RESEND_API_KEY', default='')

User = get_user_model()

POSTS_POR_PAGINA = 10

def com_reacoes(queryset, user):
    queryset = queryset.annotate(
        num_comments=Count('comments', distinct=True),
        num_like=Count('reactions', filter=Q(reactions__reaction_type='like'), distinct=True),
        num_laugh=Count('reactions', filter=Q(reactions__reaction_type='laugh'), distinct=True),
        num_wow=Count('reactions', filter=Q(reactions__reaction_type='wow'), distinct=True),
        num_sad=Count('reactions', filter=Q(reactions__reaction_type='sad'), distinct=True),
    )
    if user.is_authenticated:
        reacao_do_usuario = PostReaction.objects.filter(
            post_id=OuterRef('pk'), user_id=user.id
        ).values('reaction_type')[:1]
        queryset = queryset.annotate(
            user_reaction=Subquery(reacao_do_usuario, output_field=CharField())
        )
    return queryset

def enviar_email_confirmacao(request, user):
    try:
        user = User.objects.get(id=user.id)
        domain = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
        context = {
            'user': user,
            'domain': domain,
            'protocol': protocol,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': email_verification_token.make_token(user),
        }
        params = {
            "from": "Social Media <onboarding@resend.dev>",
            "to": [user.email],
            "subject": 'Confirme seu e-mail - Social Media',
            "html": render_to_string('email_verification_email_html.html', context),
        }
        email = resend.Emails.send(params)
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail de confirmação para {user.email}: {e}")

@login_required
@require_POST
def toggle_follow(request, username):
    target_user = get_object_or_404(User, username=username)

    if target_user == request.user:
        return JsonResponse({'error': 'Você não pode seguir a si mesmo.'}, status=400)

    follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
    if not created:
        follow.delete()
        following = False
    else:
        following = True

    return JsonResponse({
        'following': following,
        'followers_count': target_user.follower_relations.count(),
    })

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            threading.Thread(
                            target=enviar_email_confirmacao,
                            args=(request, user)
                        ).start()
            return render(request, 'email_verification_sent.html', {'email': user.email})
        return render(request, 'register.html', {
            'form': form,
        }, status=400)
    else:
        form = UserRegisterForm()
        return render(request, 'register.html', {'form': form})

@ratelimit(key='ip', rate='10/m', method='POST', block=True)
@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def login_view(request):
    if request.user.is_authenticated:
        return redirect(request.GET.get("next") or "home")

    form = LoginForm(request.POST or None)
    show_resend = False

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect(request.GET.get("next") or "home")

        if User.objects.filter(email=email, is_active=False).exists():
            form.add_error(
                None,
                "Sua conta ainda não foi confirmada. Verifique seu e-mail ou solicite um novo link.",
            )
            show_resend = True
        else:
            form.add_error(
                None,
                "E-mail ou senha incorretos. Confira os dados e tente novamente.",
            )

    return render(
        request,
        "login.html",
        {
            "form": form,
            "show_resend": show_resend,
        },
    )

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
            threading.Thread(
                target=enviar_email_confirmacao,
                args=(request, user)
            ).start()
        except User.DoesNotExist:
            pass
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
    user_posts = com_reacoes(
        Post.objects.filter(user=user).select_related('user'), request.user
    )
    data = {
        'profile_user': user,
        'user_posts': user_posts,
        'is_following': request.user.is_following(user) if request.user != user else None,
        'followers_count': user.follower_relations.count(),
        'following_count': user.following_relations.count(),
    }
    return render(request, 'user.html', data)

@login_required(login_url='users:login')
def my_user(request):
    user = request.user

    posts_list = com_reacoes(
        Post.objects.filter(user=user), request.user
    )
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
        'followers_count': user.follower_relations.count(),
        'following_count': user.following_relations.count(),
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