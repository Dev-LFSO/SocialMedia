from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.core.cache import cache
from django.template.loader import render_to_string
from django.urls import reverse
from .models import Post
from .forms import PostCreateForm
from django.db.models import Count, Q, Exists, OuterRef
from django.http import JsonResponse

POSTS_POR_PAGINA = 30
CACHE_KEY_MAIS_CURTIDOS = 'posts:mais_curtidos'
CACHE_TTL_MAIS_CURTIDOS = 300

def _com_likes(queryset, user):
    queryset = queryset.annotate(num_likes=Count('likes', distinct=True))
    if user.is_authenticated:
        likes_do_usuario = Post.likes.through.objects.filter(
            post_id=OuterRef('pk'), user_id=user.id
        )
        queryset = queryset.annotate(is_liked=Exists(likes_do_usuario))
    return queryset

def _get_mais_curtidos_ids():
    ids = cache.get(CACHE_KEY_MAIS_CURTIDOS)
    if ids is None:
        ids = list(
            Post.objects.annotate(num_likes=Count('likes', distinct=True))
            .filter(num_likes__gt=0)
            .order_by('-num_likes')
            .values_list('id', flat=True)[:10]
        )
        cache.set(CACHE_KEY_MAIS_CURTIDOS, ids, CACHE_TTL_MAIS_CURTIDOS)
    return ids

@never_cache
def all_posts(request):
    posts_list = _com_likes(
        Post.objects.select_related('user'), request.user
    )

    paginator = Paginator(posts_list, POSTS_POR_PAGINA)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    # Requisição AJAX do infinite scroll: retorna só o HTML novo + metadados de paginação
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('partials/posts_feed.html', {'posts': posts, 'user': request.user}, request=request)
        return JsonResponse({
            'html': html,
            'has_next': posts.has_next(),
            'next_page_number': posts.next_page_number() if posts.has_next() else None,
        })

    ids_mais_curtidos = _get_mais_curtidos_ids()
    posts_mais_curtidos = _com_likes(
        Post.objects.filter(id__in=ids_mais_curtidos).select_related('user'),
        request.user,
    )
    posts_mais_curtidos = sorted(
        posts_mais_curtidos, key=lambda p: ids_mais_curtidos.index(p.id)
    )

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

    cache.delete(CACHE_KEY_MAIS_CURTIDOS)

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

@login_required(login_url="users:login")
def create_post(request):
    if request.method == "POST":
        form = PostCreateForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect("posts:all_posts")
    else:
        form = PostCreateForm()

    return render(request, "create_post.html", {"form": form})

@login_required(login_url='users:login')
def delete_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id, user=request.user)
        post.delete()
        cache.delete(CACHE_KEY_MAIS_CURTIDOS)
    return redirect(request.META.get('HTTP_REFERER', 'users:my_user'))

@never_cache
def search_post(request):
    query = request.GET.get('q', '').strip()
    posts_list = Post.objects.select_related('user')

    if query:
        posts_list = Post.objects.select_related('user').filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(user__name__icontains=query) |
            Q(user__username__icontains=query)
        ).distinct()

    posts_list = _com_likes(posts_list, request.user)

    paginator = Paginator(posts_list, POSTS_POR_PAGINA)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    context = {
        'query': query,
        'posts': posts,
    }
    return render(request, 'search_post.html', context)