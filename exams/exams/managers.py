from itertools import chain
from operator import attrgetter

from django.db.models import (Case, Count, DateTimeField, ExpressionWrapper, F,
                              IntegerField, Manager, Q, QuerySet, When)
from django.db.models.functions.comparison import NullIf


class CategoryManager(Manager):

    def exams_count(self) -> object:
        count = (
            self
            .only('title', 'slug', 'show_empty', 'description')
            .annotate(
                exams_count=Count('exams', distinct=True, filter=Q(
                    exams__active=True, exams__visibility=True
                ))
            )
            .order_by('priority', '-exams_count', 'title')
        )
        return count


class SprintQuerySet(QuerySet):

    def with_stats(self, user: object = None) -> object:

        stats = (
            self
            .annotate(
                exams_count=Count('exams', distinct=True, filter=Q(
                    exams__active=True, exams__visibility=True
                )),
                questions_count=Count(
                    'exams__questions', distinct=True, filter=Q(
                        exams__questions__active=True,
                        exams__questions__visibility=True
                    )
                ),
            )
            .order_by('-created')
        )

        if user.is_authenticated:
            user_progress = (
                self
                .filter(progress__user=user)
                .order_by('progress__id', '-progress__started')
                .distinct('progress__id')
                .values('progress__id')
            )

            user_started = Case(
                When(progress__user=user, then=F('progress__started')),
                default=None, output_field=DateTimeField())

            user_finished = Case(
                When(progress__user=user, then=F('progress__finished')),
                default=None, output_field=DateTimeField())

            user_annotates = {
                'user_started': user_started,
                'user_finished': user_finished
            }

            only_with_progress = (
                stats
                .filter(progress__id__in=user_progress)
                .annotate(**user_annotates)
            )
            without_user = stats.exclude(progress__id__in=user_progress)
            stats = sorted(
                list(chain(only_with_progress, without_user)),
                key=attrgetter('created'), reverse=True
            )

        return stats


class SprintManager(Manager):

    def get_queryset(self):
        return SprintQuerySet(self.model, using=self._db)

    def with_stats(self):
        return self.get_queryset().with_stats()


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
                passed=F('progress__passed'),
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
                        progress__answers__correct=True)), 0) * 100
                    / F('progress__answers_quantity'),
                    output_field=IntegerField()
                )
            )
        )
        return progress

    def list_(self, user: object = None, only_user: bool = False,
              in_sprint: bool = False) -> object:
        filter_data = {
            'visibility': True,
            'active': True
        }
        fields_only = ['title', 'slug', 'created',
                       'priority', 'category__title', 'sprint__title']

        order_data = ['-created']

        if in_sprint:
            order_data = ['priority']

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

                if user.hide_finished_exams:
                    return query_without_user.order_by(*order_data)

                if in_sprint:
                    exams = sorted(
                        list(chain(query_without_user, exams)),
                        key=attrgetter('priority'), reverse=False
                    )
                else:
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
            .order_by(*order_data)
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
