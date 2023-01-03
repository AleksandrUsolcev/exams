from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView

from .forms import ExamProcessForm
from .models import Category, Exam, Progress, Question, UserAnswer, UserVariant


class IndexView(ListView):
    model = Category
    template_name = 'questions/index.html'
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
    template_name = 'questions/exam_list.html'
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
    template_name = 'questions/exam_detail.html'

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
    template_name = 'questions/exam_process.html'
    form_class = ExamProcessForm

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('users:signup')

        slug = self.kwargs.get('slug')
        self.stage = self.kwargs.get('pk')
        exam = Exam.objects.filter(
            slug=slug, active=True, visibility=True
        ).select_related('category').prefetch_related(
            Prefetch(
                'questions', queryset=Question.objects.filter(
                    active=True, visibility=True).annotate(
                        corrected=Count('answers__correct', filter=Q(
                            answers__progress__user=self.request.user,
                            answers__progress__exam_revision=F(
                                'exam__revision'),
                            answers__progress__exam=F('exam'),
                            answers__correct=True
                        )),
                        finished=Count('answers__date', filter=Q(
                            answers__progress__user=self.request.user,
                            answers__progress__exam_revision=F(
                                'exam__revision'),
                            answers__progress__exam=F('exam'),
                            answers__date__isnull=False
                        ))
                )
            )
        )
        self.exam = get_object_or_404(exam)

        if self.exam.questions.count() < self.stage:
            return redirect('questions:exam_detail', slug)

        self.progress, _ = Progress.objects.get_or_create(
            user=self.request.user,
            exam=self.exam,
            exam_revision=self.exam.revision,
            exam_title=self.exam.title
        )
        self.question = self.exam.questions.all().order_by(
            '-visibility', '-active', 'priority', 'id', 'text')[self.stage - 1]
        self.last_stage = self.exam.questions.count() == self.stage
        return super(ExamProcessView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        stage = self.kwargs.get('pk')
        if (stage > self.progress.stage
            or not self.exam.show_results
                and stage != self.progress.stage):
            return redirect(
                'questions:exam_process',
                slug=self.kwargs.get('slug'),
                pk=self.progress.stage
            )
        return super().get(request)

    def get_initial(self):
        initial = super().get_initial()
        self.initial_data = {
            'exam': self.exam,
            'question': self.question,
            'progress': self.progress,
            'user': self.request.user,
            'stage': self.stage
        }
        initial.update(self.initial_data)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if (self.exam.show_results
                and self.progress.answers_quantity >= self.stage):
            answer = UserAnswer.objects.prefetch_related(
                Prefetch('variants', queryset=UserVariant.objects.filter(
                    answer=F('answer')).order_by('-selected', '?'))).filter(
                progress__user=self.request.user,
                progress__exam=self.exam,
                question=self.question,
                progress__exam_revision=self.exam.revision).annotate(
                corrected_count=Count('variants', filter=Q(
                    variants__correct=True, variants__selected=True
                )),
                selected_count=Count('variants', filter=Q(
                    variants__selected=True
                ))
            ).order_by('date').first()
            extra_context = {
                'answer': answer,
                'last_stage': self.last_stage,
                'next_stage': self.stage + 1
            }
            context.update(extra_context)
        context.update(self.initial_data)
        return context

    def form_valid(self, form):
        stage = self.kwargs.get('pk')
        slug = self.kwargs.get('slug')
        data_update = {
            'stage': stage + 1,
            'answers_quantity': stage
        }
        if self.last_stage:
            data_update['finished'] = timezone.now()
            data_update['passed'] = True

        if self.progress.stage < stage + 1:
            Progress.objects.filter(
                user=self.request.user,
                exam=self.exam
            ).update(**data_update)
            form.answer()

        if self.last_stage and not self.exam.show_results:
            return redirect('users:progress_detail', pk=self.progress.id)
        elif not self.exam.show_results:
            return redirect('questions:exam_process', slug=slug, pk=stage + 1)
        else:
            return redirect('questions:exam_process', slug=slug, pk=stage)
