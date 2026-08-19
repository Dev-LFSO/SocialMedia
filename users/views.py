from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, authenticate
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from posts.models import Post
from django.db.models import Q
from django.contrib.auth import get_user_model
from .forms import UserRegisterForm, ProfileUpdateForm

User = get_user_model()

POSTS_POR_PAGINA = 10

# Create your views here.
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            login(request, user)
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

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
            return render(request, 'login.html', {'error': 'Senha inválida', 'email': email})
        except User.DoesNotExist:
            return render(request, 'login.html', {'error': 'Credencias inválidas'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    if request.GET.get('next'):
        return redirect(request.GET.get("next"))
    return redirect('home')

def search_user(request):
    query = request.GET.get('q', '').strip()
    users_data = []

    if query:
        # Busca por username ou nome, excluindo o próprio usuário logado
        users = User.objects.filter(
            Q(username__icontains=query) | Q(name__icontains=query)
        ).exclude(id=request.user.id)[:10]  # Limita aos 10 primeiros resultados

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
    user_posts = Post.objects.filter(user=user).order_by('-data_posted')
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
    # Adapte caso a foto esteja no request.user ou em um modelo relacionado (ex: request.user.perfil)
    usuario_ou_perfil = request.user 

    if usuario_ou_perfil.profile_picture:
        # Apaga o arquivo físico da imagem e limpa o campo
        usuario_ou_perfil.profile_picture.delete(save=True)
        return JsonResponse({'status': 'success', 'message': 'Foto removida!'})
    
    return JsonResponse({'status': 'error', 'message': 'Nenhuma foto encontrada'}, status=400)