def get_humanize_time(minutes):
    if minutes < 60:
        humanize_time = f'{minutes} мин.'
    else:
        str_ = '{:02d} ч. {:02d} мин.'
        humanize_time = str_.format(*divmod(minutes, 60))
    return humanize_time


def get_next_exam_in_sprint(exam: object) -> object or None:
    exams_in_sprint = list(
        exam.sprint.exams.all().order_by('priority', '-created')
    )
    exam_index = exams_in_sprint.index(exam)

    if exam_index < len(exams_in_sprint) - 1:
        next_exam = exams_in_sprint[exam_index + 1]
    else:
        next_exam = None

    return next_exam


def get_previous_exam_in_sprint(exam: object) -> object or None:
    exams_in_sprint = list(
        exam.sprint.exams.all().order_by('priority', '-created')
    )
    exam_index = exams_in_sprint.index(exam)

    if exam_index > 0:
        next_exam = exams_in_sprint[exam_index - 1]
    else:
        next_exam = None

    return next_exam
