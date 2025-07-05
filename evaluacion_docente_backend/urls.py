from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core_evaluacion.urls')), # Incluimos las URLs de nuestra app core_evaluacion
    path('api-auth/', include('rest_framework.urls')), # URLs para el login/logout del DRF (opcional para browsable API)
]