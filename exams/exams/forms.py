from django import forms
from django.forms import ValidationError

from progress.models import UserAnswer, UserVariant


class ExamProcessForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(ExamProcessForm, self).__init__(*args, **kwargs)
        self.answered = self.initial.get('answered')

        if self.answered:
            return

        self.question = self.initial.get('question')
        self.progress = self.initial.get('progress')
        self.user = self.initial.get('user')
        self.variants = self.initial.get('variants')

        if self.question.exam.shuffle_variants:
            self.variants = self.variants.order_by('?')

        self.corrected = self.variants.filter(
            correct=True).values_list('id', flat=True)
        self.add_variants_fields(self.variants)

    def add_variants_fields(self, variants_list: list) -> None:
        if self.question.many_correct:
            for variant in variants_list:
                self.fields[str(variant.id)] = forms.BooleanField(
                    label=variant.text,
                    required=False
                )

        if self.question.one_correct:
            RADIOS = []
            for variant in variants_list:
                RADIOS.append((str(variant.id), variant.text))
            self.fields['result'] = forms.ChoiceField(
                widget=forms.RadioSelect,
                choices=RADIOS,
            )

    def clean(self):
        v_count = [v for v in self.cleaned_data.values() if v is False]

        if (
            self.question.many_correct
            and len(v_count) == len(self.cleaned_data.keys())
                and self.question.exam.empty_answers is False
        ):
            raise ValidationError('Выберите хотя бы один вариант ответа')
        return self.cleaned_data

    def add_results(
            self,
            results: list,
            correct: bool,
            no_answers: bool = False
    ) -> None:
        answer = UserAnswer.objects.create(
            progress=self.progress,
            question=self.question,
            question_text=self.question.text,
            correct=correct,
            no_answers=no_answers
        )
        for_create = []

        for variant in self.variants:
            selected = False
            corrected = False

            if variant.id in results:
                selected = True

            if variant.id in self.corrected:
                corrected = True

            for_create.append(
                UserVariant(
                    answer=answer,
                    variant=variant,
                    variant_text=variant.text,
                    selected=selected,
                    correct=corrected,
                )
            )
        UserVariant.objects.bulk_create(for_create)

    def answer_with_one_correct(self):
        correct = True
        result = [int(self.cleaned_data.get('result'))]
        variant = self.variants.filter(id=result[0], correct=True)

        if not variant.exists():
            correct = False

        if result:
            self.add_results(result, correct)

    def answer_with_many_correct(self):
        correct = True
        results = []

        for variant_id in self.cleaned_data:
            status = self.cleaned_data.get(variant_id)
            if status is True:
                results.append(int(variant_id))

        if self.question.exam.empty_answers and not results:
            variants = self.variants.filter(
                question=self.question,
                correct=True
            )
            if variants.exists():
                correct = False
            self.add_results(results, correct, no_answers=True)

        uncorrects = self.variants.filter(id__in=results, correct=False)
        corrects_count = self.variants.filter(
            question=self.question,
            correct=True
        ).count()

        if uncorrects.exists() or len(results) < corrects_count:
            correct = False

        if results:
            self.add_results(results, correct)
