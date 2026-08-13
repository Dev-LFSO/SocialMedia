from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from .models import Post
from django.db.models import Count, Q
from django.http import JsonResponse


# Create your views here.
@never_cache
def all_posts(request):
    posts = Post.objects.all()
    posts_mais_curtidos = Post.objects.annotate(num_likes=Count('likes')).order_by('-num_likes')
    return render(request, 'all_posts.html', {'posts': posts, 'more_liked_posts':posts_mais_curtidos})

@login_required(login_url='users:login')
@require_POST
def like_post(request, post_id):
    post = Post.objects.get(id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'liked_counts': post.likes.count()})

@login_required(login_url='users:login')
def create_post(request):
    if request.method == "GET":
        return render(request, 'create_post.html')
    elif request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        Post.objects.create(title=title, content=content, user=request.user)
        return redirect("posts:all_posts")

@login_required(login_url='users:login')
def delete_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id, user=request.user)
        post.delete()
    return redirect(request.META.get('HTTP_REFERER', 'users:my_user'))

@never_cache
def search_post(request):
    query = request.GET.get('q', '').strip()
    posts = Post.objects.all()

    if query:
        posts = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(user__name__icontains=query) |
            Q(user__username__icontains=query)
        ).distinct().order_by('-data_posted')
        
    context = {
        'query': query,
        'posts': posts,
    }
    return render(request, 'search_post.html', context)