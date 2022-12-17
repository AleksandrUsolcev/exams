from django.contrib import admin

from .models import Progress, Question, Quiz, QuizTheme, Variant


class QuizThemeAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'priority')
    readonly_fields = ('slug',)
    list_editable = ('priority',)


class QuestionInline(admin.StackedInline):
    model = Question
    show_change_link = True
    extra = 0


class VariantInline(admin.TabularInline):
    model = Variant
    show_change_link = True
    extra = 0


class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'theme', 'author', 'revision', 'created')
    readonly_fields = ('slug', 'revision')
    raw_id_fields = ('author',)
    inlines = (QuestionInline,)

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'author', None) is None:
            obj.author = request.user
        obj.save()


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'priority')
    list_editable = ('priority',)
    raw_id_fields = ('quiz',)
    inlines = (VariantInline,)


class VariantAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'correct', 'priority')
    list_editable = ('correct', 'priority')
    raw_id_fields = ('question',)


class ProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'stage', 'answers', 'passed')

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(QuizTheme, QuizThemeAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Variant, VariantAdmin)
admin.site.register(Progress, ProgressAdmin)
