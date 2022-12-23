from django_filters.rest_framework import DjangoFilterBackend
from questions.models import Quiz
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ModelViewSet

from .serializers import QuizSerializer


class QuizViewSet(ModelViewSet):
    serializer_class = QuizSerializer
    queryset = Quiz.objects.filter()
    http_method_names = ('get')
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('title',)