from django.db.models import (Count, ExpressionWrapper, F, IntegerField,
                              Manager, Prefetch, Q, QuerySet)
from django.db.models.functions.comparison import NullIf


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
                    NullIf(Count('answers', filter=Q(
                        answers__correct=True), distinct=True), 0) * 100 /
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
