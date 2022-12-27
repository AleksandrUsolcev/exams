from itertools import chain
from operator import attrgetter

from django.db.models import (BooleanField, Case, Count, ExpressionWrapper, F,
                              IntegerField, Q, When)

from .models import Exam


def get_exams_with_progress(user: object, category_slug: str) -> object:
    if user.is_authenticated:
        query_with_user_progress = Exam.objects.filter(
            category__slug=category_slug,
            progress__user=user,
            visibility=True,
            active=True
        ).prefetch_related('progress').annotate(
            questions_count=Count('questions', filter=(
                Q(category__slug=category_slug) &
                Q(progress__user=user) &
                Q(questions__visibility=True) &
                Q(questions__active=True))
            ),
            current_stage=F('progress__stage'),
            passed=Case(
                When(progress__passed__isnull=False, then=True),
                output_field=BooleanField()
            ),
            percentage=ExpressionWrapper(
                F('progress__answers') * 100 / Count('questions', filter=(
                    Q(category__slug=category_slug) &
                    Q(progress__user=user) &
                    Q(questions__visibility=True) &
                    Q(questions__active=True))
                ),
                output_field=IntegerField()
            )
        )

        query_without_user = Exam.objects.filter(
            Q(category__slug=category_slug) &
            ~Q(id__in=query_with_user_progress),
            visibility=True,
            active=True
        ).annotate(
            questions_count=Count('questions', filter=(
                Q(category__slug=category_slug) &
                ~Q(id__in=query_with_user_progress) &
                Q(questions__visibility=True) &
                Q(questions__active=True))
            )
        )

        queryset = sorted(
            list(chain(query_without_user, query_with_user_progress)),
            key=attrgetter('created'), reverse=True
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
