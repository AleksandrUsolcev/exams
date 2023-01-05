from random import randrange

from ckeditor.fields import RichTextField
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from slugify import slugify

from . import managers

User = get_user_model()


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
        verbose_name='Краткое описание'
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


class Exam(models.Model):
    revision = models.PositiveIntegerField(
        verbose_name='Редакция',
        help_text=('Меняется автоматически при изменении/удалении вопросов '
                   'и вариантов ответов, если тест готов к публикации и не '
                   'скрыт'),
        default=0,
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
    description = RichTextField(
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
    created = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True
    )
    change_revision = models.BooleanField(
        verbose_name=('Менять версию редакции при сохранении теста, вопросов '
                      'или вариантов ответов'),
        default=False
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
    show_results = models.BooleanField(
        verbose_name=('Отображать пользователю результат после каждого ответа '
                      'и по окончанию тестирования'),
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
    active = models.BooleanField(
        verbose_name='Готов к публикации',
        help_text=('Статус принимает положительное состояние, если есть '
                   'хотя бы один не скрытый/готовый к публикации вопрос'),
        default=False)
    visibility = models.BooleanField(
        verbose_name='Опубликован',
        default=False
    )

    objects = managers.ExamManager()

    class Meta:
        verbose_name = 'Тестирование'
        verbose_name_plural = 'Тестирования'
        ordering = ['-created']

    def __str__(self):
        return f'{self.title}'

    def save(self, *args, **kwargs):
        if self._state.adding:
            code = randrange(10000, 99999)
        else:
            code = self.slug[-5:]
            if self.active and self.visibility and self.change_revision:
                self.revision += 1
        self.slug = slugify(self.title) + '-' + str(code)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('questions:exam_detail', kwargs={'slug': self.slug})


class Question(models.Model):

    ONE_CORRECT = 'one_correct'
    MANY_CORRECT = 'many_correct'

    TYPES = (
        (ONE_CORRECT, 'Допустим только один правильный ответ'),
        (MANY_CORRECT, 'Допустимы несколько вариантов ответов')
    )

    text = RichTextField(
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
        default='many_correct'
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

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['-visibility', '-active', 'priority', 'id', 'text']

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


class Progress(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='progression',
        on_delete=models.CASCADE
    )
    exam = models.ForeignKey(
        Exam,
        verbose_name='Тестирование',
        related_name='progress',
        on_delete=models.CASCADE
    )
    exam_revision = models.PositiveIntegerField(
        verbose_name='Редакция тестирования',
        null=True,
    )
    exam_title = models.CharField(
        verbose_name='Заголовок тестирования',
        max_length=200,
        null=True
    )
    stage = models.PositiveIntegerField(
        verbose_name='Этап',
        default=1
    )
    answers_quantity = models.PositiveIntegerField(
        verbose_name='Ответов',
        default=0
    )
    started = models.DateTimeField(
        verbose_name='Дата начала',
        null=True
    )
    finished = models.DateTimeField(
        verbose_name='Дата завершения',
        null=True
    )
    passed = models.BooleanField(
        verbose_name='Зачтено',
        null=True
    )

    objects = managers.ProgressManager()

    class Meta:
        verbose_name = 'Прогресс пользователя'
        verbose_name_plural = 'Прогресс пользователей'

    def __str__(self):
        return f'{self.user} stage in {self.exam_title} ({self.stage})'

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.started = timezone.now()
        super().save(*args, **kwargs)


class UserAnswer(models.Model):
    progress = models.ForeignKey(
        Progress,
        verbose_name='Прогресс',
        related_name='answers',
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question,
        verbose_name='Вопрос',
        related_name='answers',
        null=True,
        on_delete=models.SET_NULL
    )
    question_text = models.TextField(
        verbose_name='Текст вопроса',
        null=True
    )
    correct = models.BooleanField(
        verbose_name='Результат',
        null=True,
    )
    no_answers = models.BooleanField(
        verbose_name='Без ответов',
        null=True,
    )
    date = models.DateTimeField(
        verbose_name='Дата ответа',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Ответ пользователя'
        verbose_name_plural = 'Ответы пользователей'
        ordering = ['date']


class UserVariant(models.Model):
    answer = models.ForeignKey(
        UserAnswer,
        verbose_name='Ответ',
        related_name='variants',
        on_delete=models.CASCADE
    )
    variant = models.ForeignKey(
        Variant,
        verbose_name='Ответ',
        related_name='answers',
        null=True,
        on_delete=models.SET_NULL
    )
    variant_text = models.TextField(
        verbose_name='Вариант ответа',
        null=True
    )
    selected = models.BooleanField(
        verbose_name='Выбран пользователем',
        default=False
    )
    correct = models.BooleanField(
        verbose_name='Ответ верен',
        default=False
    )

    class Meta:
        verbose_name = 'Вариант ответа пользователя'
        verbose_name_plural = 'Варианты ответов пользователей'
        ordering = ['-correct', '-selected']

    def __str__(self):
        return f'{self.variant_text}'
