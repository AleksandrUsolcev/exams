from random import randrange

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from slugify import slugify

User = get_user_model()


class QuizTheme(models.Model):
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
    priority = models.PositiveIntegerField(
        verbose_name='Приоритет',
        default=99,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(99)
        ]
    )

    class Meta:
        verbose_name = 'Тематика квизов'
        verbose_name_plural = 'Тематики квизов'
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


class Quiz(models.Model):
    revision = models.PositiveIntegerField(
        verbose_name='Редакция квиза',
        help_text=('Меняется автоматически при изменении/удалении вопросов'
                   ' и вариантов ответов'),
        default=1,
        editable=False
    )
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
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='quizzes',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    theme = models.ForeignKey(
        QuizTheme,
        verbose_name='Тематика',
        related_name='quizzes',
        null=True,
        on_delete=models.SET_NULL
    )
    created = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True
    )
    show_results = models.BooleanField(
        verbose_name='Отображать пользователю подробные результаты',
        default=True
    )
    shuffle_variants = models.BooleanField(
        verbose_name='Перемешивать варианты ответов, игнорируя приоритет',
        default=True
    )
    empty_answers = models.BooleanField(
        verbose_name='Разрешить оставлять выбор пустым',
        default=False
    )

    class Meta:
        verbose_name = 'Квиз'
        verbose_name_plural = 'Квизы'
        ordering = ['-created']

    def __str__(self):
        return f'{self.title}'

    def save(self, *args, **kwargs):
        if self._state.adding:
            code = randrange(10000, 99999)
        else:
            code = self.slug[-5:]
            self.revision += 1
            progress = Progress.objects.filter(quiz=self.pk)
            if progress.exists():
                progress.delete()
        self.slug = slugify(self.title) + '-' + str(code)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        progress = Progress.objects.filter(quiz=self.pk)
        if progress.exists():
            progress.delete()
        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('questions:quiz_detail', kwargs={'slug': self.slug})


class Question(models.Model):

    ONE_CORRECT = 'one_correct'
    MANY_CORRECT = 'many_correct'

    TYPES = (
        (ONE_CORRECT, 'Допустим только один правильный ответ'),
        (MANY_CORRECT, 'Допустимы несколько вариантов ответов')
    )

    text = models.TextField(
        verbose_name='Вопрос'
    )
    priority = models.PositiveIntegerField(
        verbose_name='Приоритет',
        default=99,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(99)
        ]
    )
    quiz = models.ForeignKey(
        Quiz,
        verbose_name='Квиз',
        related_name='questions',
        on_delete=models.CASCADE
    )
    type = models.CharField(
        verbose_name='Тип',
        choices=TYPES,
        max_length=32,
        default='many_correct'
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
        ordering = ['priority', 'id', 'text']

    def __str__(self):
        if len(self.text) > 48:
            return f'{self.text[:48]}...'
        return f'{self.text}'

    def delete(self, *args, **kwargs):
        new_version = self.quiz.revision + 1
        progress = Progress.objects.filter(quiz=self.quiz)
        if progress.exists():
            progress.delete()
        Quiz.objects.filter(id=self.quiz.id).update(revision=new_version)
        super().delete(*args, **kwargs)


class Variant(models.Model):
    text = models.TextField(
        verbose_name='Текст варианта ответа'
    )
    priority = models.PositiveIntegerField(
        verbose_name='Приоритет',
        default=99,
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
        on_delete=models.CASCADE
    )

    @property
    def quiz(self):
        return self.question.quiz

    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'
        ordering = ['priority', 'id', 'text']

    def __str__(self):
        if len(self.text) > 48:
            return f'{self.text[:48]}...'
        return f'{self.text}'

    def delete(self, *args, **kwargs):
        new_version = self.question.quiz.revision + 1
        progress = Progress.objects.filter(quiz=self.question.quiz)
        if progress.exists():
            progress.delete()
        Quiz.objects.filter(id=self.question.quiz.id).update(
            revision=new_version
        )
        super().delete(*args, **kwargs)


class UserAnswer(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='answers',
        on_delete=models.CASCADE
    )
    quiz = models.ForeignKey(
        Quiz,
        verbose_name='Квиз',
        related_name='answers',
        on_delete=models.CASCADE
    )
    quiz_revision = models.PositiveIntegerField(
        verbose_name='Редакция квиза',
        null=True,
    )
    quiz_title = models.CharField(
        verbose_name='Заголовок квиза',
        max_length=200,
        null=True
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
        ordering = ['-date']

    def __str__(self):
        return f'{self.user} answer {self.question}'


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
    correct = models.BooleanField(
        verbose_name='Результат'
    )

    class Meta:
        verbose_name = 'Вариант ответа пользователя'
        verbose_name_plural = 'Варианты ответов пользователей'

    def __str__(self):
        return f'{self.variant_text}'


class Progress(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='progression',
        on_delete=models.CASCADE
    )
    quiz = models.ForeignKey(
        Quiz,
        verbose_name='Квиз',
        related_name='progress',
        on_delete=models.CASCADE
    )
    stage = models.PositiveIntegerField(
        verbose_name='Этап',
        default=1
    )
    answers = models.PositiveIntegerField(
        verbose_name='Ответов',
        default=0
    )
    passed = models.DateTimeField(
        verbose_name='Дата завершения',
        null=True
    )

    class Meta:
        verbose_name = 'Прогресс пользователя'
        verbose_name_plural = 'Прогресс пользователей'

    def __str__(self):
        return f'{self.user.id} stage in {self.quiz.id} ({self.stage})'


@receiver(post_save, sender=Variant)
@receiver(post_save, sender=Question)
def update_revision(sender, instance, **kwargs):
    new_version = instance.quiz.revision + 1
    progress = Progress.objects.filter(quiz=instance.quiz)
    if progress.exists():
        progress.delete()
    Quiz.objects.filter(id=instance.quiz.id).update(revision=new_version)
