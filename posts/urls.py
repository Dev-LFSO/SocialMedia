from django.urls import path
from .views import (
    all_posts, like_post, create_post, delete_post, search_post, goto_post,
    list_comments, add_comment, delete_comment, load_more_comments, following_feed,
)

app_name = 'posts'

urlpatterns = [
    path('', all_posts, name='all_posts'),
    path('<int:post_id>/', like_post, name='like_post'),
    path('following/', following_feed, name='following_feed'),
    path('create_post', create_post, name='create_post'),
    path('delete_post/<int:post_id>', delete_post, name='delete_post'),
    path('search_post', search_post, name='search_post'),
    path('goto/<int:post_id>/', goto_post, name='goto_post'),
    path('<int:post_id>/comments/', list_comments, name='list_comments'),
    path('<int:post_id>/comments/load_more/', load_more_comments, name='load_more_comments'),
    path('<int:post_id>/comments/add/', add_comment, name='add_comment'),
    path('comments/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
]