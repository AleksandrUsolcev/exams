from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from exams.models import Exam

from .forms import SignupForm
from .models import User


class SignupView(CreateView):
    form_class = SignupForm
    success_url = reverse_lazy('exams:index')
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

    def get_object(self, *args, **kwargs):
        user = (
            User.objects
            .filter(username=self.kwargs.get('username'))
            .only(
                'username', 'date_joined', 'about', 'first_name', 'last_name'
            )
            .with_progress()
        )
        return get_object_or_404(user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exams = (
            Exam.objects
            .select_related('category')
            .list_(user=self.object, only_user=True)
            .order_by('-started')
        )
        extra_context = {
            'exams': exams[:6],
            'progress_url': True
        }
        context.update(extra_context)
        return context


class UserEditView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'hide_finished_exams',
              'hide_finished_sprints', 'about']
    template_name = 'users/profile_edit.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_object(self, *args, **kwargs):
        return self.request.user


class RankingListView(ListView):
    model = User
    template_name = 'users/rankings.html'
    context_object_name = 'users'
    paginate_by = 50

    def get_queryset(self):
        queryset = (
            User.objects
            .filter(is_active=True)
            .with_progress()
            .get_rank()
            .only(
                'username', 'date_joined', 'about', 'first_name', 'last_name'
            )
            .order_by('rank')
        )
        return queryset
