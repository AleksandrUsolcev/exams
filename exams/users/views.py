from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from questions.models import Exam, UserAnswer

from .forms import SignupForm
from .models import User


class SignupView(CreateView):
    form_class = SignupForm
    success_url = reverse_lazy('questions:index')
    template_name = 'users/signup.html'

    def form_valid(self, form):
        valid = super().form_valid(form)
        login(self.request, self.object)
        return valid


class UserProfileView(DetailView):
    model = User
    template_name = 'users/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unique_passed = Exam.objects.prefetch_related('answers').filter(
            answers__user=self.object,
        ).distinct().count()
        answers = UserAnswer.objects.filter(user=self.object)
        try:
            correct_percentage = int(
                (answers.filter(correct=True).count() / answers.count()) * 100)
        except ZeroDivisionError:
            correct_percentage = 0
        extra_context = {
            'unique_passed': unique_passed,
            'correct_percentage': correct_percentage
        }
        context.update(extra_context)
        return context


class UserEditView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'about']
    template_name = 'users/profile_edit.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_object(self, *args, **kwargs):
        return self.request.user
