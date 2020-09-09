from django.urls import include
from django.conf.urls import url, re_path
from authentication import routes as user_routes
from core import routes as core_routes
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView

urlpatterns = [
    url(r'^auth/', include(user_routes)),
    url(r'^api/', include(core_routes)),
    re_path('^.*$', TemplateView.as_view(template_name="index.html")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
