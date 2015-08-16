import re


def get_time_period(row):
    tp_obj = {}
    # get days of week
    tp_obj['days'] = re.sub(r'HOR\s\d-', '', re.search(r'HOR\s\d-[A-Z]+\s', row).group(0)).strip()

    # get start and end times
    time_period = re.search(r'\d{2}:\d{2}[AMP]{2}-\d{2}:\d{2}[AMP]{2}', row)
    if time_period:
        time_period = time_period.group(0).split('-')
        tp_obj['start_time'] = time_period[0]
        tp_obj['end_time'] = time_period[1]
    else:
        tp_obj['start_time'] = None
        tp_obj['end_time'] = None

    # get building
    building = re.search(r'EDIF-\d+\s', row)
    if building:
        building = re.sub(r'EDIF-', '', building.group(0)).strip()
        if building:
            tp_obj['building'] = building
    else:
        tp_obj['building'] = None

    # get classroom
    classroom = re.search(r'SALON-.+', row)
    if classroom:
        classroom = re.sub(r'SALON-', '', classroom.group(0)).strip()
        if classroom:
            tp_obj['classroom'] = classroom
    else:
        tp_obj['classroom'] = None

    return tp_obj


def get_instructor(row):
    if re.search(r'SE\sANUNCIARA', row):
        return None
    else:
        return re.sub(r'(INSTRUCTOR\s:|\.)', '', row).strip()


def get_note(row):
    note = {}
    note['id'] = int(re.sub(r'NOTA\s', '', re.search(r'NOTA\s\d', row).group(0)))
    note['text'] = re.sub(r'NOTA\s\d:', '', row).strip()
    return note


def get_no_aceptara(row):
    return row[row.find(':')+1:].strip()


def get_reserve(row):
    return row[row.find(':')+1:].strip()


def get_max(row):
    return int(re.sub(r'MAXIMO\s=', '', re.search(r'MAXIMO\s=\s\d{3}', row).group(0)).strip())


def get_co_requisitos(row):
    row = re.sub(r'CO-REQUISITOS\s:', '', row).strip()
    return re.findall(r'[A-Z]{4}-\d{4}', row)


def get_pre_requisitos(row, last):
    if last:
        row = re.sub(r'\s*', '', row).strip()
        row = re.sub(r'\.', '', row).strip()
        arr = re.split(r'\)', row)
        final_arr = []
        for i, e in enumerate(arr):
            if e:
                final_arr.append({'id': i, 'course': e})
        return final_arr
    else:
        row = re.sub(r'PRE-REQUISITOS\s:', '', row).strip()
        row = re.sub(r'\s*', '', row).strip()
        row = re.sub(r'\.', '', row).strip()
        arr = re.split(r'\)', row)
        final_arr = []
        for i, e in enumerate(arr):
            if e:
                final_arr.append({'id': i, 'course': e})
        return final_arr
