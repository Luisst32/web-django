from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from .models import Story, StoryView
from users.models import TipoUser

User = get_user_model()

class StoriesTestCase(TestCase):
    def setUp(self):
        # Create TipoUser with id=1 to satisfy custom user default
        self.tipo_user, _ = TipoUser.objects.get_or_create(
            id=1,
            defaults={'tipo_usuario': 'Regular User'}
        )
        
        # Create two test users
        self.user1 = User.objects.create_user(
            username="user1", 
            email="user1@example.com", 
            password="password123", 
            sexo=1,
            tipo_user=self.tipo_user
        )
        self.user2 = User.objects.create_user(
            username="user2", 
            email="user2@example.com", 
            password="password123", 
            sexo=1,
            tipo_user=self.tipo_user
        )
        
        self.client1 = Client()
        self.client1.login(username="user1", password="password123")
        
        self.client2 = Client()
        self.client2.login(username="user2", password="password123")

    def test_crear_story_texto(self):
        response = self.client1.post(reverse('stories:crear_story'), {
            'tipo_historia': 'texto',
            'texto': 'Hola Mundo',
            'color_fondo': '#ff0000'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        self.assertEqual(Story.objects.count(), 1)
        story = Story.objects.first()
        self.assertEqual(story.texto, 'Hola Mundo')
        self.assertEqual(story.usuario, self.user1)
        self.assertEqual(story.color_fondo, '#ff0000')
        self.assertFalse(story.imagen)
        self.assertEqual(story.duracion, 30) # Default duration

    def test_crear_story_con_audio_y_duracion(self):
        # Create story with text, audio_inicio and custom duracion
        response = self.client1.post(reverse('stories:crear_story'), {
            'tipo_historia': 'texto',
            'texto': 'Historia Musical',
            'color_fondo': '#00ff00',
            'audio_inicio': '15',
            'duracion': '45'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        self.assertEqual(Story.objects.count(), 1)
        story = Story.objects.first()
        self.assertEqual(story.texto, 'Historia Musical')
        self.assertEqual(story.audio_inicio, 15)
        self.assertEqual(story.duracion, 45)
        self.assertFalse(story.audio) # empty since no file was uploaded

    def test_crear_story_sin_texto(self):
        response = self.client1.post(reverse('stories:crear_story'), {
            'tipo_historia': 'texto',
            'texto': '',
            'color_fondo': '#ff0000'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertEqual(Story.objects.count(), 0)

    def test_marcar_vista(self):
        story = Story.objects.create(usuario=self.user2, texto="Historia de User 2")
        
        # User 1 views User 2's story
        response = self.client1.post(reverse('stories:marcar_vista', args=[story.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        self.assertTrue(StoryView.objects.filter(story=story, usuario=self.user1).exists())

    def test_eliminar_propia_story(self):
        story = Story.objects.create(usuario=self.user1, texto="Mi propia historia")
        self.assertEqual(Story.objects.count(), 1)
        
        response = self.client1.post(reverse('stories:eliminar_story', args=[story.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(Story.objects.count(), 0)

    def test_eliminar_story_ajena(self):
        story = Story.objects.create(usuario=self.user2, texto="Historia de otro")
        self.assertEqual(Story.objects.count(), 1)
        
        # User 1 tries to delete User 2's story
        response = self.client1.post(reverse('stories:eliminar_story', args=[story.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertEqual(Story.objects.count(), 1)

