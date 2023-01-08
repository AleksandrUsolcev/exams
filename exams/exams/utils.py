def get_humanize_time(minutes):
    if minutes < 60:
        humanize_time = f'{minutes} мин.'
    else:
        str_ = '{:02d} ч. {:02d} мин.'
        humanize_time = str_.format(*divmod(minutes, 60))
    return humanize_time
