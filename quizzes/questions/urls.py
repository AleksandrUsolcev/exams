from django.urls import path

from . import views

app_name = 'questions'

urlpatterns = [
    path(
        '',
        views.IndexView.as_view(),
        name='index'
    ),
    path(
        'theme/<slug:slug>/',
        views.QuizListView.as_view(),
        name='quiz_list'
    ),
    path(
        'quiz/<slug:slug>/',
        views.QuizDetailView.as_view(),
        name='quiz_detail'
    ),
    path(
        'quiz/<slug:slug>/progress/<int:pk>/',
        views.QuizProcessView.as_view(),
        name='quiz_process'
    ),
    path(
        'quiz/<slug:slug>/finally/',
        views.QuizFinallyView.as_view(),
        name='quiz_finally'
    ),
    path(
        'quiz-add',
        views.QuizAddView.as_view(),
        name='quiz_add'
    ),
]
