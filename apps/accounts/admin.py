from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'height_m', 'current_weight_kg', 'biotype', 'training_frequency_per_week', 'created_at')
    search_fields = ('user__username', 'user__email', 'biotype')
    list_filter = ('biotype', 'training_frequency_per_week')

