from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from questions.models import Exam, Progress, UserAnswer, UserVariant

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
        exams = (
            Exam.objects
            .select_related('category')
            .list_(user=self.object, only_user=True)
        )
        extra_context = {
            'exams': exams[:6]
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


class UserProgressDetailView(DetailView):
    model = Progress
    template_name = 'users/progress_detail.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_queryset(self):
        progress_id = self.kwargs.get('pk')
        queryset = Progress.objects.get_details(
            progress_id=progress_id, variants=UserVariant, answers=UserAnswer
        )
        return queryset
