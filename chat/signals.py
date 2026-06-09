from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.apps import apps  # <--- On utilise 'apps' pour éviter le conflit

# Ce "capteur" crée un profil dès qu'un utilisateur est créé
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        # On récupère le modèle dynamiquement
        ProfileModel = apps.get_model('accounts', 'Profile')
        ProfileModel.objects.get_or_create(user=instance)

# Ce "capteur" sauvegarde le profil quand l'utilisateur est mis à jour
@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    # On vérifie si le profil existe avant de sauvegarder pour éviter les erreurs
    if hasattr(instance, 'profile'):
        instance.profile.save()