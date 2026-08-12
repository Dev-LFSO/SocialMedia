from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Post
from django.http import JsonResponse


# Create your views here.
@login_required(login_url='users:login')
def all_posts(request):
    posts = Post.objects.all()
    more_liked_posts = Post.objects.all().order_by('-likes')[0:4]
    return render(request, 'all_posts.html', {'posts': posts, 'more_liked_posts':more_liked_posts})

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