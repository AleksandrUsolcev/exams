from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView

from .models import Quiz, QuizTheme


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
