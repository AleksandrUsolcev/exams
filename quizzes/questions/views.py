from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView, TemplateView

from .forms import QuizProcessForm
from .models import Progress, Quiz, QuizTheme


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


class QuizProcessView(TemplateView):
    template_name = 'questions/quiz_process.html'
    from_class = QuizProcessForm

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        stage = self.kwargs.get('pk')
        quiz = get_object_or_404(Quiz, slug=slug)
        progress, just_created = Progress.objects.get_or_create(
            user=self.request.user,
            quiz=quiz
        )
        if stage != progress.stage:
            return redirect(
                'questions:quiz_process',
                slug=slug,
                pk=progress.stage
            )
        return super().get(request)
