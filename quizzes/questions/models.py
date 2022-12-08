from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Quiz(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=200
    )
    description = models.TextField(
        verbose_name='Краткое описание'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='quizzes',
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(
        verbose_name='Дата добавления',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Квиз'
        verbose_name_plural = 'Квизы'
        ordering = ['-created']

    def __str__(self):
        return f'{self.name}'


class Question(models.Model):
    text = models.TextField(
        verbose_name='Вопрос'
    )
    queue = models.PositiveIntegerField(
        verbose_name='Очередность',
        default=0
    )
    quiz = models.ForeignKey(
        Quiz,
        verbose_name='Квиз',
        related_name='questions',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        if len(self.text) > 48:
            return f'{self.text[:48]}...'
        return f'{self.text}'


class Answer(models.Model):
    text = models.TextField(
        verbose_name='Текст варианта ответа'
    )
    correct = models.BooleanField(
        verbose_name='Верный ответ',
        default=False
    )
    question = models.ForeignKey(
        Question,
        verbose_name='Вопрос',
        related_name='answers',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'

    def __str__(self):
        if len(self.text) > 48:
            return f'{self.text[:48]}...'
        return f'{self.text}'
