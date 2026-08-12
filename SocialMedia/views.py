from django.shortcuts import render
from datetime import datetime
import requests


# Create your views here.

def home(request):
    key = '3c0ca70b24484989b06d9d6a3d12958d'
    url = 'https://newsapi.org/v2/top-headlines?country=us&apiKey='+key
    news_list = requests.get(url).json()

    news_list = list(filter(lambda x: x['urlToImage'] is not None, news_list['articles']))

    for news in news_list:
        news['publishedAt'] = datetime.strptime(news['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%H:%M - %d/%m/%y')

    news_list = news_list[0:12]

    return render(request, 'home.html' , {'news_list':news_list})

