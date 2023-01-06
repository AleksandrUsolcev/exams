from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse

from .managers import UserManager


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True
    )
    about = models.TextField(
        verbose_name='Обо мне',
        null=True,
        blank=True,
        max_length=200
    )
    hide_finished_exams = models.BooleanField(
        verbose_name='Скрывать пройденные тесты',
        default=False
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    @property
    def position_of_rankings(self):
        ranks = (
            User.objects
            .filter(is_active=True)
            .with_progress()
            .get_rank()
            .order_by('rank')
            .values_list('id', flat=True)
        )
        return list(ranks).index(self.id) + 1

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def get_absolute_url(self):
        return reverse('users:profile', kwargs={'username': self.username})

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)
