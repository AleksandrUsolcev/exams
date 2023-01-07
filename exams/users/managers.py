from django.contrib.auth.models import UserManager
from django.db.models import (Count, ExpressionWrapper, F, IntegerField,
                              OuterRef, Q, QuerySet, Subquery)
from django.db.models.expressions import Window
from django.db.models.functions.comparison import NullIf
from django.db.models.functions.window import DenseRank


class UserQuerySet(QuerySet):

    def with_progress(self) -> object:
        progress = (
            self
            .annotate(
                exams_count=Count('progression__exam', distinct=True, filter=Q(
                    progression__user_id=F('id'),
                    progression__finished__isnull=False
                )),
                passed_count=Count(
                    'progression__exam', distinct=True, filter=Q(
                        progression__id__in=Subquery(
                            self
                            .filter(progression__user_id=OuterRef('id'))
                            .order_by(
                                'progression__exam__id',
                                '-progression__started'
                            )
                            .distinct('progression__exam__id')
                            .values('progression__id')
                        ),
                        progression__user_id=F('id'),
                        progression__passed=True
                    )),
                correct_percentage=ExpressionWrapper(NullIf(
                    Count('progression__answers', distinct=True, filter=Q(
                        progression__user_id=F('id'),
                        progression__answers__correct=True
                    )), 0) * 100 /
                    NullIf(Count(
                        'progression__answers', distinct=True,
                        filter=Q(
                            progression__user_id=F('id'),
                        )), 0), output_field=IntegerField()
                ),
                points=ExpressionWrapper(
                    Count('progression__answers', distinct=True, filter=Q(
                        progression__id__in=Subquery(
                            self
                            .filter(progression__user_id=OuterRef('id'))
                            .order_by(
                                'progression__exam__id',
                                '-progression__started'
                            )
                            .distinct('progression__exam__id')
                            .values('progression__id')
                        ),
                        progression__answers__correct=True,
                        progression__passed=True
                    )) * 10, output_field=IntegerField()
                )
            )
        )
        return progress

    def get_rank(self):
        rank = (
            self
            .annotate(
                rank=Window(expression=DenseRank(), order_by=[
                    F('points').desc(),
                    F('passed_count').desc(),
                    F('correct_percentage').desc(),
                    F('exams_count').desc(),
                    F('date_joined').asc()
                ])
            )
        )
        return rank


class UserManager(UserManager):

    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)

    def with_progress(self):
        return self.get_queryset().with_progress()

    def get_rank(self):
        return self.get_queryset().get_rank()
