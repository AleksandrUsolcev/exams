from django import forms


class QuizProcessForm(forms.Form):
    name = forms.CharField(max_length=100, label='Имя')
