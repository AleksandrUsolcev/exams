from django.urls import include, path
from rest_framework.routers import DefaultRouter


from . import views

app_name = 'api'

v1 = DefaultRouter()

v1.register('quizzes', views.QuizViewSet, basename='quizzes')

urlpatterns = [
    path('', include(v1.urls))
]
