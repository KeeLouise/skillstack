"""
URL configuration for skillstack project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path("users/", include(("users.urls", "users"), namespace="users")),
    path('projects/', include('projects.urls')),
    path('messaging/', include('messaging.urls')),
    path("portfolio/", include(("portfolio.urls", "portfolio"), namespace="portfolio")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Error handlers defined to avoid circular imports - KR 16/08/2025
from django.template.loader import select_template

def error_400(request, exception):
    tpl = select_template(["errors/400.html", "400.html"])
    return HttpResponseBadRequest(tpl.render({}, request))

def error_403(request, exception):
    tpl = select_template(["errors/403.html", "403.html", "403_csrf.html"])
    return HttpResponseForbidden(tpl.render({}, request))

def error_404(request, exception):
    tpl = select_template(["errors/404.html", "404.html"])
    return HttpResponseNotFound(tpl.render({}, request))

def error_500(request):
    tpl = select_template(["errors/500.html", "500.html"])
    return HttpResponseServerError(tpl.render({}, request))

handler400 = "skillstack.urls.error_400"
handler403 = "skillstack.urls.error_403"
handler404 = "skillstack.urls.error_404"
handler500 = "skillstack.urls.error_500"