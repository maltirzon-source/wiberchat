from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    # Le lien unique vers l'utilisateur
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # On utilise 'image' au lieu d'avatar pour la compatibilité avec tes vues
    image = models.ImageField(default='default.jpg', upload_to="profile_pics/", null=True, blank=True)

    # Informations complémentaires
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    # Utile pour afficher "En ligne" ou "Vu à..." dans Wiberchat
    last_seen = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Profil de {self.user.username}"

    # Fonction pour savoir si l'utilisateur est actuellement en ligne (activité < 5 min)
    def is_online(self):
        if self.last_seen:
            return (timezone.now() - self.last_seen).total_seconds() < 300
        return False
