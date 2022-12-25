from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView

from .forms import QuizProcessForm
from .models import (Progress, Question, Quiz, QuizTheme, UserAnswer,
                     UserVariant)
from .utils import get_quizzes_with_progress


class IndexView(ListView):
    model = QuizTheme
    template_name = 'questions/index.html'
    context_object_name = 'themes'
    paginate_by = 15
    queryset = QuizTheme.objects.prefetch_related(
        Prefetch('quizzes', queryset=Quiz.objects.filter(
            active=True, visibility=True)))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Квизы!'
        return context


class QuizListView(ListView):
    model = Quiz
    template_name = 'questions/quiz_list.html'
    context_object_name = 'quizzes'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        theme = get_object_or_404(QuizTheme, slug=self.kwargs.get('slug'))
        context.update({'theme': theme})
        return context

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        return get_quizzes_with_progress(self.request.user, slug)


class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'questions/quiz_detail.html'

    def get_object(self, *args, **kwargs):
        slug = self.kwargs.get('slug')
        return get_object_or_404(Quiz, slug=slug, active=True, visibility=True)


class QuizProcessView(LoginRequiredMixin, FormView):
    template_name = 'questions/quiz_process.html'
    form_class = QuizProcessForm

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('users:signup')

        slug = self.kwargs.get('slug')
        self.stage = self.kwargs.get('pk')
        quiz = Quiz.objects.filter(
            slug=slug, active=True, visibility=True
        ).select_related('theme').prefetch_related(
            Prefetch(
                'questions', queryset=Question.objects.filter(
                    active=True, visibility=True)
            ))
        self.quiz = get_object_or_404(quiz)

        if self.quiz.questions.count() < self.stage:
            return redirect('questions:quiz_detail', slug)

        self.progress, _ = Progress.objects.get_or_create(
            user=self.request.user,
            quiz=self.quiz
        )
        self.question = self.quiz.questions.all()[self.stage - 1]
        self.last_stage = self.quiz.questions.count() == self.stage
        return super(QuizProcessView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        stage = self.kwargs.get('pk')
        if stage > self.progress.stage:
            return redirect(
                'questions:quiz_process',
                slug=self.kwargs.get('slug'),
                pk=self.progress.stage
            )
        return super().get(request)

    def get_initial(self):
        initial = super().get_initial()
        self.initial_data = {
            'quiz': self.quiz,
            'question': self.question,
            'progress': self.progress,
            'user': self.request.user,
            'stage': self.stage
        }
        initial.update(self.initial_data)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.progress.answers >= self.stage:
            answer = UserVariant.objects.filter(
                answer__user=self.request.user,
                answer__question=self.question,
                answer__quiz_revision=self.quiz.revision
            ).order_by('-selected', '?')
            self.initial_data['answer'] = answer
        context.update(self.initial_data)
        return context

    def form_valid(self, form):
        stage = self.kwargs.get('pk')
        data_update = {
            'stage': stage + 1,
            'answers': stage
        }
        if self.last_stage:
            data_update['passed'] = timezone.now()

        if self.progress.stage < stage + 1:
            Progress.objects.filter(
                user=self.request.user,
                quiz=self.quiz
            ).update(**data_update)
            form.answer()

        if self.last_stage:
            return redirect(
                'questions:quiz_finally',
                slug=self.kwargs.get('slug')
            )
        return redirect(
            'questions:quiz_process',
            slug=self.kwargs.get('slug'),
            pk=stage + 1
        )


class QuizFinallyView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = 'questions/quiz_finally.html'

    def get(self, request, *args, **kwargs):
        progress = Progress.objects.filter(
            user=self.request.user,
            quiz=self.get_object(),
            passed__isnull=False
        )
        if not progress.exists():
            return redirect('questions:quiz_detail', self.get_object().slug)
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        latest_answers = UserAnswer.objects.prefetch_related(
            Prefetch('variants', queryset=UserVariant.objects.filter(
                answer=F('answer')).order_by('-selected', '?'))).filter(
            user=self.request.user,
            quiz=self.object,
            quiz_revision=self.object.revision).annotate(
            corrected_count=Count('variants', filter=Q(
                variants__correct=True, variants__selected=True
            )),
            selected_count=Count('variants', filter=Q(variants__selected=True))
        ).order_by('date')

        correct_count = latest_answers.filter(correct=True).count()
        questions = self.object.questions.filter(active=True, visibility=True)
        questions_count = questions.count()
        try:
            correct_percentage = int((correct_count / questions_count) * 100)
        except ZeroDivisionError:
            correct_percentage = 0
        extra_context = {
            'latest_answers': latest_answers,
            'questions_count': questions_count,
            'correct_count': correct_count,
            'correct_percentage': correct_percentage
        }
        context.update(extra_context)
        return context
