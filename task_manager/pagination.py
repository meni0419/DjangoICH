from rest_framework.pagination import CursorPagination

class GlobalCursorPagination(CursorPagination):
    page_size = 5
    ordering = '-created_at'
    page_size_query_param = None
