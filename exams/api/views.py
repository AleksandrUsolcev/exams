from django_filters.rest_framework import DjangoFilterBackend
from questions.models import Exam
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ModelViewSet

from .pagination import ExamPagination
from .serializers import ExamSerializer


class ExamViewSet(ModelViewSet):
    serializer_class = ExamSerializer
    queryset = Exam.objects.filter(
        active=True, visibility=True, category__isnull=False
    ).prefetch_related('category')
    http_method_names = ('get')
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('title',)
    pagination_class = ExamPagination
