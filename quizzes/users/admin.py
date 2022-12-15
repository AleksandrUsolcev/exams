from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email')
    ordering = ('id',)


admin.site.register(User, CustomUserAdmin)
