from ckeditor.widgets import CKEditorWidget
from django import forms
from django.contrib import admin
from django.db import models
from django.forms import Textarea

from .models import Category, Exam, Question, Variant


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


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 60})},
    }


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    readonly_fields = ('active', 'variants_count')
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }
    inlines = (VariantInline,)
    show_change_link = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('variants')

    def variants_count(self, obj):
        return obj.variants.all().count()

    variants_count.short_description = 'Вариантов ответа'


class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'revision',
                    'questions_count', 'active', 'visibility', 'created')
    list_editable = ('visibility',)
    readonly_fields = ('author', 'slug', 'active',
                       'revision', 'questions_count', 'created')

    inlines = (QuestionInline,)
    save_on_top = True
    description = forms.CharField(widget=CKEditorWidget())

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


class QuestionAdmin(admin.ModelAdmin):
    fields = ('exam', 'visibility', 'active', 'priority',
              'type', 'description', 'text', 'success_message')
    list_display = ('text', 'exam', 'priority')
    list_editable = ('priority',)
    raw_id_fields = ('exam',)
    inlines = (VariantInline,)
    save_on_top = True
    readonly_fields = ('active',)


admin.site.register(Category, CategoryAdmin)
admin.site.register(Exam, ExamAdmin)
admin.site.register(Question, QuestionAdmin)
