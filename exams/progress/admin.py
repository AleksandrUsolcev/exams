from django.contrib import admin

from .models import Progress


class ProgressAdmin(admin.ModelAdmin):

    def has_change_permission(self, request, obj=None):
        return False

    def current_stage(self, obj):
        stage = obj.stage
        if obj.finished:
            stage = 'Тест пройден'
        return stage

    current_stage.short_description = 'Этап'


admin.site.register(Progress, ProgressAdmin)
