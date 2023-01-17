from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (Count, ExpressionWrapper, F, IntegerField,
                              Prefetch, Q)
from django.db.models.functions.comparison import NullIf
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView
from progress.models import Progress, UserAnswer, UserSprint, UserVariant

from .forms import ExamProcessForm
from .models import Category, Exam, Question, Sprint, Variant
from .utils import (get_humanize_time, get_next_exam_in_sprint,
                    get_previous_exam_in_sprint)


class IndexView(ListView):
    model = Category
    template_name = 'exams/index.html'
    context_object_name = 'categories'
    queryset = Category.objects.exams_count()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exams = (
            Exam.objects
            .filter(active=True, visibility=True)
            .select_related('category')
            .list_(user=self.request.user)
        )
        extra_context = {
            'title': 'Exams',
            'exams': exams[:12]
        }
        if len(exams) > 5:
            extra_context['more_link'] = True
        context.update(extra_context)
        return context


class SprintListView(ListView):
    model = Sprint
    template_name = 'exams/sprint_list.html'
    context_object_name = 'sprints'
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            Sprint.objects
            .all()
            .with_stats(user=self.request.user)
        )
        return queryset


class SprintDetailView(ListView):
    model = Exam
    template_name = 'exams/sprint_detail.html'
    paginate_by = 18
    context_object_name = 'exams'

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        queryset = (
            Exam.objects
            .filter(active=True, visibility=True, sprint__slug=slug)
            .select_related('category')
            .list_(user=self.request.user, in_sprint=True)
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug')
        sprint = get_object_or_404(Sprint, slug=slug)
        context['sprint'] = sprint
        return context


class ExamListView(ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'
    paginate_by = 18

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.request.GET.get('category')

        if slug:
            category = get_object_or_404(Category, slug=slug)
            context.update({'category': category})

        categories = Category.objects.exams_count()
        context.update({'categories': categories})
        return context

    def get_queryset(self):
        slug = self.request.GET.get('category')
        filter_data = {
            'active': True,
            'visibility': True
        }

        if slug:
            filter_data['category__slug'] = slug

        queryset = (
            Exam.objects
            .filter(**filter_data)
            .select_related('category')
            .list_(user=self.request.user)
        )
        return queryset


class ExamDetailView(DetailView):
    model = Exam
    template_name = 'exams/exam_detail.html'

    def get_object(self, *args, **kwargs):
        slug = self.kwargs.get('slug')
        exam = (
            Exam.objects
            .filter(slug=slug, active=True, visibility=True)
            .select_related('category', 'sprint')
            .users_stats()
            .questions_count()
        )
        return get_object_or_404(exam)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug')
        exam = self.object

        if self.request.user.is_authenticated:
            progress = (
                Exam.objects
                .filter(
                    slug=slug, progress__user=self.request.user,
                    active=True, visibility=True
                )
                .with_request_user_progress()
                .order_by('-started')
                .first()
            )
            context.update(
                {'progress': progress, 'previous_exam_passed': True}
            )

            if exam.sprint and not exam.sprint.any_order and not progress:

                if exam.sprint:
                    previous_exam = get_previous_exam_in_sprint(exam)
                    context['previous_exam'] = previous_exam

                    if previous_exam:
                        previous_exam_passed = (
                            Progress.objects
                            .filter(
                                user=self.request.user,
                                exam=previous_exam,
                                passed=True
                            )
                        ).exists()

                        context['previous_exam_passed'] = previous_exam_passed

        if exam.timer:
            context['humanize_time'] = get_humanize_time(exam.timer)
        return context


class ExamProcessView(LoginRequiredMixin, FormView):
    template_name = 'exams/exam_process.html'
    form_class = ExamProcessForm

    def get_or_create_progress(self):
        progress = (
            Progress.objects
            .filter(user=self.request.user, exam__slug=self.slug)
            .order_by('-started')
            .get_percentage()
            .first()
        )
        restart = self.request.GET.get('restart')

        if not progress or progress.finished and restart:
            exam = (
                Exam.objects
                .filter(slug=self.slug, active=True, visibility=True)
                .select_related('sprint')
                .first()
            )

            user_sprint = (
                UserSprint.objects
                .filter(user=self.request.user, sprint=exam.sprint)
            )

            if (
                exam.sprint and not exam.sprint.any_order and not progress
                or exam.allow_retesting
            ):
                if exam.sprint:
                    previous_exam = get_previous_exam_in_sprint(exam)

                    if previous_exam:
                        previous_is_passed = (
                            Progress.objects
                            .filter(
                                exam=previous_exam, user=self.request.user,
                                passed=True
                            )
                        )
                        if not previous_is_passed.exists():
                            return False

                if not user_sprint.exists() and exam.sprint:
                    UserSprint.objects.create(
                        user=self.request.user, sprint=exam.sprint
                    )
                progress = Progress.objects.create(
                    user=self.request.user,
                    exam=exam,
                    exam_revision=exam.revision
                )
        return progress

    def get_remaining_time(self):
        time_to_pass = self.question.exam.timer * 60
        current = (timezone.now() - self.progress.started).total_seconds()
        remaining_time = int(time_to_pass - current)
        return remaining_time

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('users:signup')

        self.slug = self.kwargs.get('slug')
        self.stage = self.kwargs.get('pk')
        self.progress = self.get_or_create_progress()

        if self.progress is False:
            return redirect('exams:exam_detail', self.slug)

        self.questions_queue = (
            Question.objects
            .filter(
                active=True, visibility=True,
            )
            .annotate(
                global_correct_percentage=ExpressionWrapper(
                    NullIf(Count('answers', distinct=True, filter=Q(
                        answers__correct=True
                    )), 0) * 100
                    / NullIf(Count('answers', distinct=True), 0),
                    output_field=IntegerField()
                )
            )
            .filter(exam__slug=self.slug)
            .annotate(
                corrected=Count('answers__correct', filter=Q(
                    answers__progress=self.progress,
                    answers__correct=True
                )),
                finished=Count('answers__date', filter=Q(
                    answers__progress=self.progress,
                    answers__date__isnull=False
                ))
            )
            .select_related('exam', 'exam__category')
            .order_by('priority', 'id')
        )

        if len(self.questions_queue) < self.stage:
            return redirect('exams:exam_detail', self.slug)

        self.question = self.questions_queue[self.stage - 1]
        self.last_stage = len(self.questions_queue) == self.stage
        self.answered = self.stage < self.progress.stage
        return super(ExamProcessView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if (
            self.stage > self.progress.stage
            or not self.question.exam.show_results
            and self.stage != self.progress.stage
        ):
            return redirect(
                'exams:exam_process',
                slug=self.kwargs.get('slug'),
                pk=self.progress.stage
            )
        return super().get(request)

    def get_initial(self):
        initial = super().get_initial()
        if self.answered is False:
            self.variants = Variant.objects.filter(question=self.question)
            initial['variants'] = self.variants
        self.initial_data = {
            'question': self.question,
            'answered': self.answered,
            'progress': self.progress,
            'user': self.request.user,
            'stage': self.stage
        }
        initial.update(self.initial_data)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.question.exam.show_results and self.answered:
            filter_data = {
                'answer': F('answer')
            }

            answer = (
                UserAnswer.objects
                .prefetch_related(Prefetch('variants', queryset=(
                    UserVariant.objects
                    .filter(**filter_data)
                    .order_by('-selected', '?')
                )))
                .filter(
                    progress=self.progress,
                    question=self.question,
                )
                .get_counters()
                .order_by('date')
                .first()
            )
            extra_context = {
                'answer': answer,
                'last_stage': self.last_stage,
                'next_stage': self.stage + 1
            }
            context.update(extra_context)

        if self.question.exam.timer:
            context['remaining_time'] = self.get_remaining_time()
            context['humanize_time'] = get_humanize_time(
                self.question.exam.timer)

        context['questions'] = self.questions_queue
        context.update(self.initial_data)
        return context

    def form_valid(self, form):
        data = {
            'stage': self.stage + 1,
            'answers_quantity': self.stage
        }

        if self.progress.stage < self.stage + 1:
            Progress.objects.filter(id=self.progress.id).update(**data)

            match True:
                case self.question.many_correct:
                    form.answer_with_many_correct()
                case self.question.one_correct:
                    form.answer_with_one_correct()
                case self.question.text_answer:
                    form.answer_with_text_answer()

        if self.last_stage:
            update = {
                'finished': timezone.now(),
                'passed': True
            }
            actual_progress = (
                Progress.objects
                .filter(id=self.progress.id)
                .get_percentage()
            )

            if self.question.exam.timer and self.get_remaining_time() < 0:
                update['passed'] = False

            try:
                if (
                    self.question.exam.required_percent
                    and self.question.exam.required_percent
                    > actual_progress.first().correct_percentage
                ):
                    update['passed'] = False
            except TypeError:
                update['passed'] = False

            actual_progress.update(**update)

            if update.get('passed') is True and self.question.exam.sprint:
                next_exam = get_next_exam_in_sprint(self.question.exam)
                user_sprint = (
                    UserSprint.objects
                    .filter(
                        user=self.request.user,
                        sprint=self.question.exam.sprint
                    )
                )

                if not next_exam and user_sprint.exists():
                    user_sprint.update(finished=timezone.now())

            return redirect('progress:progress_detail', pk=self.progress.id)

        elif self.question.exam.show_results:
            return redirect(
                'exams:exam_process', slug=self.slug, pk=self.stage)
        else:
            return redirect(
                'exams:exam_process', slug=self.slug, pk=self.stage + 1)
