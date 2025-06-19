from django.db import models
from django.conf import settings

# Modelo para los Tweets
class Tweet(models.Model):
    contenido = models.TextField(blank=False)  # Contenido del tweet
    futbolista = models.CharField(max_length=255)  # Nombre del futbolista relacionado
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)  # Autor del tweet
    foto = models.URLField(blank=True, null=True)  # URL de la foto (opcional)
    create_at = models.DateTimeField(auto_now_add=True)  # Fecha de creación

    def __str__(self):
        return self.contenido[:50]  # Mostrar solo los primeros 50 caracteres del tweet en la lista


# Opciones de reacciones posibles para los tweets
REACTION_CHOICES = [
    ('like', 'Like'),
    ('love', 'Love'),
    ('angry', 'Angry'),
    ('sad', 'Sad'),
    ('goat', 'Goat')   
]


# Modelo para las reacciones a los tweets (como likes, enoja, etc.)
class Reaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Usuario que reacciona
    tweet = models.ForeignKey(Tweet, related_name='reactions', on_delete=models.CASCADE)  # Tweet al que se reacciona
    reaction_type = models.CharField(max_length=50, choices=REACTION_CHOICES)  # Tipo de reacción (like, me enoja, etc.)

    def __str__(self):
        return f"Reaction by {self.user.username} on tweet {self.tweet.id} - {self.reaction_type}"


# Modelo para los comentarios en los tweets
class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Usuario que comenta
    tweet = models.ForeignKey(Tweet, related_name='comments', on_delete=models.CASCADE)  # Tweet comentado
    text = models.TextField()  # Texto del comentario
    created_at = models.DateTimeField(auto_now_add=True)  # Fecha de creación del comentario

    def __str__(self):
        return f"Comment by {self.user.username} on tweet {self.tweet.id}"
