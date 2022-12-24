from rest_framework.pagination import PageNumberPagination


class QuizPagination(PageNumberPagination):
    page_size = 10
