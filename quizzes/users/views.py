from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView

from .forms import SignupForm


class SignupView(CreateView):
    form_class = SignupForm
    success_url = reverse_lazy('questions:index')
    template_name = 'users/signup.html'


class UserProfileView(DetailView):
    pass
