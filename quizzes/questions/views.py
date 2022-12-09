from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView

from .forms import QuizProcessForm
from .models import Progress, Question, Quiz, QuizTheme


class IndexView(ListView):
    model = QuizTheme
    template_name = 'questions/index.html'
    context_object_name = 'themes'
    queryset = QuizTheme.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Квизы!'
        return context


class QuizListView(ListView):
    model = Quiz
    template_name = 'questions/quiz_list.html'
    context_object_name = 'quizzes'
    queryset = Quiz.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        theme = get_object_or_404(QuizTheme, slug=self.kwargs.get('slug'))
        quizes = Quiz.objects.filter(theme=theme)
        extra_context = {
            'theme': theme,
            'quizes': quizes
        }
        context.update(extra_context)
        return context

    def get_queryset(self):
        theme = get_object_or_404(QuizTheme, slug=self.kwargs.get('slug'))
        return Quiz.objects.filter(theme=theme)


class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'questions/quiz_detail.html'


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
        }
        context.update(extra_context)
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial['question'] = self.question[self.stage - 1]
        return initial

    def form_valid(self, form):
        if self.progress.stage < self.stage + 1:
            Progress.objects.filter(
                user=self.request.user,
                quiz=self.quiz
            ).update(stage=self.stage + 1)
        return redirect(
            'questions:quiz_process',
            slug=self.slug,
            pk=self.stage + 1
        )
        # return super().form_valid(form)
