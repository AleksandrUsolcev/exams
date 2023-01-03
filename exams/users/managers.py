from django.contrib.auth.models import UserManager
from django.db.models import (Count, ExpressionWrapper, F, IntegerField, Q,
                              QuerySet)
from django.db.models.functions.comparison import NullIf


class UserQuerySet(QuerySet):

    def with_progress(self) -> object:
        progress = (
            self
            .annotate(
                exams_count=Count('progression__exam', distinct=True, filter=Q(
                    progression__user_id=F('id'),
                    progression__finished__isnull=False
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
                )
            )
        )
        return progress


class UserManager(UserManager):

    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)

    def with_progress(self):
        return self.get_queryset().with_progress()
