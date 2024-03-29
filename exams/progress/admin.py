from django.contrib import admin

from .models import Progress, UserSprint


class ProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'exam', 'exam_revision', 'answers_quantity',
                    'current_stage', 'passed', 'started', 'finished')

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def current_stage(self, obj):
        stage = obj.stage
        if obj.finished:
            stage = 'Тест пройден'
        return stage

    current_stage.short_description = 'Этап'


class UserSprintAdmin(admin.ModelAdmin):
    list_display = ('user', 'sprint', 'started', 'finished')

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(Progress, ProgressAdmin)
admin.site.register(UserSprint, UserSprintAdmin)
