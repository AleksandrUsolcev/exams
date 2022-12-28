from itertools import chain
from operator import attrgetter

from django.db.models import (BooleanField, Case, Count, ExpressionWrapper, F,
                              IntegerField, Q, When)

from .models import Exam


def get_exams_with_progress(user: object,
                            category_slug: str,
                            without_user: bool = False
                            ) -> object:

    if user.is_authenticated and without_user:
        queryset = Exam.objects.filter(
            category__slug=category_slug,
            progress__user=user,
            progress__exam_revision=F('revision'),
            visibility=True,
            active=True
        ).prefetch_related('progress').annotate(
            questions_count=Count('questions', filter=(
                Q(category__slug=category_slug) &
                Q(progress__user=user) &
                Q(questions__visibility=True) &
                Q(questions__active=True)) &
                Q(progress__exam_revision=F('revision'))
            ),
            current_stage=F('progress__stage'),
            is_finished=Case(
                When(progress__finished__isnull=False, then=True),
                output_field=BooleanField()
            ),
            percentage=ExpressionWrapper(
                F('progress__answers_count') * 100 / Count(
                    'questions', filter=(
                        Q(category__slug=category_slug) &
                        Q(progress__user=user) &
                        Q(questions__visibility=True) &
                        Q(questions__active=True)) &
                    Q(progress__exam_revision=F('revision'))
                ),
                output_field=IntegerField()
            )
        )

        query_without_user = Exam.objects.filter(
            Q(category__slug=category_slug) &
            ~Q(id__in=queryset),
            visibility=True,
            active=True
        ).annotate(
            questions_count=Count('questions', filter=(
                Q(category__slug=category_slug) &
                ~Q(id__in=queryset) &
                Q(questions__visibility=True) &
                Q(questions__active=True))
            )
        )

        queryset = sorted(
            list(chain(query_without_user, queryset)),
            key=attrgetter('created'), reverse=True
        )
        return queryset

    elif not category_slug:
        queryset = Exam.objects.filter(
            progress__user=user,
            progress__exam_revision=F('revision'),
            visibility=True,
            active=True
        ).prefetch_related('progress').annotate(
            questions_count=Count('questions', filter=(
                Q(progress__user=user) &
                Q(questions__visibility=True) &
                Q(questions__active=True)) &
                Q(progress__exam_revision=F('revision'))
            ),
            current_stage=F('progress__stage'),
            is_finished=Case(
                When(progress__finished__isnull=False, then=True),
                output_field=BooleanField()
            ),
            percentage=ExpressionWrapper(
                F('progress__answers_count') * 100 / Count(
                    'questions', filter=(
                        Q(progress__user=user) &
                        Q(questions__visibility=True) &
                        Q(questions__active=True)) &
                    Q(progress__exam_revision=F('revision'))
                ),
                output_field=IntegerField()
            )
        )
        return queryset

    queryset = Exam.objects.filter(
        category__slug=category_slug, visibility=True, active=True).annotate(
        questions_count=Count('questions', filter=(
            Q(category__slug=category_slug) &
            Q(questions__visibility=True) &
            Q(questions__active=True)
        ))).order_by('-created')
    return queryset
