from django.contrib.auth.forms import UserCreationForm
from django.forms import ValidationError

from .models import User


class SignupForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = ('email', 'username')

    def clean(self):
        email = self.cleaned_data.get('email').lower()
        username = self.cleaned_data.get('username')
        if User.objects.filter(email=email):
            raise ValidationError('Указанный email уже занят')
        if User.objects.filter(username__iexact=username):
            raise ValidationError('Пользователь с такими ником уже существует')
        return self.cleaned_data
