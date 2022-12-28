from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, ExpressionWrapper, F, IntegerField, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from questions.models import Progress

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
        latest_progress = Progress.objects.filter(
            user=self.object, exam_revision=F('exam__revision')
        ).select_related('exam').annotate(
            questions_count=Count(
                'exam__questions', filter=(
                    Q(exam__questions__visibility=True) &
                    Q(exam__questions__active=True)
                )
            ),
            percentage=ExpressionWrapper(
                F('answers_count') * 100 / Count(
                    'exam__questions', filter=(
                        Q(exam__questions__visibility=True) &
                        Q(exam__questions__active=True)
                    )
                ),
                output_field=IntegerField()
            ),
            percentage_passed=ExpressionWrapper(
                F('passed') * 100 / F('answers_count'),
                output_field=IntegerField()
            )
        ).order_by('-started')
        extra_context = {
            'latest_progress': latest_progress[:6],
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
