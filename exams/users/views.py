from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (Count, ExpressionWrapper, F, IntegerField,
                              Prefetch, Q)
from django.db.models.functions.comparison import NullIf
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from questions.models import Progress, UserAnswer, UserVariant

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

        latest_exams = (
            Progress.objects
            .filter(user=self.object)
            .order_by('exam_id', '-started')
            .distinct('exam_id')
            .values('id')
        )

        latest_progress = (
            Progress.objects
            .filter(user=self.object, id__in=latest_exams)
            .select_related('exam', 'exam__category')
            .only(
                'started', 'finished', 'passed', 'answers_quantity',
                'exam__title', 'exam__category__title'
            )
            .annotate(
                questions_count=Count(
                    'exam__questions', distinct=True,
                    filter=Q(exam__questions__visibility=True,
                             exam__questions__active=True)
                ),

                percentage=ExpressionWrapper(
                    F('answers_quantity') * 100 /
                    NullIf(Count('exam__questions', distinct=True, filter=Q(
                        exam__questions__visibility=True,
                        exam__questions__active=True,
                        finished__isnull=True)), 0),
                    output_field=IntegerField()
                ),

                percentage_correct=ExpressionWrapper(
                    NullIf(Count('answers', distinct=True, filter=Q(
                        answers__correct=True)), 0) * 100 /
                    F('answers_quantity'),
                    output_field=IntegerField()
                )
            )
            .order_by('-started')
        )

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


class UserProgressDetailView(DetailView):
    model = Progress
    template_name = 'users/progress_detail.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_queryset(self):
        user = self.kwargs.get('username')
        progress_id = self.kwargs.get('pk')
        queryset = (
            Progress.objects
            .filter(id=progress_id, user__username=user)
            .select_related('user', 'exam', 'exam__category')
            .prefetch_related(
                Prefetch(
                    'answers', queryset=UserAnswer.objects
                    .filter(progress=F('progress'))
                    .defer('question', 'date')
                    .annotate(
                        corrected_count=Count('variants', filter=Q(
                            variants__correct=True,
                            variants__selected=True
                        )),
                        selected_count=Count('variants', filter=Q(
                            variants__selected=True
                        ))
                    )
                ),
                Prefetch(
                    'answers__variants', queryset=UserVariant.objects
                    .filter(answer=F('answer'))
                    .defer('variant')
                    .order_by('-selected', '?')
                ))
            .only('user__username', 'exam__title', 'exam__show_results',
                  'exam__success_message', 'exam__category__title',
                  'exam__category__slug')
            .annotate(
                questions_count=Count(
                    'exam__questions', distinct=True, filter=Q(
                        exam__questions__visibility=True,
                        exam__questions__active=True
                    )),

                correct_count=Count(
                    'answers', distinct=True, filter=Q(
                        answers__correct=True
                    )),

                correct_percentage=ExpressionWrapper(
                    Count('answers', filter=Q(
                        answers__correct=True), distinct=True) * 100 /
                    NullIf(Count('exam__questions', distinct=True, filter=Q(
                        exam__questions__visibility=True,
                        exam__questions__active=True
                    )), 0), output_field=IntegerField()
                )
            )
        )
        return queryset
