from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.urls import reverse
from .models import Post, Comment, PostReaction, REACTION_CHOICES
from SocialMedia.decorators import owner_required
from django.db.models import Count, Q, Exists, OuterRef, Subquery, CharField
from django.http import JsonResponse
from django.db import IntegrityError

POSTS_POR_PAGINA = 30
CACHE_KEY_MAIS_CURTIDOS = 'posts:mais_curtidos'
CACHE_TTL_MAIS_CURTIDOS = 300
COMMENTS_POR_PAGINA = 10
REACTION_TYPES = [c[0] for c in REACTION_CHOICES]

def _com_reacoes(queryset, user):
    """
    Anota a queryset de posts com contadores de cada tipo de reação
    (like, laugh, wow, sad) e, se o usuário estiver logado, qual
    reação ele deu nesse post (user_reaction), evitando N+1.
    """
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
    return queryset.order_by('-data_posted')


def _get_mais_curtidos_ids():
    """
    Ranking do painel "Mais Curtidos" continua baseado especificamente
    em quem deu reação tipo 'like' (mantém o significado original do
    painel), não na soma de todas as reações.
    """
    ids = cache.get(CACHE_KEY_MAIS_CURTIDOS)
    if ids is None:
        ids = list(
            Post.objects.annotate(
                num_like=Count('reactions', filter=Q(reactions__reaction_type='like'), distinct=True)
            )
            .order_by('-num_like')
            .values_list('id', flat=True)[:10]
        )
        cache.set(CACHE_KEY_MAIS_CURTIDOS, ids, CACHE_TTL_MAIS_CURTIDOS)
    return ids

@login_required(login_url='users:login')
@never_cache
def following_feed(request):
    following_ids = request.user.following_relations.values_list('following_id', flat=True)

    posts_list = _com_reacoes(
        Post.objects.filter(user_id__in=following_ids).select_related('user'), request.user
    )

    paginator = Paginator(posts_list, POSTS_POR_PAGINA)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('partials/posts_feed.html', {'posts': posts, 'user': request.user}, request=request)
        return JsonResponse({
            'html': html,
            'has_next': posts.has_next(),
            'next_page_number': posts.next_page_number() if posts.has_next() else None,
        })

    return render(request, 'following_feed.html', {
        'posts': posts,
        'following_count': len(following_ids),
    })

@never_cache
def all_posts(request):
    posts_list = _com_reacoes(
        Post.objects.select_related('user'), request.user
    )

    paginator = Paginator(posts_list, POSTS_POR_PAGINA)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('partials/posts_feed.html', {'posts': posts, 'user': request.user}, request=request)
        return JsonResponse({
            'html': html,
            'has_next': posts.has_next(),
            'next_page_number': posts.next_page_number() if posts.has_next() else None,
        })

    ids_mais_curtidos = _get_mais_curtidos_ids()
    posts_mais_curtidos = _com_reacoes(
        Post.objects.filter(id__in=ids_mais_curtidos).select_related('user'),
        request.user,
    )
    posts_mais_curtidos = sorted(
        posts_mais_curtidos, key=lambda p: ids_mais_curtidos.index(p.id)
    )

    return render(request, 'all_posts.html', {'posts': posts, 'more_liked_posts': posts_mais_curtidos})

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
        image = request.FILES.get("image")

        post = Post(title=title, content=content, user=request.user)
        if image:
            post.image = image

        try:
            post.full_clean()
        except ValidationError as e:
            errors = e.message_dict.get('image', e.messages)
            return render(request, 'create_post.html', {
                'error': ' '.join(errors) if isinstance(errors, list) else errors,
                'title': title,
                'content': content,
            })

        post.save()
        cache.delete(CACHE_KEY_MAIS_CURTIDOS)
        return redirect("posts:all_posts")

@login_required(login_url='users:login')
@owner_required(Post, pk_url_kwarg='post_id')
@require_POST
def delete_post(request, post_id):
    post = request.owned_object
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

    posts_list = _com_reacoes(posts_list, request.user)

    paginator = Paginator(posts_list, POSTS_POR_PAGINA)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    context = {
        'query': query,
        'posts': posts,
    }
    return render(request, 'search_post.html', context)

def list_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments_qs = post.comments.select_related('user')
    paginator = Paginator(comments_qs, COMMENTS_POR_PAGINA)
    ultima_pagina = paginator.num_pages
    page_obj = paginator.get_page(ultima_pagina)

    html = render_to_string(
        'partials/comments_list.html',
        {
            'comments': page_obj.object_list,
            'post_id': post.id,
            'current_page': ultima_pagina,
            'has_previous': page_obj.has_previous(),
            'user': request.user,
        },
        request=request,
    )
    return JsonResponse({'html': html})

def load_more_comments(request, post_id):
    """
    Carrega uma página anterior (comentários mais antigos) sob demanda,
    usada pelo infinite scroll de dentro da caixa de comentários.
    """
    post = get_object_or_404(Post, id=post_id)
    page = int(request.GET.get('page', 1))

    comments_qs = post.comments.select_related('user')
    paginator = Paginator(comments_qs, COMMENTS_POR_PAGINA)

    if page < 1 or page > paginator.num_pages:
        return JsonResponse({'html': '', 'has_previous': False})

    page_obj = paginator.get_page(page)
    html = render_to_string(
        'partials/comments_items.html',
        {'comments': page_obj.object_list, 'user': request.user},
        request=request,
    )
    return JsonResponse({'html': html, 'has_previous': page_obj.has_previous()})

@login_required(login_url='users:login')
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    content = request.POST.get('content', '').strip()

    if not content:
        return JsonResponse({'error': 'O comentário não pode estar vazio.'}, status=400)
    if len(content) > 500:
        return JsonResponse({'error': 'O comentário não pode ultrapassar 500 caracteres.'}, status=400)

    comment = Comment.objects.create(post=post, user=request.user, content=content)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('partials/comment_item.html', {'comment': comment, 'request': request})
        return JsonResponse({'html': html})

    return redirect(request.META.get('HTTP_REFERER', 'posts:all_posts'))

@login_required(login_url='users:login')
@owner_required(Comment, pk_url_kwarg='comment_id')
@require_POST
def delete_comment(request, comment_id):
    comment = request.owned_object
    comment.delete()
    return JsonResponse({'success': True})

@login_required(login_url='users:login')
@require_POST
def toggle_reaction(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    reaction_type = request.POST.get('reaction_type')

    if reaction_type not in REACTION_TYPES:
        return JsonResponse({'error': 'Tipo de reação inválido.'}, status=400)

    existing = PostReaction.objects.filter(post=post, user=request.user).first()

    if existing and existing.reaction_type == reaction_type:
        existing.delete()
        user_reaction = None
    elif existing:
        existing.reaction_type = reaction_type
        existing.save()
        user_reaction = reaction_type
    else:
        try:
            PostReaction.objects.create(post=post, user=request.user, reaction_type=reaction_type)
            user_reaction = reaction_type
        except IntegrityError:
            # Corrida: outra requisição criou a reação entre o filter() e o create().
            # Em vez de falhar, atualiza a que já existe para o tipo pedido.
            existing = PostReaction.objects.filter(post=post, user=request.user).first()
            if existing:
                existing.reaction_type = reaction_type
                existing.save()
                user_reaction = reaction_type
            else:
                user_reaction = None

    counts = {
        rt: post.reactions.filter(reaction_type=rt).count() for rt in REACTION_TYPES
    }

    if reaction_type == 'like' or user_reaction == 'like':
        cache.delete(CACHE_KEY_MAIS_CURTIDOS)

    return JsonResponse({'user_reaction': user_reaction, 'counts': counts})
