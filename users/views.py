from django.conf import settings
from django.utils import timezone
from django.views.generic import detail
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .serializers import RegisterSerializer


def set_token_cookies(response: Response, access: str = None, refresh: str = None):
    cfg = settings.AUTH_COOKIES
    if access:
        response.set_cookie(
            key=cfg['ACCESS']['NAME'],
            value=access,
            max_age=cfg['ACCESS']['MAX_AGE'],
            path=cfg['ACCESS']['PATH'],
            secure=cfg['ACCESS']['SECURE'],
            httponly=cfg['ACCESS']['HTTPONLY'],
            samesite=cfg['ACCESS']['SAMESITE'],
        )

    if refresh:
        response.set_cookie(
            key=cfg['REFRESH']['NAME'],
            value=refresh,
            max_age=cfg['REFRESH']['MAX_AGE'],
            path=cfg['REFRESH']['PATH'],
            secure=cfg['REFRESH']['SECURE'],
            httponly=cfg['REFRESH']['HTTPONLY'],
            samesite=cfg['REFRESH']['SAMESITE'],
        )


def clear_token_cookies(response: Response):
    cfg = settings.AUTH_COOKIES
    response.delete_cookie(cfg['ACCESS']['NAME'], path=cfg['ACCESS']['PATH'])
    response.delete_cookie(cfg['REFRESH']['NAME'], path=cfg['REFRESH']['PATH'])


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"detail": "User registered successfully."},
            status=status.HTTP_201_CREATED
        )


class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        data = response.data
        access = data.get('access')
        refresh = data.get('refresh')
        resp = Response({"detail": "Login successful."}, status=status.HTTP_200_OK)
        set_token_cookies(resp, access=access, refresh=refresh)
        return resp


class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        cfg = settings.AUTH_COOKIES
        refresh_cookie = request.COOKIES.get(cfg['REFRESH']['NAME'])
        data = request.data.copy()
        if not data.get('refresh') and refresh_cookie:
            data['refresh'] = refresh_cookie

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        access = serializer.validated_data.get('access')
        refresh = serializer.validated_data.get('refresh')
        resp = Response({"detail": "Token refreshed successfully."}, status=status.HTTP_200_OK)
        set_token_cookies(resp, access=access)
        if refresh:
            set_token_cookies(resp, refresh=refresh)
        return resp


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cfg = settings.AUTH_COOKIES
        refresh_cookie = request.COOKIES.get(cfg['REFRESH']['NAME'])

        if refresh_cookie:
            try:
                token = RefreshToken(refresh_cookie)
                token.blacklist()
            except TokenError:
                pass

        resp = Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)
        clear_token_cookies(resp)
        return resp
