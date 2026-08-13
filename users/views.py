from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from posts.models import Post
from django.contrib.auth import get_user_model
from .forms import UserRegisterForm, ProfileUpdateForm

User = get_user_model()

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
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        data = {
            'form': form,
            'user': user,
        }
        if form.is_valid():
            form.save()
            return redirect('users:my_user')
        else:
            return render(request, 'my_user.html', data)
    else:
        form = ProfileUpdateForm(instance=request.user)
        data = {
            'form': form,
            'user': user,
        }
    return render(request, 'my_user.html', data)