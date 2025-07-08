from django.urls import path
from . import views

blog = 'blog'  # This creates a namespace for the blog app

urlpatterns = [
    path('', views.index, name=''),  # blog/
    path('blog/home/', views.home, name='blog_home'),  # blog/home/
    path('blog/about/', views.about, name='about'),  # blog/about/
    path('blog/posts/', views.posts, name='posts'),  # blog/posts/
]

