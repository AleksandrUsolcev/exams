from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from progress.models import Progress, UserSprint

from .models import User


@admin.action(description='Удалить связанный прогресс')
def delete_progress(modeladmin, request, queryset):
    Progress.objects.filter(user__in=queryset).delete()
    UserSprint.objects.filter(user__in=queryset).delete()


class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email')
    ordering = ('id',)
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': (
        'hide_finished_exams', 'about',
    )}),)
    actions = [delete_progress]


admin.site.register(User, CustomUserAdmin)
