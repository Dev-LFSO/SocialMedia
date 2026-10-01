from functools import wraps
from django.shortcuts import get_object_or_404


def owner_required(model, pk_url_kwarg, owner_field='user'):
    """
    Decorator genérico que garante que o objeto buscado pertence ao
    usuário logado. Se não pertencer (ou não existir), retorna 404 —
    não revela se o objeto existe pra outros usuários.

    Uso:
        @login_required
        @owner_required(Post, pk_url_kwarg='post_id')
        def edit_post(request, post_id):
            post = request.owned_object
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            pk = kwargs.get(pk_url_kwarg)
            filtro = {'id': pk, owner_field: request.user}
            obj = get_object_or_404(model, **filtro)
            request.owned_object = obj
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator