from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from exams.models import Exam
from users.models import User

from .models import Progress, UserAnswer, UserVariant


class ProgressDetailView(DetailView):
    model = Progress
    template_name = 'progress/progress_detail.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_queryset(self):
        progress_id = self.kwargs.get('pk')
        queryset = (
            Progress.objects
            .filter(id=progress_id)
            .get_details(variants=UserVariant, answers=UserAnswer)
            .get_percentage()
        )
        return queryset


class ProgressListView(ListView):
    model = Progress
    template_name = 'progress/progress_list.html'
    context_object_name = 'exams'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    paginate_by = 18

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get('username')
        context.update({'progress_url': True, 'username': username})
        return context

    def get_queryset(self):
        username = self.kwargs.get('username')
        user = get_object_or_404(User, username=username, is_active=True)
        queryset = (
            Exam.objects
            .select_related('category', 'sprint')
            .list_(user=user, only_user=True)
            .order_by('-started')
        )
        return queryset
