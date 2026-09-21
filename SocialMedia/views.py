from django.shortcuts import render
from datetime import datetime
from django.core.paginator import Paginator
from decouple import config
from django.core.cache import cache
from django_ratelimit.exceptions import Ratelimited
import requests

NOTICIAS_POR_PAGINA = 12
CACHE_KEY_NOTICIAS = 'home:noticias'
CACHE_TTL_NOTICIAS = 10 * 60

def _buscar_noticias():
    """
    Busca um lote grande de notícias da NewsAPI, filtra as que têm imagem
    e formata a data. O resultado fica em cache por alguns minutos pra
    não bater na API a cada troca de página nem a cada usuário.
    """
    noticias = cache.get(CACHE_KEY_NOTICIAS)
    if noticias is not None:
        return noticias

    key = config('NEWS_API_KEY')
    url = f'https://newsapi.org/v2/top-headlines?country=us&pageSize=100&apiKey={key}'

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
    except requests.RequestException:
        return []

    artigos = data.get('articles', [])
    noticias = [a for a in artigos if a.get('urlToImage')]

    for noticia in noticias:
        try:
            noticia['publishedAt'] = datetime.strptime(
                noticia['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'
            ).strftime('%H:%M - %d/%m/%y')
        except (ValueError, KeyError):
            noticia['publishedAt'] = ''

    cache.set(CACHE_KEY_NOTICIAS, noticias, CACHE_TTL_NOTICIAS)
    return noticias


def home(request):
    noticias = _buscar_noticias()

    paginator = Paginator(noticias, NOTICIAS_POR_PAGINA)
    page_number = request.GET.get('page')
    news_list = paginator.get_page(page_number)

    return render(request, 'home.html', {'news_list': news_list})

def custom_403_view(request, exception=None):
    """
    Handler global de 403. Se a causa foi rate limit, mostra
    a página amigável de "muitas tentativas"; senão, 403 genérico.
    """
    if isinstance(exception, Ratelimited):
        return render(request, 'ratelimited.html', status=429)
    return render(request, '403.html', status=403)

def custom_500_view(request, exception=None):
    return render(request, '500.html', status=500)