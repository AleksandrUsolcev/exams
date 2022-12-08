from django.contrib import admin

from .models import Question, Quiz, QuizTheme, Variant


class QuizThemeAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'priority')
    list_editable = ('priority',)


class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'theme', 'author', 'created')


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'priority')
    list_editable = ('priority',)


class VariantAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'correct', 'priority')
    list_editable = ('correct', 'priority')


admin.site.register(QuizTheme, QuizThemeAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Variant, VariantAdmin)
