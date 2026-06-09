from django.contrib import admin
from .models import Statut, Message

# --- CONFIGURATION DES MESSAGES ---
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    # On affiche les colonnes importantes, y compris tes nouvelles coches
    list_display = ('sender', 'receiver', 'timestamp', 'is_delivered', 'is_read')
    list_filter = ('is_read', 'is_delivered', 'timestamp', 'sender')
    search_fields = ('content', 'sender__username', 'receiver__username')
    readonly_fields = ('timestamp',) # On ne peut pas modifier l'heure d'un message

    # Organisation par blocs dans la fiche du message
    fieldsets = (
        ('Expédition', {
            'fields': ('sender', 'receiver')
        }),
        ('Contenu', {
            'fields': ('content', 'image', 'file')
        }),
        ('État de distribution', {
            'fields': ('is_delivered', 'is_read', 'timestamp')
        }),
    )

# --- CONFIGURATION DES STATUTS (ACTUS) ---
@admin.register(Statut)
class StatutAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_pub', 'get_likes_count')
    list_filter = ('date_pub', 'user')
    search_fields = ('contenu', 'user__username')

    def get_likes_count(self, obj):
        return obj.total_likes()
    get_likes_count.short_description = 'Nombre de Likes'