from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    last_seen = models.DateTimeField(default=timezone.now)

    def is_online(self):
        if self.last_seen:
            return self.last_seen > timezone.now() - datetime.timedelta(minutes=5)
        return False

    def __str__(self):
        return f"Profil de {self.user.username}"


class Statut(models.Model):
    TYPE_CHOICES = [
        ('text', 'Texte'),
        ('image', 'Image'),
        ('video', 'Vidéo'),
        ('audio', 'Audio'),
        ('poll', 'Sondage'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='statuts')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='text')
    contenu = models.TextField(blank=True, null=True)
    image = models.FileField(upload_to='status_pics/', blank=True, null=True)
    audio = models.FileField(upload_to='status_audio/', blank=True, null=True)
    date_pub = models.DateTimeField(auto_now_add=True)
    date_expire = models.DateTimeField(blank=True, null=True)
    likes = models.ManyToManyField(User, related_name='statut_likes', blank=True)
    views = models.ManyToManyField(User, related_name='statut_views', blank=True)

    def save(self, *args, **kwargs):
        if not self.date_expire:
            self.date_expire = timezone.now() + datetime.timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.date_expire

    def total_likes(self):
        return self.likes.count()

    def total_views(self):
        return self.views.count()

    class Meta:
        ordering = ['-date_pub']

    def __str__(self):
        return f"{self.user.username} - {self.get_type_display()} - {self.date_pub.strftime('%d/%m/%Y %H:%M')}"


class SondageOption(models.Model):
    statut = models.ForeignKey(Statut, on_delete=models.CASCADE, related_name='options')
    texte = models.CharField(max_length=100)
    votes = models.ManyToManyField(User, related_name='votes_sondage', blank=True)

    def total_votes(self):
        return self.votes.count()

    def __str__(self):
        return f"{self.texte} - {self.total_votes()} votes"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_pics/', blank=True, null=True)
    file = models.FileField(upload_to='chat_docs/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_delivered = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"De {self.sender.username} à {self.receiver.username}"


class PinnedChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pinned_chats')
    pinned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pinned_by')
    pinned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'pinned_user')
        ordering = ['-pinned_at']

    def __str__(self):
        return f"{self.user.username} a épinglé {self.pinned_user.username}"