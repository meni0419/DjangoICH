from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import Post, Category

# Create custom admin site for blog
class BlogAdminSite(AdminSite):
    site_header = 'Blog Administration'
    site_title = 'Blog Admin'
    index_title = 'Welcome to Blog Administration'

# Create instance of custom admin site
blog_admin_site = BlogAdminSite(name='blog_admin')

# Register models with custom admin site
@admin.register(Post, site=blog_admin_site)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Category, site=blog_admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

# Also register with default admin (optional)
admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)