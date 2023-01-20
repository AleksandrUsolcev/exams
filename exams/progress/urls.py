from django.urls import path

from . import views

app_name = 'progress'

urlpatterns = [
    path(
        'progress/<int:pk>/',
        views.ProgressDetailView.as_view(),
        name='progress_detail'
    ),
    path(
        'progress/@<slug:username>/',
        views.ProgressListView.as_view(),
        name='progress_list'
    ),
    path(
        'progress/tracker/',
        views.ProgressTrackerView.as_view(),
        name='progress_tracker'
    )
]
