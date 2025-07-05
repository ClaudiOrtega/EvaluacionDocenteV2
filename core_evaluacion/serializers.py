from rest_framework import serializers
from .models import Profesor, Curso, Pregunta, FormularioEvaluacion, Evaluacion, Respuesta
from django.contrib.auth.models import User

# Serializador para el modelo User de Django (para mostrar información del usuario)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['username'] # Generalmente el username no se cambia por API de perfil


class ProfesorSerializer(serializers.ModelSerializer):
    # Usamos UserSerializer para mostrar los detalles del usuario asociado
    usuario = UserSerializer(read_only=True)
    # Si quisieras crear/actualizar un profesor y también su usuario:
    # usuario_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='usuario', write_only=True)

    class Meta:
        model = Profesor
        fields = '__all__' # Incluye todos los campos del modelo Profesor

class CursoSerializer(serializers.ModelSerializer):
    # Muestra los detalles del profesor asociado
    profesor = ProfesorSerializer(read_only=True)
    # Si el frontend solo enviara el ID del profesor:
    # profesor_id = serializers.PrimaryKeyRelatedField(queryset=Profesor.objects.all(), source='profesor', write_only=True)

    class Meta:
        model = Curso
        fields = '__all__'

class PreguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pregunta
        fields = '__all__'

class FormularioEvaluacionSerializer(serializers.ModelSerializer):
    # Mostrar las preguntas anidadas en el formulario
    preguntas = PreguntaSerializer(many=True, read_only=True)

    class Meta:
        model = FormularioEvaluacion
        fields = '__all__'


class RespuestaSerializer(serializers.ModelSerializer):
    # Muestra los detalles de la pregunta asociada
    pregunta = PreguntaSerializer(read_only=True)
    # Permite al frontend enviar el ID de la pregunta al crear una respuesta
    pregunta_id = serializers.PrimaryKeyRelatedField(queryset=Pregunta.objects.all(), source='pregunta', write_only=True)

    class Meta:
        model = Respuesta
        fields = '__all__'
        # Excluye 'evaluacion' ya que se manejara en el serializador padre (EvaluacionSerializer)
        extra_kwargs = {'evaluacion': {'read_only': True}}


class EvaluacionSerializer(serializers.ModelSerializer):
    # Muestra los detalles de estudiante, profesor, curso y formulario
    estudiante = UserSerializer(read_only=True)
    profesor = ProfesorSerializer(read_only=True)
    curso = CursoSerializer(read_only=True)
    formulario_evaluacion = FormularioEvaluacionSerializer(read_only=True)

    # Permite la escritura de los IDs al crear una evaluación
    profesor_id = serializers.PrimaryKeyRelatedField(queryset=Profesor.objects.all(), source='profesor', write_only=True)
    curso_id = serializers.PrimaryKeyRelatedField(queryset=Curso.objects.all(), source='curso', write_only=True)
    formulario_evaluacion_id = serializers.PrimaryKeyRelatedField(queryset=FormularioEvaluacion.objects.all(), source='formulario_evaluacion', write_only=True)

    # Permite crear/actualizar respuestas anidadas dentro de la evaluación
    respuestas = RespuestaSerializer(many=True) # `many=True` porque una evaluación tiene muchas respuestas

    class Meta:
        model = Evaluacion
        fields = '__all__'
        read_only_fields = ['estudiante', 'fecha_envio'] # El estudiante se asigna automaticamente en la vista

    # Este metodo es crucial para manejar la creación anidada de Evaluacion y sus Respuestas
    def create(self, validated_data):
        # Extrae las respuestas de los datos validados antes de crear la evaluación
        respuestas_data = validated_data.pop('respuestas')

        # Crea la instancia de la evaluacion
        evaluacion = Evaluacion.objects.create(**validated_data)

        # Crea las respuestas y las asocia a la evaluación recién creada
        for respuesta_data in respuestas_data:
            # Asegúrate de pasar la instancia de la pregunta, no solo el ID
            pregunta = respuesta_data.pop('pregunta')
            Respuesta.objects.create(evaluacion=evaluacion, pregunta=pregunta, **respuesta_data)

        return evaluacion
