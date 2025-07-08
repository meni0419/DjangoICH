from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.models import User


def index(request):
    superuser = User.objects.filter(is_superuser=True).first()
    return HttpResponse(f"Hello, {superuser.username if superuser else 'No superuser found'}")


def home(request):
    return render(request, 'blog/home.html')

def about(request):
    return HttpResponse("Blog Posts - Coming Soon!")

def posts(request):
    return HttpResponse("Blog Posts - Coming Soon!")
