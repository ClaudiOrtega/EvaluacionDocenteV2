from django.db import models
from django.contrib.auth.models import User # Django's built-in User model

class Profesor(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_profesor', verbose_name='Usuario Asociado')
    id_empleado = models.CharField(max_length=20, unique=True, verbose_name='ID Empleado')
    departamento = models.CharField(max_length=100, verbose_name='Departamento')

    class Meta:
        verbose_name = "Profesor"
        verbose_name_plural = "Profesores"
        ordering = ['usuario__last_name', 'usuario__first_name']

    def __str__(self):
        full_name = self.usuario.get_full_name()
        return full_name if full_name else self.usuario.username

class Curso(models.Model):
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Curso')
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código del Curso')
    profesor = models.ForeignKey(Profesor, on_delete=models.SET_NULL, null=True, blank=True, related_name='cursos_impartidos', verbose_name='Profesor Asignado')

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

class Pregunta(models.Model):
    TIPOS_PREGUNTA = [
        ('texto', 'Entrada de Texto Libre'),
        ('calificacion', 'Escala de Calificación (1-5)'), # O (1-10) según prefieras
        ('seleccion_unica', 'Selección Única'),
        ('seleccion_multiple', 'Selección Múltiple'),
        ('booleano', 'Sí/No o Verdadero/Falso'),
    ]
    texto = models.TextField(verbose_name='Texto de la Pregunta')
    tipo_pregunta = models.CharField(max_length=20, choices=TIPOS_PREGUNTA, verbose_name='Tipo de Pregunta')

    class Meta:
        verbose_name = "Pregunta"
        verbose_name_plural = "Preguntas"
        ordering = ['id']

    def __str__(self):
        return self.texto[:70] + "..." if len(self.texto) > 70 else self.texto

class FormularioEvaluacion(models.Model):
    titulo = models.CharField(max_length=200, verbose_name='Título del Formulario')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    preguntas = models.ManyToManyField(Pregunta, related_name='formularios_asociados', verbose_name='Preguntas del Formulario')
    esta_activo = models.BooleanField(default=True, verbose_name='¿Está Activo?')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')

    class Meta:
        verbose_name = "Formulario de Evaluación"
        verbose_name_plural = "Formularios de Evaluación"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.titulo

class Evaluacion(models.Model):
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluaciones_dadas', verbose_name='Estudiante')
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, related_name='evaluaciones_recibidas', verbose_name='Profesor Evaluado')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='evaluaciones_curso', verbose_name='Curso Evaluado')
    formulario_evaluacion = models.ForeignKey(FormularioEvaluacion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Formulario Usado')
    fecha_envio = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Envío')

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        # Esto previene que un mismo estudiante evalúe al mismo profesor en el mismo curso con el mismo formulario más de una vez
        unique_together = ('estudiante', 'profesor', 'curso', 'formulario_evaluacion')
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"Evaluación de {self.profesor} por {self.estudiante.username} para {self.curso.nombre}"

class Respuesta(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='respuestas', verbose_name='Evaluación')
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, verbose_name='Pregunta')

    # Campos para diferentes tipos de respuestas
    respuesta_texto = models.TextField(blank=True, null=True, verbose_name='Respuesta de Texto')
    respuesta_calificacion = models.IntegerField(blank=True, null=True, verbose_name='Respuesta de Calificación') # Ej: 1 a 5
    respuesta_booleana = models.BooleanField(blank=True, null=True, verbose_name='Respuesta Booleana')
    # Para selección unica/multiple, podrías guardar el valor seleccionado o una lista de valores
    respuesta_seleccion = models.CharField(max_length=255, blank=True, null=True, verbose_name='Respuesta de Selección') # Si es única
    respuesta_multiples_selecciones = models.JSONField(blank=True, null=True, verbose_name='Respuestas de Múltiple Selección') # Si es múltiple

    class Meta:
        verbose_name = "Respuesta"
        verbose_name_plural = "Respuestas"
        # Una pregunta solo puede tener una respuesta por evaluación
        unique_together = ('evaluacion', 'pregunta')
        ordering = ['pregunta__id']

    def __str__(self):
        content = ""
        if self.respuesta_texto:
            content = self.respuesta_texto[:30]
        elif self.respuesta_calificacion is not None:
            content = str(self.respuesta_calificacion)
        elif self.respuesta_booleana is not None:
            content = "Sí" if self.respuesta_booleana else "No"
        elif self.respuesta_seleccion:
            content = self.respuesta_seleccion
        elif self.respuesta_multiples_selecciones:
            content = ", ".join(self.respuesta_multiples_selecciones)
        return f"Respuesta a '{self.pregunta.texto[:50]}...' de {self.evaluacion.estudiante.username}: {content}"