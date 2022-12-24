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
        self.slug = self.kwargs.get('slug')
        self.stage = self.kwargs.get('pk')
        if not self.request.user.is_authenticated:
            return redirect('users:signup')
        self.quiz = get_object_or_404(Quiz, slug=self.slug)
        self.progress, self.just_created = Progress.objects.get_or_create(
            user=self.request.user,
            quiz=self.quiz
        )
        self.question = Question.objects.filter(quiz=self.quiz)
        self.questions_list = self.quiz.questions.filter(
            active=True, visibility=True
        )
        if self.stage > self.questions_list.count():
            Progress.objects.filter(
                user=self.request.user,
                quiz=self.quiz
            ).update(passed=timezone.now())
            return redirect(
                'questions:quiz_finally',
                slug=self.slug
            )
        self.answers = UserAnswer.objects.filter(
            user=self.request.user,
            question=self.question[self.stage - 1],
            quiz_revision=self.quiz.revision
        ).prefetch_related('variants')
        self.answered = UserAnswer.objects.filter(
            user=self.request.user,
            quiz_revision=self.quiz.revision
        ).values_list('question__id', flat=True)
        self.already_answered = False
        if self.answers.exists():
            self.already_answered = True
        return super(QuizProcessView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.stage > self.progress.stage:
            return redirect(
                'questions:quiz_process',
                slug=self.slug,
                pk=self.progress.stage
            )
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.question[self.stage - 1]
        extra_context = {
            'progress': self.progress,
            'quiz': self.quiz,
            'just_created': self.just_created,
            'question': question,
            'questions_list': self.questions_list,
            'stage': self.stage,
            'already_answered': self.already_answered,
            'answers': self.answers,
            'answered': self.answered
        }
        context.update(extra_context)
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial_data = {
            'question': self.question[self.stage - 1],
            'quiz': self.quiz,
            'user': self.request.user,
            'already_answered': self.already_answered
        }
        initial.update(initial_data)
        return initial

    def form_valid(self, form):
        if self.progress.stage < self.stage + 1:
            Progress.objects.filter(
                user=self.request.user,
                quiz=self.quiz
            ).update(stage=self.stage + 1, answers=self.stage)
        form.answer()
        return redirect(
            'questions:quiz_process',
            slug=self.slug,
            pk=self.stage + 1
        )


class QuizFinallyView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = 'questions/quiz_finally.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        get_object_or_404(
            Progress,
            quiz=self.object,
            user=self.request.user
        )

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
