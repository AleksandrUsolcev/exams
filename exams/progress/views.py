from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView
from users.models import User

from exams.models import Exam
from exams.utils import get_next_exam_in_sprint

from .models import Progress, UserAnswer, UserVariant


class ProgressDetailView(DetailView):
    model = Progress
    template_name = 'progress/progress_detail.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_object(self):
        progress_id = self.kwargs.get('pk')
        progress = (
            Progress.objects
            .filter(id=progress_id)
            .select_related('exam__sprint')
            .get_details(variants=UserVariant, answers=UserAnswer)
            .get_percentage()
        )
        return get_object_or_404(progress)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        uuid = self.request.GET.get('uuid')
        context['access_allowed'] = True

        if self.object.user == user and self.object.exam.sprint:
            previously_passed = (
                Progress.objects
                .filter(user=user, exam=self.object.exam, passed=True)
                .exists()
            )

            if previously_passed or self.object.exam.sprint.any_order:
                next_exam = get_next_exam_in_sprint(self.object.exam)
                context['next_exam'] = next_exam

        if self.object.exam.only_guest_keys:
            url = self.request.build_absolute_uri(self.request.path)
            shared_url = url + '?uuid=' + self.object.guest_key
            context['shared_url'] = shared_url

            if not (
                uuid == self.object.guest_key
                or self.object.user == user
                or user.is_staff
            ):
                context['access_allowed'] = False

        if (
            self.object.user == user
            and not self.object.passed
            and self.object.exam.allow_retesting
        ):
            context['retesting'] = True

        return context


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
