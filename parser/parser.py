import re
import json

import requests
from bs4 import BeautifulSoup

from utils import (get_time_period, get_instructor, get_note, get_no_aceptara,
                   get_reserve, get_max, get_co_requisitos, get_pre_requisitos)


def get_data():
    base_url = 'http://www.uprb.edu'
    url = 'http://www.uprb.edu/es/academico/registro/horarioacad/horarioacad.htm'
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')

    periods = []

    results = soup.find(id='Menu Secundario').find_all('td')

    # Periods
    for e in results[1:]:
        anchor = e.find('a')
        if anchor:
            period = {}
            title = re.sub(r'\s+', ' ', anchor.text.replace('\r\n', ''))
            period['name'] = title.split('-')[0].strip()
            period['term'] = title.split('-')[1].strip()
            period['url'] = url.replace(url.split('/')[-1], '') + anchor['href']
            periods.append(period)

    # Departments
    for period in periods:
        html = requests.get(period['url']).text
        soup = BeautifulSoup(html, 'html.parser')
        departments = []
        url = period['url']

        for e in soup.find_all('table')[3].find_all('a'):
            department = {}
            department['name'] = re.sub(r'\s+', ' ', e.text.replace('\r\n', ''))
            if e['href'].startswith('/'):
                department['url'] = base_url + e['href']
            else:
                department['url'] = url.replace(url[url.rindex('/')::], '/') + e['href']
            departments.append(department)

        period['departments'] = departments

    # Courses
    for period in periods:
        print '\n' + period['name']
        print '===================='
        for department in period['departments']:
            courses = []
            dep_url = department['url']
            html = requests.get(dep_url).text
            soup = BeautifulSoup(html, 'html.parser')

            anchor = soup.find('iframe').find('a')['href']
            url = dep_url.replace(dep_url[dep_url.rindex('/')::], '/') + anchor

            html = requests.get(url).text
            soup = BeautifulSoup(html, 'html.parser')

            print department['name']

            if soup.find('body'):
                period['year'] = re.search(
                    r'\d{4}-\d{4}',
                    soup.find('h4').font.text).group(0)

                titles = soup.find('pre').font.find_all('b')
                [e.extract() for e in soup.find('pre').font.find_all('b')]
                [e.replaceWithChildren() for e in soup.find('pre').font.find_all('hr')]

                idx = 0
                for course in re.split(r'\r\n\r\n', soup.find('pre').font.text)[1:]:
                    course_obj = {}
                    header = re.sub(r'\s+', ' ', titles[idx].text.replace('\r\n', ''))
                    course_obj['id'] = re.search(r'[A-Z]{4}-\d{4}-.{3}', header).group(0)
                    header = re.sub(r'[A-Z]{4}-\d{4}-[A-Z].{3}', '', header)
                    course_obj['credits'] = re.search(r'\d+\.\d-?(\d+\.\d)?', header).group(0)
                    header = re.sub(r'\d\.\d', '', header)
                    course_obj['type'] = re.sub(r'SS', '', re.search(r'\s(LEC|LAB|INT|PRA|SEM)\sSS', header).group(0)).strip()
                    header = header[:re.finditer(r'\s(LEC|LAB|INT|PRA|SEM)\sSS', header).next().start(0)]
                    course_obj['title'] = header.strip()

                    ################## ALL ROWS ######################
                    time_periods = []
                    notes = []
                    reserves = []
                    last = ''
                    for row in course.split('\r\n'):
                        row = row.strip()

                        # check freshmen
                        if re.search(r'FRESHMEN', row):
                            course_obj['freshmen'] = True

                        # check unex
                        if re.search(r'UNEX', row):
                            course_obj['unex'] = True

                        if re.search(r'HOR\s\d', row):
                            last = 'HOR'
                            time_periods.append(get_time_period(row))
                        elif re.search(r'INSTRUCTOR', row):
                            last = 'INSTRUCTOR'
                            course_obj['instructor'] = get_instructor(row)
                        elif re.search(r'NOTA\s\d', row):
                            last = 'NOTA'
                            notes.append(get_note(row))
                        elif re.search(r'NO\sACEPTARA', row):
                            last = 'NO ACEPTARA'
                            course_obj['no-aceptara'] = get_no_aceptara(row)
                        elif re.search(r'RESERVADO\(S\)', row):
                            last = 'RESERVADO'
                            reserves.append(get_reserve(row))
                        elif re.search(r'MAXIMO', row):
                            last = 'MAXIMO'
                            course_obj['max'] = get_max(row)
                        elif re.search(r'CO-REQUISITOS', row):
                            last = 'CO-REQUISITOS'
                            course_obj['co-requisitos'] = get_co_requisitos(row)
                        elif last == 'PRE-REQUISITOS' or re.search(r'PRE-REQUISITOS', row):
                            if last == 'PRE-REQUISITOS':
                                course_obj['pre-requisitos'].extend(get_pre_requisitos(row, True))
                            else:
                                course_obj['pre-requisitos'] = get_pre_requisitos(row, False)
                            last = 'PRE-REQUISITOS'

                    if 'freshmen' not in course_obj:
                        course_obj['freshmen'] = False

                    if 'unex' not in course_obj:
                        course_obj['unex'] = False

                    if 'co-requisitos' not in course_obj:
                        course_obj['co-requisitos'] = []

                    if 'pre-requisitos' not in course_obj:
                        course_obj['pre-requisitos'] = []

                    if 'max' not in course_obj:
                        course_obj['max'] = None

                    # Add all arrays to the course object
                    course_obj['time_periods'] = time_periods
                    course_obj['notes'] = notes
                    course_obj['reserves'] = reserves

                    # clean up on pre-requisitos
                    start_idx = 0
                    zero_count = 0
                    for i, e in enumerate(course_obj['pre-requisitos']):
                        if e['id'] == 0:
                            zero_count = zero_count + 1
                        if zero_count == 2:
                            start_idx = i
                            break

                    if start_idx > 0:
                        while start_idx < len(course_obj['pre-requisitos']):
                            previous_id = course_obj['pre-requisitos'][start_idx-1]['id']
                            course_obj['pre-requisitos'][start_idx]['id'] = previous_id+1
                            start_idx = start_idx + 1

                    for e in course_obj['pre-requisitos']:
                        y_or_o = re.search(r'\(.', e['course']).group(0)[1:]
                        e['y_or_o'] = y_or_o
                        e['course'] = re.sub(r'\(.', '', e['course'])

                    courses.append(course_obj)
                    idx = idx + 1

                department['courses'] = courses
            else:
                department['courses'] = []

    with open('data.json', 'w') as outfile:
        json.dump(periods, outfile)
