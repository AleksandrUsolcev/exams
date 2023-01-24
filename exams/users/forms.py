import re

from django.contrib.auth.forms import UserCreationForm
from django.forms import ValidationError

from .models import User


class SignupForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = ('email', 'username')

    def clean(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if User.objects.filter(email__iexact=email):
            raise ValidationError('Указанный email уже занят')
        if not re.match("^[A-Za-z0-9]*$", username):
            raise ValidationError('Имя не соответствует требованиям '
                                  '(только латиница и цифры)')
        if User.objects.filter(username__iexact=username):
            raise ValidationError('Пользователь с такими ником уже существует')
        return self.cleaned_data
