from django.contrib import admin

from .models import Answer, Question, Quiz


class QuizAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'created')


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'queue')
    list_editable = ('queue',)


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'correct')
    list_editable = ('correct',)


admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
