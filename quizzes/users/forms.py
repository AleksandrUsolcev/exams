from django.contrib.auth.forms import UserCreationForm
from django.forms import ValidationError

from .models import User


class SignupForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = ('email', 'username')

    def clean(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email):
            raise ValidationError('Указанный email уже занят')
        return self.cleaned_data
