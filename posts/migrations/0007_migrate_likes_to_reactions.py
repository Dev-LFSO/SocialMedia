from django.db import migrations


def copiar_likes_para_reactions(apps, schema_editor):
    Post = apps.get_model('posts', 'Post')
    PostReaction = apps.get_model('posts', 'PostReaction')

    for post in Post.objects.all():
        for user in post.likes.all():
            PostReaction.objects.get_or_create(
                post=post, user=user, defaults={'reaction_type': 'like'}
            )


def reverter(apps, schema_editor):
    PostReaction = apps.get_model('posts', 'PostReaction')
    PostReaction.objects.filter(reaction_type='like').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_postreaction'),  # ajuste pro nome real da migração que criou PostReaction
    ]

    operations = [
        migrations.RunPython(copiar_likes_para_reactions, reverter),
    ]