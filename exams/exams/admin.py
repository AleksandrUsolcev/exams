from ckeditor.widgets import CKEditorWidget
from django import forms
from django.contrib import admin
from django.db import models
from django.forms import Textarea
from nested_admin.nested import (NestedModelAdmin, NestedStackedInline,
                                 NestedTabularInline)
from progress.models import Progress, UserSprint

from .models import Category, Exam, Question, Sprint, Variant


@admin.action(description='Удалить связанный прогресс')
def delete_exam_progress(modeladmin, request, queryset):
    Progress.objects.filter(exam__in=queryset).delete()


@admin.action(description='Удалить связанный прогресс')
def delete_sprint_progress(modeladmin, request, queryset):
    UserSprint.objects.filter(sprint__in=queryset).delete()


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'exams_count', 'priority')
    list_editable = ('priority',)
    readonly_fields = ('slug', 'exams_count',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('exams')

    def exams_count(self, obj):
        return obj.exams.filter(visibility=True, active=True).count()

    exams_count.short_description = 'Тестирований'


class ExamInline(NestedStackedInline):
    model = Exam
    show_change_link = True
    extra = 0
    fieldsets = (
        ('', {
            'fields': ('title', 'visibility', 'priority', 'category', 'active')
        }),
    )
    readonly_fields = ('title', 'category', 'active')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('category').order_by('priority', 'id')

    def has_add_permission(self, request, obj=None):
        return False


class SprintAdmin(NestedModelAdmin):
    list_display = ('title', 'exams_count', 'created')
    inlines = (ExamInline,)
    save_on_top = True
    readonly_fields = ('created', 'slug')
    actions = [delete_sprint_progress]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('exams')

    def exams_count(self, obj):
        return obj.exams.all().count()

    exams_count.short_description = 'Тестов'


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
    raw_id_fields = ('sprint',)
    description = forms.CharField(widget=CKEditorWidget())
    actions = [delete_exam_progress]

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


admin.site.register(Category, CategoryAdmin)
admin.site.register(Sprint, SprintAdmin)
admin.site.register(Exam, ExamAdmin)
