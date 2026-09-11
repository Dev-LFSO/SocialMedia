from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.urls import reverse
from .models import Post
from django.db.models import Count, Q, Exists, OuterRef
from django.http import JsonResponse

POSTS_POR_PAGINA = 30


def _com_likes(queryset, user):
    """
    Anota a queryset de posts com:
    - num_likes: total de curtidas (evita post.likes.count no template)
    - is_liked: se o usuário logado curtiu (evita request.user in post.likes.all)
    Isso elimina o N+1 do feed, tudo resolvido em 1-2 queries só.
    """
    queryset = queryset.annotate(num_likes=Count('likes', distinct=True))
    if user.is_authenticated:
        likes_do_usuario = Post.likes.through.objects.filter(
            post_id=OuterRef('pk'), user_id=user.id
        )
        queryset = queryset.annotate(is_liked=Exists(likes_do_usuario))
    return queryset


@never_cache
def all_posts(request):
    posts_list = _com_likes(
        Post.objects.select_related('user'), request.user
    ).order_by('-data_posted')

    paginator = Paginator(posts_list, POSTS_POR_PAGINA)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    posts_mais_curtidos = _com_likes(
        Post.objects.select_related('user'), request.user
    ).order_by('-num_likes')[:10]

    return render(request, 'all_posts.html', {'posts': posts, 'more_liked_posts': posts_mais_curtidos})


@login_required(login_url='users:login')
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'like_count': post.likes.count()})

def goto_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posicao = Post.objects.filter(
        Q(data_posted__gt=post.data_posted) |
        Q(data_posted=post.data_posted, id__gt=post.id)
    ).count()
    pagina = (posicao // POSTS_POR_PAGINA) + 1

    url = f"{reverse('posts:all_posts')}?page={pagina}#{post.id}"
    return redirect(url)

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
    posts_list = Post.objects.select_related('user').order_by('-data_posted')

    if query:
        posts_list = Post.objects.select_related('user').filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(user__name__icontains=query) |
            Q(user__username__icontains=query)
        ).distinct().order_by('-data_posted')

    posts_list = _com_likes(posts_list, request.user)

    paginator = Paginator(posts_list, POSTS_POR_PAGINA)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    context = {
        'query': query,
        'posts': posts,
    }
    return render(request, 'search_post.html', context)