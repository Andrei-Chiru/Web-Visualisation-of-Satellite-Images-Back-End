from django.contrib import admin
from django.urls import path, include, re_path
from api.views import CreateUserView, tile_serving, serve_image  # import serve_image here
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/register/', CreateUserView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='get_token'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path ('api-auth/', include('rest_framework.urls')),
    path ('api/', include('api.urls')),
    path('map/', serve_image, name='serve_image'),
    re_path(r'^tiles/(?P<path>.*)$', tile_serving, name='tile_serving'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Serve files from MEDIA_ROOT
