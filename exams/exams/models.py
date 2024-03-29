from random import randrange

from ckeditor_uploader.fields import RichTextUploadingField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from slugify import slugify
from users.models import User

from . import managers


class Category(models.Model):
    title = models.CharField(
        verbose_name='Название',
        max_length=200
    )
    slug = models.SlugField(
        unique=True,
        max_length=340,
        verbose_name='ЧПУ'
    )
    description = models.TextField(
        verbose_name='Краткое описание',
        max_length=300
    )
    show_empty = models.BooleanField(
        verbose_name='Отображать если нет тестов',
        default=True
    )
    priority = models.PositiveIntegerField(
        verbose_name='Приоритет',
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(99)
        ]
    )

    objects = managers.CategoryManager()

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['priority', 'title']

    def __str__(self):
        return f'{self.title}'

    def save(self, *args, **kwargs):
        if self._state.adding:
            code = randrange(10000, 99999)
        else:
            code = self.slug[-5:]
        self.slug = slugify(self.title) + '-' + str(code)
        super().save(*args, **kwargs)


class Sprint(models.Model):
    title = models.CharField(
        verbose_name='Название',
        max_length=200
    )
    slug = models.SlugField(
        unique=True,
        editable=False,
        max_length=340,
        verbose_name='ЧПУ'
    )
    description = models.TextField(
        verbose_name='Краткое описание',
        null=True,
        blank=True,
        max_length=600
    )
    any_order = models.BooleanField(
        verbose_name='Разрешается решать тесты в произвольном порядке',
        default=True
    )
    created = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True
    )

    objects = managers.SprintManager()

    class Meta:
        verbose_name = 'Спринт'
        verbose_name_plural = 'Спринты'
        ordering = ['-created']

    def __str__(self):
        return f'{self.title}'

    def save(self, *args, **kwargs):
        if self._state.adding:
            code = randrange(10000, 99999)
        else:
            code = self.slug[-5:]
        self.slug = slugify(self.title) + '-' + str(code)
        super().save(*args, **kwargs)


class Exam(models.Model):
    revision = models.DateTimeField(
        verbose_name='Редакция',
        null=True,
        blank=True,
        editable=False
    )
    title = models.CharField(
        verbose_name='Название',
        max_length=200
    )
    success_message = models.TextField(
        verbose_name='Сообщение после прохождения теста',
        help_text='Не обязательно к заполнению',
        blank=True,
        null=True
    )
    slug = models.SlugField(
        unique=True,
        max_length=340,
        verbose_name='ЧПУ'
    )
    description = RichTextUploadingField(
        verbose_name='Описание'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='exams',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        related_name='exams',
        null=True,
        on_delete=models.SET_NULL,
        db_index=True
    )
    sprint = models.ForeignKey(
        Sprint,
        verbose_name='Спринт',
        related_name='exams',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_index=True
    )
    created = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True
    )
    timer = models.PositiveIntegerField(
        verbose_name='Время на выполнение (мин.)',
        help_text='Необязательное поле',
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(720)
        ]
    )
    required_percent = models.PositiveIntegerField(
        verbose_name='Процент верных ответов для успешного прохождения',
        help_text=('Необязательное поле. По умолчанию прохождение будет '
                   'успешным при любом проценте'),
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100)
        ]
    )
    allow_retesting = models.BooleanField(
        verbose_name='Разрешить повторное прохождение',
        default=True
    )
    show_results = models.BooleanField(
        verbose_name=('Отображать пользователю результат после каждого ответа '
                      'и по окончанию тестирования'),
        default=True
    )
    only_guest_keys = models.BooleanField(
        verbose_name=('Доступ для гостей к результатам только по '
                      'ссылке-приглашению'),
        help_text='При условии, что пользователю отображается результат',
        default=True
    )
    show_correct = models.BooleanField(
        verbose_name='Отображать пользователю верные варианты ответов',
        help_text=('Только если активен параметр с отображением '
                   'пользователю результатов'),
        default=True
    )
    shuffle_variants = models.BooleanField(
        verbose_name='Перемешивать варианты ответов, игнорируя приоритет',
        default=True
    )
    empty_answers = models.BooleanField(
        verbose_name='Разрешить оставлять выбор пустым',
        help_text='Только для типов вопросов с несколькими вариантами ответов',
        default=False
    )
    priority = models.PositiveIntegerField(
        verbose_name='Приоритет',
        help_text=('Влияет на порядок выдачи теста, '
                   'если он относится к спринту'),
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(99)
        ]
    )
    active = models.BooleanField(
        verbose_name='Готов к публикации',
        help_text=('Статус принимает положительное состояние, если есть '
                   'хотя бы один не скрытый/готовый к публикации вопрос'),
        default=False
    )
    visibility = models.BooleanField(
        verbose_name='Опубликован',
        default=False
    )

    objects = managers.ExamManager()

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'
        ordering = ['-created']

    def __str__(self):
        return f'{self.title}'

    def save(self, *args, **kwargs):
        if self._state.adding:
            code = randrange(10000, 99999)
        else:
            code = self.slug[-5:]
            if self.active and self.visibility:
                self.revision = timezone.now()
        self.slug = slugify(self.title) + '-' + str(code)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('exams:exam_detail', kwargs={'slug': self.slug})


class Question(models.Model):

    ONE_CORRECT = 'one_correct'
    MANY_CORRECT = 'many_correct'
    TEXT_ANSWER = 'text_answer'

    TYPES = (
        (ONE_CORRECT, 'Допустим только один правильный ответ'),
        (MANY_CORRECT, 'Допустимы несколько вариантов ответов'),
        (TEXT_ANSWER, 'Текстовый ответ')
    )
    description = RichTextUploadingField(
        verbose_name='Подробное описание/информация',
        blank=True,
        null=True
    )
    text = models.TextField(
        verbose_name='Вопрос'
    )
    success_message = models.TextField(
        verbose_name='Сообщение после ответа',
        help_text=('Не обязательно к заполнению, выводится в том случае, '
                   'если опция отображения результата активна'),
        blank=True,
        null=True
    )
    priority = models.PositiveIntegerField(
        verbose_name='Приоритет',
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(99)
        ]
    )
    exam = models.ForeignKey(
        Exam,
        verbose_name='Тестирование',
        related_name='questions',
        on_delete=models.CASCADE,
        db_index=True
    )
    type = models.CharField(
        verbose_name='Тип',
        choices=TYPES,
        max_length=32,
        default='one_correct'
    )
    active = models.BooleanField(
        verbose_name='Готов к публикации',
        help_text=('Статус принимает положительное состояние, если '
                   'есть хотя бы один вариант ответа, соответствующий '
                   'настройками вопроса и теста'),
        default=False
    )
    visibility = models.BooleanField(
        verbose_name='Опубликован',
        default=False
    )

    @property
    def one_correct(self):
        return self.type == self.ONE_CORRECT

    @property
    def many_correct(self):
        return self.type == self.MANY_CORRECT

    @property
    def text_answer(self):
        return self.type == self.TEXT_ANSWER

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['-visibility', '-active', 'priority', 'id']

    def __str__(self):
        if len(self.text) > 48:
            return f'{self.text[:48]}...'
        return f'{self.text}'


class Variant(models.Model):
    text = models.TextField(
        verbose_name='Текст варианта ответа'
    )
    priority = models.PositiveIntegerField(
        verbose_name='Приоритет',
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(99)
        ]
    )
    correct = models.BooleanField(
        verbose_name='Верный ответ',
        default=False
    )
    question = models.ForeignKey(
        Question,
        verbose_name='Вопрос',
        related_name='variants',
        on_delete=models.CASCADE,
        db_index=True
    )

    @property
    def exam(self):
        return self.question.exam

    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'
        ordering = ['priority', 'id', 'text']

    def __str__(self):
        if len(self.text) > 48:
            return f'{self.text[:48]}...'
        return f'{self.text}'
