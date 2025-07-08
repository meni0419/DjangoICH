from django.urls import path
from . import views
from .admin import blog_admin_site

app_name = 'blog'  # This creates a namespace for the blog app

urlpatterns = [
    path('', views.index, name=''),  # blog/
    path('home/', views.home, name='blog_home'),  # blog/home/
    path('about/', views.about, name='about'),  # blog/about/
    path('posts/', views.posts, name='posts'),  # blog/posts/
    path('admin/', blog_admin_site.urls), # blog/admin/
]

