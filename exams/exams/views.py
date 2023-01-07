from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (Count, ExpressionWrapper, F, IntegerField,
                              Prefetch, Q)
from django.db.models.functions.comparison import NullIf
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView
from progress.models import Progress, UserAnswer, UserVariant

from .forms import ExamProcessForm
from .models import Category, Exam, Question, Variant


class IndexView(ListView):
    model = Category
    template_name = 'exams/index.html'
    context_object_name = 'categories'
    queryset = Category.objects.exams_count()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exams = (
            Exam.objects
            .select_related('category')
            .list_(user=self.request.user)
        )
        extra_context = {
            'title': 'Exams - проверь свои знания',
            'exams': exams[:12]
        }
        context.update(extra_context)
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
        filter_data = {}

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
            .select_related('category')
            .users_stats()
            .questions_count()
        )
        return get_object_or_404(exam, slug=slug, active=True, visibility=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug')

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
            context.update({'progress': progress})

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
            exam = get_object_or_404(
                Exam, slug=self.slug, active=True, visibility=True
            )
            if not progress or exam.allow_retesting:
                progress = Progress.objects.create(
                    user=self.request.user,
                    exam=exam,
                    exam_revision=exam.revision
                )
        return progress

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('users:signup')

        self.slug = self.kwargs.get('slug')
        self.stage = self.kwargs.get('pk')
        self.progress = self.get_or_create_progress()

        self.questions_queue = (
            Question.objects
            .filter(
                active=True, visibility=True,
            )
            .annotate(
                global_correct_percentage=ExpressionWrapper(
                    NullIf(Count('answers', distinct=True, filter=Q(
                        answers__correct=True
                    )), 0) * 100 /
                    NullIf(Count('answers', distinct=True), 0),
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
            .only(
                'text', 'success_message', 'type', 'exam__show_results',
                'exam__empty_answers', 'exam__timer', 'exam__required_percent',
                'exam__shuffle_variants', 'exam__slug', 'exam__title',
                'exam__category__title', 'exam__category__slug'
            )
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
            answer = (
                UserAnswer.objects
                .prefetch_related(Prefetch('variants', queryset=(
                    UserVariant.objects
                    .filter(answer=F('answer'))
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
            if self.question.many_correct:
                form.answer_with_many_correct()
            elif self.question.one_correct:
                form.answer_with_one_correct()

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

        if self.last_stage and not self.question.exam.show_results:
            return redirect('progress:progress_detail', pk=self.progress.id)
        elif not self.question.exam.show_results:
            return redirect(
                'exams:exam_process', slug=self.slug, pk=self.stage + 1)
        else:
            return redirect(
                'exams:exam_process', slug=self.slug, pk=self.stage)
