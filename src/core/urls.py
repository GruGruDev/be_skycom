"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include
from django.urls import path
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView


class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http"] if int(os.environ.get("DEBUG", default=0)) else ["https"]
        return schema


schema_view = get_schema_view(
    openapi.Info(
        title="Skycom API",
        default_version="v1",
        description="Skycom API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="noreply@gmail.com"),
        license=openapi.License(name="BSD License"),
        x_logo={"url": "https://skycom.netlify.app/images/logo.jpg"},
    ),
    generator_class=BothHttpAndHttpsSchemaGenerator,
    public=True,
    permission_classes=[permissions.AllowAny],
)


def home(request):
    return JsonResponse(
        {
            "DEBUG": os.environ.get("DEBUG"),
            "Allow host": os.environ.get("DJANGO_ALLOWED_HOSTS"),
            "CI_COMMIT_SHORT_SHA": os.environ.get("CI_COMMIT_SHA"),
            "CI_COMMIT_TIMESTAMP": os.environ.get("CI_COMMIT_TIMESTAMP"),
        }
    )


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("docs/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/cdp/", include("customers.api.urls")),
    path("api/users/", include("users.api.urls")),
    path("api/locations/", include("locations.api.urls")),
    path("api/products/", include("products.api.urls")),
    path("api/promotions/", include("promotions.api.urls")),
    path("api/warehouses/", include("warehouses.api.urls")),
    path("api/orders/", include("orders.api.urls")),
    path("api/files/", include("files.api.urls")),
]


# pylint: disable=W0612
def trigger_error(request):
    division_by_zero = 1 / 0  # noqa


urlpatterns += [
    path("sentry-debug/", trigger_error),
]
