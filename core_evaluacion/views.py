from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Avg, Count
from django.db.models.functions import Coalesce

from rest_framework import serializers # <--- Asegúrate de que esta línea esté presente y sea así.

from .models import Profesor, Curso, Pregunta, FormularioEvaluacion, Evaluacion, Respuesta
from .serializers import (
    ProfesorSerializer, CursoSerializer, PreguntaSerializer,
    FormularioEvaluacionSerializer, EvaluacionSerializer, RespuestaSerializer,
    UserSerializer
)
from django.contrib.auth.models import User

# Permisos personalizados (ejemplo)
class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permite acceso de escritura solo a administradores, lectura para todos.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS: # GET, HEAD, OPTIONS
            return True
        return request.user and request.user.is_staff # Solo si es un usuario administrador

class IsStudentOrAdmin(permissions.BasePermission):
    """
    Permite acceso completo a estudiantes (para sus propias evaluaciones) y a administradores.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff: # Admins pueden hacer cualquier cosa
            return True
        # Para GET, PUT, DELETE sobre una evaluación específica, el estudiante debe ser el propietario
        return obj.estudiante == request.user

    def has_permission(self, request, view):
        # POST (crear evaluación) y GET (listar evaluaciones)
        return request.user and request.user.is_authenticated # Todos los autenticados pueden ver/crear


class ProfesorViewSet(viewsets.ModelViewSet):
    queryset = Profesor.objects.all()
    serializer_class = ProfesorSerializer
    # Permiso: los administradores pueden editar, los usuarios autenticados pueden ver
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def promedio_calificacion(self, request, pk=None):
        """
        Calcula el promedio de calificaciones de un profesor específico.
        """
        profesor = self.get_object()
        # Calcula el promedio de todas las respuestas de calificacion dadas al profesor
        # Coalesce(Avg(...), 0.0) asegura que si no hay calificaciones, el resultado sea 0.0 en lugar de None
        avg_rating = profesor.evaluaciones_recibidas.aggregate(
            avg_calificacion=Coalesce(Avg('respuestas__respuesta_calificacion'), 0.0)
        )['avg_calificacion']
        return Response({'profesor_id': pk, 'promedio_calificacion': round(avg_rating, 2)})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def estadisticas_generales(self, request):
        """
        Muestra estadísticas generales de todos los profesores (solo para admin).
        """
        estadisticas = Profesor.objects.annotate(
            num_evaluaciones=Count('evaluaciones_recibidas', distinct=True),
            promedio_general=Coalesce(Avg('evaluaciones_recibidas__respuestas__respuesta_calificacion'), 0.0)
        ).values('id', 'usuario__first_name', 'usuario__last_name', 'num_evaluaciones', 'promedio_general')
        return Response(list(estadisticas))


class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    permission_classes = [IsAdminOrReadOnly]


class PreguntaViewSet(viewsets.ModelViewSet):
    queryset = Pregunta.objects.all()
    serializer_class = PreguntaSerializer
    permission_classes = [permissions.IsAdminUser] # Solo administradores pueden crear/editar preguntas


class FormularioEvaluacionViewSet(viewsets.ModelViewSet):
    queryset = FormularioEvaluacion.objects.filter(esta_activo=True) # Por defecto, solo formularios activos
    serializer_class = FormularioEvaluacionSerializer
    # Permite a cualquier usuario autenticado ver formularios activos, admin puede crear/editar/desactivar
    permission_classes = [IsAdminOrReadOnly]

    # Un endpoint para que los usuarios (estudiantes) puedan ver que formularios están disponibles
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def disponibles(self, request):
        """
        Lista solo los formularios de evaluación que están activos y disponibles.
        """
        disponibles = self.get_queryset().filter(esta_activo=True)
        serializer = self.get_serializer(disponibles, many=True)
        return Response(serializer.data)


class EvaluacionViewSet(viewsets.ModelViewSet):
    queryset = Evaluacion.objects.all()
    serializer_class = EvaluacionSerializer
    permission_classes = [IsStudentOrAdmin] # Ver clase de permiso personalizada

    def get_queryset(self):
        """
        Permite a los estudiantes ver solo sus propias evaluaciones,
        los administradores pueden ver todas.
        """
        user = self.request.user
        if user.is_staff: # Si es admin, ve todas
            return Evaluacion.objects.all()
        # Si es un usuario regular, ve solo sus propias evaluaciones
        return Evaluacion.objects.filter(estudiante=user)

    def perform_create(self, serializer):
        """
        Asigna automáticamente el estudiante a la evaluación con el usuario autenticado.
        """
        # Verifica si el estudiante ya evaluo a este profesor/curso/formulario
        estudiante = self.request.user
        profesor = serializer.validated_data['profesor']
        curso = serializer.validated_data['curso']
        formulario_evaluacion = serializer.validated_data['formulario_evaluacion']

        if Evaluacion.objects.filter(
            estudiante=estudiante,
            profesor=profesor,
            curso=curso,
            formulario_evaluacion=formulario_evaluacion
        ).exists():
            raise serializers.ValidationError("Ya has enviado una evaluación para este profesor y curso con este formulario.")

        serializer.save(estudiante=estudiante)

    @action(detail=False, methods=['get'])
    def mis_evaluaciones(self, request):
        """
        Endpoint para que un estudiante vea solo las evaluaciones que ha enviado.
        """
        # El get_queryset ya filtra por el usuario si no es admin.
        # No necesitamos un filtro adicional aqui a menos que quieras una logica diferente.
        # Aqui simplemente devolvemos lo que ya filtraria get_queryset.
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def resultados_detallados(self, request, pk=None):
        """
        Muestra los resultados detallados de una evaluación específica (solo para admin).
        """
        evaluacion = self.get_object()
        serializer = EvaluacionSerializer(evaluacion) # Reutilizamos el serializador principal
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def reportes_generales(self, request):
        """
        Genera reportes generales de evaluaciones (solo para admin).
        Podrías expandir esto para generar PDFs, CSVs, etc.
        """
        # Ejemplo: Contar cuantas evaluaciones ha recibido cada profesor
        reporte_profesores = Profesor.objects.annotate(
            total_evaluaciones=Count('evaluaciones_recibidas', distinct=True)
        ).values('usuario__first_name', 'usuario__last_name', 'total_evaluaciones')

        # Ejemplo: Promedio de calificacion por curso
        reporte_cursos = Curso.objects.annotate(
            promedio_calificacion_curso=Coalesce(Avg('evaluaciones_curso__respuestas__respuesta_calificacion'), 0.0),
            total_evaluaciones_curso=Count('evaluaciones_curso', distinct=True)
        ).values('nombre', 'codigo', 'promedio_calificacion_curso', 'total_evaluaciones_curso')

        return Response({
            'reporte_profesores': list(reporte_profesores),
            'reporte_cursos': list(reporte_cursos)
        })