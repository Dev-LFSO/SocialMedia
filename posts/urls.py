from django.urls import path
from .views import all_posts, like_post, create_post, delete_post, search_post, goto_post

app_name = 'posts'

urlpatterns = [
    path('', all_posts, name='all_posts'),
    path('<int:post_id>/', like_post, name='like_post'),
    path('create_post', create_post, name='create_post'),
    path('delete_post/<int:post_id>', delete_post, name='delete_post'),
    path('search_post', search_post, name='search_post'),
    path('goto/<int:post_id>/', goto_post, name='goto_post'),
]