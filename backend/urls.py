from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from myapp.api.views import CreateUserView
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("myapp/user/registration/", CreateUserView.as_view(), name="register"),
    path("myapp/token/", TokenObtainPairView.as_view(), name="get_token"),
    path("myapp/token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("myapp-auth/", include("rest_framework.urls")),
    path("myapp/", include("myapp.api.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
