from django.contrib import admin
from django.db import models
from django.forms import Textarea
from nested_admin.nested import (NestedModelAdmin, NestedStackedInline,
                                 NestedTabularInline)

from .models import Category, Exam, Progress, Question, Variant


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'exams_count', 'priority')
    list_editable = ('priority',)
    readonly_fields = ('slug', 'exams_count',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('exams')

    def exams_count(self, obj):
        return obj.exams.filter(visibility=False, active=False).count()

    exams_count.short_description = 'Тестирований'


class VariantInline(NestedTabularInline):
    model = Variant
    extra = 1
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 60})},
    }


class QuestionInline(NestedStackedInline):
    model = Question
    show_change_link = True
    extra = 1
    readonly_fields = ('active', 'variants_count')
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }
    inlines = (VariantInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('variants')

    def variants_count(self, obj):
        return obj.variants.all().count()

    variants_count.short_description = 'Вариантов ответа'


class ExamAdmin(NestedModelAdmin):
    list_display = ('title', 'category', 'author', 'revision',
                    'questions_count', 'active', 'visibility', 'created')
    list_editable = ('visibility',)
    readonly_fields = ('author', 'slug', 'active',
                       'revision', 'questions_count', 'created')

    inlines = (QuestionInline,)
    save_on_top = True
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
    }

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('questions').prefetch_related(
            'category', 'author',)

    def questions_count(self, obj):
        return obj.questions.all().count()

    questions_count.short_description = 'Вопросов'

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'author', None) is None:
            obj.author = request.user
        obj.save()


class ProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'exam', 'exam_revision', 'answers_count',
                    'current_stage', 'passed', 'started', 'finished')

    def has_change_permission(self, request, obj=None):
        return False

    def current_stage(self, obj):
        stage = obj.stage
        if obj.finished:
            stage = 'Тест пройден'
        return stage

    current_stage.short_description = 'Этап'


admin.site.register(Category, CategoryAdmin)
admin.site.register(Exam, ExamAdmin)
admin.site.register(Progress, ProgressAdmin)
