from uuid import uuid4

from django.db import models
from users.models import User

from exams.models import Exam, Question, Sprint, Variant

from . import managers


class UserSprint(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='sprints',
        on_delete=models.CASCADE
    )
    sprint = models.ForeignKey(
        Sprint,
        verbose_name='Спринт',
        related_name='progress',
        on_delete=models.CASCADE
    )
    started = models.DateTimeField(
        verbose_name='Дата начала',
        auto_now_add=True
    )
    finished = models.DateTimeField(
        verbose_name='Дата завершения',
        null=True
    )

    class Meta:
        verbose_name = 'Пройденный спринт'
        verbose_name_plural = 'Пройденные спринты'


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
    exam_revision = models.DateTimeField(
        verbose_name='Редакция тестирования',
        null=True,
        blank=True
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
        auto_now_add=True
    )
    finished = models.DateTimeField(
        verbose_name='Дата завершения',
        null=True
    )
    passed = models.BooleanField(
        verbose_name='Зачтено',
        null=True
    )
    guest_key = models.CharField(
        verbose_name='Гостевой ключ',
        null=True,
        blank=True,
        editable=False,
        max_length=100
    )

    objects = managers.ProgressManager()

    class Meta:
        verbose_name = 'Прогресс пользователя'
        verbose_name_plural = 'Прогресс пользователей'

    def __str__(self):
        return f'{self.user} in exam: {self.exam_id} (stage: {self.stage})'

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.guest_key = str(uuid4())
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

    objects = managers.UserAnswerManager()

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
