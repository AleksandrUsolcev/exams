from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView

from .forms import ExamProcessForm
from .models import Category, Exam, Progress, Question, UserAnswer, UserVariant
from .utils import get_exams_with_progress


class IndexView(ListView):
    model = Category
    template_name = 'questions/index.html'
    context_object_name = 'categories'
    paginate_by = 15
    queryset = Category.objects.prefetch_related(
        Prefetch('exams', queryset=Exam.objects.filter(
            active=True, visibility=True)))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Exams - проверь свои знания'
        return context


class ExamListView(ListView):
    model = Exam
    template_name = 'questions/exam_list.html'
    context_object_name = 'exams'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(Category, slug=self.kwargs.get('slug'))
        context.update({'category': category})
        return context

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        queryset = get_exams_with_progress(self.request.user, slug)
        return queryset


class ExamDetailView(DetailView):
    model = Exam
    template_name = 'questions/exam_detail.html'

    def get_object(self, *args, **kwargs):
        slug = self.kwargs.get('slug')
        return get_object_or_404(Exam, slug=slug, active=True, visibility=True)


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
        self.question = self.exam.questions.all()[self.stage - 1]
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
                and self.progress.answers_count >= self.stage):
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
            'answers_count': stage
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
            return redirect('questions:exam_finally', slug=slug)
        elif not self.exam.show_results:
            return redirect('questions:exam_process', slug=slug, pk=stage + 1)
        else:
            return redirect('questions:exam_process', slug=slug, pk=stage)


class ExamFinallyView(LoginRequiredMixin, DetailView):
    model = Exam
    template_name = 'questions/exam_finally.html'

    def get(self, request, *args, **kwargs):
        progress = Progress.objects.filter(
            user=self.request.user,
            exam=self.get_object(),
            finished__isnull=False
        )
        if not progress.exists():
            return redirect('questions:exam_detail', self.get_object().slug)
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        latest_answers = UserAnswer.objects.prefetch_related(
            Prefetch('variants', queryset=UserVariant.objects.filter(
                answer=F('answer')).order_by('-selected', '?'))).filter(
            progress__user=self.request.user,
            progress__exam=self.object,
            progress__exam_revision=self.object.revision).annotate(
            corrected_count=Count('variants', filter=Q(
                variants__correct=True, variants__selected=True
            )),
            selected_count=Count('variants', filter=Q(variants__selected=True))
        ).order_by('date')

        correct_count = latest_answers.filter(correct=True).count()
        questions = self.object.questions.filter(active=True, visibility=True)
        questions_count = questions.count()
        try:
            correct_percentage = int((correct_count / questions_count) * 100)
        except ZeroDivisionError:
            correct_percentage = 0
        extra_context = {
            'latest_answers': latest_answers,
            'questions_count': questions_count,
            'correct_count': correct_count,
            'correct_percentage': correct_percentage
        }
        context.update(extra_context)
        return context
