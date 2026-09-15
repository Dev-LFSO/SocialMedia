from django.shortcuts import render
from datetime import datetime
from decouple import config
from django_ratelimit.exceptions import Ratelimited
import requests

# Create your views here.
def home(request):
    key = config('NEWS_API_KEY')
    url = 'https://newsapi.org/v2/top-headlines?country=us&apiKey=' + key
    news_list = requests.get(url).json()

    news_list = list(filter(lambda x: x['urlToImage'] is not None, news_list['articles']))

    for news in news_list:
        news['publishedAt'] = datetime.strptime(news['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%H:%M - %d/%m/%y')

    news_list = news_list[0:12]

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