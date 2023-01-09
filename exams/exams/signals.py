from django.db.models import Count, F, Q
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Exam, Question, Variant


@receiver(post_save, sender=Variant)
@receiver(post_save, sender=Question)
@receiver(post_delete, sender=Variant)
@receiver(post_delete, sender=Question)
def exam_update_revision(sender, instance, **kwargs):
    if (
        instance.exam.active and instance.exam.visibility
        and instance.exam.change_revision
    ):
        instance.exam.revision = F('revision') + 1
        instance.exam.save()


@receiver(post_save, sender=Variant)
@receiver(post_delete, sender=Variant)
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
def exam_active_change(sender, instance, raw, **kwargs):
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
def exam_active_self_change(sender, instance, **kwargs):
    active = False
    questions = Question.objects.filter(
        exam=instance.id, active=True, visibility=True)
    if questions.exists():
        active = True
    Exam.objects.filter(id=instance.id).update(active=active)
