from rest_framework.pagination import PageNumberPagination


class ExamPagination(PageNumberPagination):
    page_size = 10
