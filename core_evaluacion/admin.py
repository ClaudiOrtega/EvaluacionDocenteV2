from django.contrib import admin
from .models import Profesor, Curso, Pregunta, FormularioEvaluacion, Evaluacion, Respuesta

@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'id_empleado', 'departamento')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'id_empleado', 'departamento')
    list_filter = ('departamento',)
    raw_id_fields = ('usuario',) # Para buscar usuarios por ID si hay muchos

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'profesor')
    search_fields = ('nombre', 'codigo', 'profesor__usuario__username')
    list_filter = ('profesor__departamento',)
    raw_id_fields = ('profesor',)

@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('texto', 'tipo_pregunta')
    search_fields = ('texto',)
    list_filter = ('tipo_pregunta',)

@admin.register(FormularioEvaluacion)
class FormularioEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'esta_activo', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion')
    list_filter = ('esta_activo',)
    filter_horizontal = ('preguntas',) # Facilita la selección de muchas preguntas

class RespuestaInline(admin.TabularInline):
    model = Respuesta
    extra = 1 # Muestra un campo extra para añadir una nueva respuesta al editar una evaluación
    fields = ('pregunta', 'respuesta_texto', 'respuesta_calificacion', 'respuesta_booleana', 'respuesta_seleccion', 'respuesta_multiples_selecciones')
    raw_id_fields = ('pregunta',) # Para buscar preguntas por ID

@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'profesor', 'curso', 'formulario_evaluacion', 'fecha_envio')
    search_fields = ('estudiante__username', 'profesor__usuario__username', 'curso__nombre', 'formulario_evaluacion__titulo')
    list_filter = ('profesor', 'curso', 'formulario_evaluacion', 'fecha_envio')
    raw_id_fields = ('estudiante', 'profesor', 'curso', 'formulario_evaluacion')
    inlines = [RespuestaInline] # Permite gestionar las respuestas directamente desde la evaluación