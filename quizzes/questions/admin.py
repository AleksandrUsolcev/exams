from django.contrib import admin

from .models import Progress, Question, Quiz, QuizTheme, Variant


class QuizThemeAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'quizzes_count', 'priority')
    list_editable = ('priority',)
    readonly_fields = ('slug', 'quizzes_count',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('quizzes')

    def quizzes_count(self, obj):
        return obj.quizzes.filter(visibility=False, active=False).count()

    quizzes_count.short_description = 'Квизов'


class QuestionInline(admin.StackedInline):
    model = Question
    show_change_link = True
    extra = 0
    readonly_fields = ('active', 'variants_count')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('variants')

    def variants_count(self, obj):
        return obj.variants.all().count()

    variants_count.short_description = 'Вариантов ответа'


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 0


class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'theme', 'author',
                    'revision', 'questions_count', 'visibility', 'created')
    list_editable = ('visibility',)
    readonly_fields = ('author', 'slug', 'active',
                       'revision', 'questions_count')
    inlines = (QuestionInline,)
    save_on_top = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('questions').prefetch_related(
            'theme', 'author')

    def questions_count(self, obj):
        return obj.questions.all().count()

    questions_count.short_description = 'Вопросов'

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'author', None) is None:
            obj.author = request.user
        obj.save()


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'priority')
    list_editable = ('priority',)
    raw_id_fields = ('quiz',)
    inlines = (VariantInline,)
    save_on_top = True
    readonly_fields = ('active',)


class ProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'stage', 'answers', 'passed')

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(QuizTheme, QuizThemeAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Progress, ProgressAdmin)
