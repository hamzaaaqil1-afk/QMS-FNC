"""
URL configuration for erp_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from qms.auth_views import get_csrf, login_view, logout_view, me_view
from qms.user_views import (
    liste_utilisateurs, creer_utilisateur,
    modifier_utilisateur, toggle_actif, liste_groupes
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Auth
    path('api/auth/csrf/',   get_csrf,     name='csrf'),
    path('api/auth/login/',  login_view,   name='login'),
    path('api/auth/logout/', logout_view,  name='logout'),
    path('api/auth/me/',     me_view,      name='me'),
    # Utilisateurs
    path('api/users/',                    liste_utilisateurs,  name='users-list'),
    path('api/users/create/',             creer_utilisateur,   name='users-create'),
    path('api/users/<int:user_id>/',      modifier_utilisateur,name='users-update'),
    path('api/users/<int:user_id>/toggle/',toggle_actif,       name='users-toggle'),
    path('api/groups/',                   liste_groupes,       name='groups-list'),
    # Modules
    path('api/qms/', include('qms.urls')),
    path('api/risks/', include('risks.urls')),
    path('api/crm/', include('crm.urls')),
    path('api/hrm/', include('hrm.urls')),
    path('api/achats/', include('achats.urls')),
    path('api/finance/', include('finance.urls')),
    path('api/mes/', include('mes.urls')),
    path('api/tenants/', include('tenants.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)