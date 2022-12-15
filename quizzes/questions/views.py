from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import CreateView, DetailView, FormView, ListView

from .forms import QuizAddUpdateView, QuizProcessForm
from .models import Progress, Question, Quiz, QuizTheme, UserAnswer


class IndexView(ListView):
    model = QuizTheme
    template_name = 'questions/index.html'
    context_object_name = 'themes'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Квизы!'
        return context

    def get_queryset(self):
        return QuizTheme.objects.prefetch_related('quizzes')


class QuizListView(ListView):
    model = Quiz
    template_name = 'questions/quiz_list.html'
    context_object_name = 'quizzes'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        theme = get_object_or_404(QuizTheme, slug=self.kwargs.get('slug'))
        extra_context = {}
        if self.request.user.is_authenticated:
            progress = Progress.objects.select_related('quiz').filter(
                user=self.request.user,
                quiz__theme__slug=self.kwargs.get('slug')
            ).annotate(
                questions_count=Count('quiz__questions')
            )
            in_progress = [fields.quiz.id for fields in progress]
            passed = [fields.quiz.id for fields in progress if fields.passed]
            passed_percent = {}
            current_stages = {}
            for f in progress:
                if f.questions_count:
                    result = int(((f.stage - 1) * 100) / f.questions_count)
                    passed_percent[f.quiz.id] = result
                current_stages[f.quiz.id] = f.stage
            extra_context = {
                'in_progress': in_progress,
                'passed': passed,
                'passed_percent': passed_percent,
                'current_stages': current_stages
            }
        extra_context['theme'] = theme
        context.update(extra_context)
        return context

    def get_queryset(self):
        return Quiz.objects.filter(
            theme__slug=self.kwargs.get('slug')).annotate(
            questions_count=Count('questions')
        ).order_by('-created')


class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'questions/quiz_detail.html'


class QuizAddView(CreateView):
    form_class = QuizAddUpdateView
    template_name = 'questions/quiz_add.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class QuizProcessView(FormView):
    template_name = 'questions/quiz_process.html'
    form_class = QuizProcessForm

    def dispatch(self, request, *args, **kwargs):
        self.slug = self.kwargs.get('slug')
        self.stage = self.kwargs.get('pk')
        self.quiz = get_object_or_404(Quiz, slug=self.slug)
        self.progress, self.just_created = Progress.objects.get_or_create(
            user=self.request.user,
            quiz=self.quiz
        )
        self.question = Question.objects.filter(quiz=self.quiz)
        if self.stage > self.quiz.questions.count():
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
        )
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
            'stage': self.stage,
            'already_answered': self.already_answered,
            'answers': self.answers
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


class QuizFinallyView(DetailView):
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
            'variants'
        ).filter(
            user=self.request.user,
            quiz=self.object,
            quiz_revision=self.object.revision
        ).order_by('date')
        correct_count = latest_answers.filter(correct=True).count()
        questions_count = self.object.questions.count()
        correct_percentage = int((correct_count / questions_count) * 100)
        extra_context = {
            'latest_answers': latest_answers,
            'questions_count': questions_count,
            'correct_count': correct_count,
            'correct_percentage': correct_percentage
        }
        context.update(extra_context)
        return context
