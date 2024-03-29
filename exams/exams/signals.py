from functools import wraps

from django.db.models import Count, Q
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Exam, Question, Variant


def disable_for_loaddata(signal_handler):
    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if kwargs.get('raw'):
            return
        signal_handler(*args, **kwargs)
    return wrapper


@receiver(post_save, sender=Question)
@receiver(post_delete, sender=Question)
@disable_for_loaddata
def exam_update_revision(sender, instance, **kwargs):
    if (instance.exam.active and instance.exam.visibility):
        instance.exam.revision = timezone.now()
        instance.exam.save()


@receiver(post_save, sender=Variant)
@receiver(post_delete, sender=Variant)
@disable_for_loaddata
def question_active_change(sender, instance, **kwargs):
    empty_status = instance.exam.empty_answers
    active = False
    if empty_status:
        variants_count = instance.question.variants.count()
        active = variants_count > 0
    else:
        variants = instance.question.variants.filter(correct=True)
        active = variants.exists()
    instance.question.active = active
    instance.question.save()
    active = instance.exam.questions.filter(
        active=True, visibility=True).exists()
    instance.exam.active = active
    instance.exam.save()


@receiver(post_save, sender=Question)
@receiver(post_delete, sender=Question)
@disable_for_loaddata
def exam_active_change(sender, instance, **kwargs):
    empty_status = instance.exam.empty_answers
    active = False
    exam_active = instance.exam.questions.filter(
        active=True, visibility=True).exists()
    if instance.variants.count():
        if (
            instance.one_correct
            and instance.variants.filter(correct=True).count() == 1
        ):
            active = True
        elif instance.text_answer:
            variants = instance.variants.filter(correct=True)
            active = variants.exists()
        elif instance.many_correct:
            if empty_status:
                active = True
            else:
                variants = instance.variants.filter(correct=True)
                active = variants.exists()
    Question.objects.filter(id=instance.id).update(active=active)
    instance.exam.active = exam_active
    instance.exam.save()


@receiver(pre_save, sender=Exam)
@disable_for_loaddata
def exam_empty_answers_change(sender, instance, **kwargs):
    if instance.id is None:
        return
    previous_stage = Exam.objects.get(id=instance.id)
    if previous_stage.empty_answers != instance.empty_answers:
        active = False
        questions = (
            instance.questions
            .prefetch_related('variants')
            .annotate(
                corrected_count=Count(
                    'variants__correct',
                    filter=Q(variants__correct=True)
                )
            )
            .filter(
                type='many_correct',
                variants__isnull=False,
                corrected_count=0
            )
            .distinct()
        )
        if instance.empty_answers:
            active = True
        questions.update(active=active)


@receiver(post_save, sender=Exam)
@disable_for_loaddata
def exam_active_self_change(sender, instance, **kwargs):
    active = False
    questions = Question.objects.filter(
        exam=instance.id, active=True, visibility=True)
    if questions.exists():
        active = True
    Exam.objects.filter(id=instance.id).update(active=active)
