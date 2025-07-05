from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    ProfesorViewSet, CursoViewSet, PreguntaViewSet,
    FormularioEvaluacionViewSet, EvaluacionViewSet
)

# Creamos un router para registrar nuestros ViewSets
router = DefaultRouter()
router.register(r'profesores', ProfesorViewSet)
router.register(r'cursos', CursoViewSet)
router.register(r'preguntas', PreguntaViewSet)
router.register(r'formularios-evaluacion', FormularioEvaluacionViewSet)
router.register(r'evaluaciones', EvaluacionViewSet)

urlpatterns = [
    # Incluimos todas las URLs generadas por el router
    path('', include(router.urls)),
]