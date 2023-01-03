from itertools import chain
from operator import attrgetter

from django.db.models import (Count, ExpressionWrapper, F, IntegerField,
                              Manager, Prefetch, Q, QuerySet)
from django.db.models.functions.comparison import NullIf


class CategoryManager(Manager):

    def exams_count(self) -> object:
        count = (
            self
            .only('title', 'slug', 'show_empty')
            .annotate(
                exams_count=Count('exams', distinct=True, filter=Q(
                    exams__active=True, exams__visibility=True
                ))
            )
            .order_by('priority', '-exams_count', 'title')
        )
        return count


class ExamQuerySet(QuerySet):

    def questions_count(self):
        count = (
            self
            .annotate(
                questions_count=Count('questions', distinct=True, filter=Q(
                    questions__visibility=True,
                    questions__active=True
                ))
            )
        )
        return count

    def users_stats(self):
        stats = (
            self
            .annotate(
                users_count=Count('progress__user', distinct=True, filter=Q(
                    progress__finished__isnull=False
                )),
                average_progress=ExpressionWrapper(NullIf(Count(
                    'progress__answers', distinct=True, filter=Q(
                        progress__finished__isnull=False,
                        progress__answers__correct=True
                    )), 0) * 100 / NullIf(Count(
                        'progress__answers', distinct=True, filter=Q(
                            progress__finished__isnull=False
                        )), 0),
                    output_field=IntegerField()
                )
            )
        )
        return stats

    def with_request_user_progress(self):
        progress = (
            self
            .annotate(
                current_answers=F('progress__answers_quantity'),
                current_stage=F('progress__stage'),
                progress_id=F('progress__id'),
                started=F('progress__started'),
                finished=F('progress__finished'),
                percentage_answers=ExpressionWrapper(
                    F('progress__answers_quantity') * 100 / NullIf(Count(
                        'questions', distinct=True, filter=Q(
                            questions__active=True,
                            questions__visibility=True
                        )), 0),
                    output_field=IntegerField()
                ),
                percentage_correct=ExpressionWrapper(
                    NullIf(Count('progress__answers', distinct=True, filter=Q(
                        progress__answers__correct=True)), 0) * 100 /
                    F('progress__answers_quantity'),
                    output_field=IntegerField()
                )
            )
        )
        return progress

    def list_(self, user: object = None, only_user: bool = False) -> object:
        filter_data = {
            'visibility': True,
            'active': True
        }
        fields_only = ['title', 'slug', 'created', 'category__title']

        try:
            user_progress = (
                self
                .filter(progress__user=user)
                .order_by('progress__exam__id', '-progress__started')
                .distinct('progress__exam__id')
                .values('progress__id')
            )
            filter_data['progress__id__in'] = user_progress
            exams = self.filter(**filter_data).with_request_user_progress()

            if only_user is False:
                exams = exams.only(*fields_only).questions_count()
                query_without_user = (
                    self
                    .users_stats()
                    .filter(~Q(id__in=exams))
                    .only(*fields_only)
                    .questions_count()
                )
                exams = sorted(
                    list(chain(query_without_user, exams)),
                    key=attrgetter('created'), reverse=True
                )
                return exams
            else:
                return exams.only(*fields_only).questions_count()

        except TypeError:
            pass

        exams = (
            self
            .users_stats()
            .filter(**filter_data)
            .only(*fields_only)
            .questions_count()
            .order_by('-created')
        )
        return exams


class ExamManager(Manager):

    def get_queryset(self):
        return ExamQuerySet(self.model, using=self._db)

    def questions_count(self):
        return self.get_queryset().questions_count()

    def users_stats(self):
        return self.get_queryset().users_stats()

    def with_request_user_progress(self):
        return self.get_queryset().with_request_user_progress()

    def list_(self, user: object = None, only_user: bool = False) -> object:
        return self.get_queryset().list_(user, only_user)


class ProgressQuerySet(QuerySet):

    def get_details(self, answers: object, variants: object) -> object:
        details = (
            self
            .select_related('user', 'exam', 'exam__category')
            .prefetch_related(
                Prefetch(
                    'answers', queryset=answers.objects
                    .filter(progress=F('progress'))
                    .defer('question', 'date')
                    .annotate(
                        corrected_count=Count('variants', filter=Q(
                            variants__correct=True,
                            variants__selected=True
                        )),
                        selected_count=Count('variants', filter=Q(
                            variants__selected=True
                        ))
                    )
                ),
                Prefetch(
                    'answers__variants', queryset=variants.objects
                    .filter(answer=F('answer'))
                    .defer('variant')
                    .order_by('-selected', '?')
                ))
            .only('user__username', 'exam__title', 'exam__show_results',
                  'exam__success_message', 'exam__category__title',
                  'exam__category__slug')
            .annotate(
                questions_count=Count(
                    'exam__questions', distinct=True, filter=Q(
                        exam__questions__visibility=True,
                        exam__questions__active=True
                    )),

                correct_count=Count(
                    'answers', distinct=True, filter=Q(
                        answers__correct=True
                    )),

                correct_percentage=ExpressionWrapper(
                    Count('answers', filter=Q(
                        answers__correct=True), distinct=True) * 100 /
                    NullIf(Count('exam__questions', distinct=True, filter=Q(
                        exam__questions__visibility=True,
                        exam__questions__active=True
                    )), 0), output_field=IntegerField()
                )
            )
        )
        return details


class ProgressManager(Manager):

    def get_queryset(self):
        return ProgressQuerySet(self.model, using=self._db)

    def get_details(self, answers: object, variants: object) -> object:
        return self.get_queryset().get_details()
