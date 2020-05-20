import datetime
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def _read_json(f_name):
    with open(f_name) as f:
        data = json.loads(f.read())
    return data


_CUR_DIR_ = Path(__file__).parent.resolve()
_ROOT_DIR_ = _CUR_DIR_.parent.resolve()
_TEMPLATE_FILE_ = 'template.html'
_CONTENT_FILE_ = _CUR_DIR_.joinpath('content.json')
_LABELS_FILE_ = _read_json(_CUR_DIR_.joinpath('labels.json'))


def _format_date(date):
    if not date:
        return None

    if type(date) == str:
        date = _parse_date(date)

    return datetime.datetime.strftime(date, '%b %Y')


def _parse_date(date_str):
    return datetime.datetime.strptime(date_str, '%Y-%m')


class Company:
    def __init__(self, name, website, location):
        super().__init__()
        self.name = name
        self.website = website
        self.location = location


class Position:
    def __init__(self, s_date, e_date, title):
        super().__init__()
        self.start = _format_date(s_date)

        if e_date:
            self.end = _format_date(e_date)
        else:
            self.end = 'Present'

        self.title = title


class CvRow:
    def __init__(self, period, description):
        super().__init__()
        self.period = period
        self.description = description


def _load_template():
    env = Environment(loader=FileSystemLoader(_CUR_DIR_))
    return env.get_template(_TEMPLATE_FILE_)


def _build_content():
    data = _read_json(_CONTENT_FILE_)

    content = {
        "name": data.get('name'),
        "positions": data.get('positions'),
        "limitations": data.get('limitations'),
        "summaries": data.get('summaries'),
        "contacts": _extract_contacts(data),
        "links": _extract_social_links(data),
        "languages": data.get('languages'),
        "experience": _extract_experience(data),
        "education": _extract_cv_row(data.get('education')),
        "certification": _extract_cv_row(data.get('certification')),
    }
    return content


def _extract_social_links(content):
    socials = []
    for link in content.get('links'):
        link_type = link.get('type')
        socials.append({'label': link_type, 'link': link.get('link'), 'icon': _get_icon(link_type)})

    return socials

def _get_icon(contact_type):
    if contact_type == 'LinkedIn':
        return '/img/linked-in.png'
    if contact_type == 'GitHub':
        return '/img/git-hub.png'
    if contact_type == 'HackerRank':
        return '/img/hackerrank.png'


def _extract_contacts(content):
    contacts = []
    for contact in content.get('contacts'):
        contact_type = contact.get('type')
        contact_data = contact.get('contact')
        contact_label = _LABELS_FILE_.get(contact_type)
        if not contact_label:
            contact_label = contact_type.capitalize()

        contact_link = None
        if contact_type == 'email':
            contact_link = 'mailto:' + contact_data
        elif contact_type == 'skype':
            contact_link = 'skype:{}?userinfo'.format(contact_data)
        elif contact_type == 'mobile':
            contact_link = 'call:' + contact_data

        contacts.append(
            {'label': contact_label, 'link': contact_link, 'data': contact_data})

    return contacts



def _extract_experience(content):
    result = []
    for exp_item in content.get('experience'):
        positions = []
        sorted_pos = sorted(exp_item.get('positions'),
                            key=lambda pos: pos.get('start'))

        for i, pos_item in enumerate(sorted_pos):
            positions.append(Position(
                pos_item.get('start'),
                pos_item.get('end'),
                pos_item.get('title')
            ))

        comp = exp_item.get('company')

        l_pos = positions[len(sorted_pos) - 1]
        result.append({
            'title': l_pos.title,
            'start': positions[0].start,
            'end': l_pos.end,
            'company': Company(comp.get('name'), comp.get('website'), comp.get('location')),
            'technologies': ', '.join(exp_item.get('technologies')),
            'description': exp_item.get('description')
        })
    return result


def _to_month(date):
    return date.year * 12 + date.month


def _format_duration(delta_month):
    years = int(delta_month / 12)
    delta_month = delta_month % 12
    m_format = None
    if delta_month == 0:
        m_format = ""
    elif delta_month == 1:
        m_format = str(delta_month) + " mo"
    else:
        m_format = str(delta_month) + " mos"

    if years == 1:
        return "1 yr " + m_format
    if years > 0:
        return str(years) + " yrs " + m_format

    return m_format


def _extract_cv_row(data):
    result = []
    for item in data:
        s_date = item.get('start')
        e_date = item.get('end')
        year = item.get('year')
        descr = item.get('description')
        if year:
            row = CvRow(year, descr)
        else:
            period = "{} - {}".format(
                _format_date(s_date),
                _format_date(e_date)
            )
            row = CvRow(period, descr)

        result.append(row)

    return result


if __name__ == "__main__":
    print("Preparing data")
    template = _load_template()
    content = _build_content()

    print("Rendering")
    rendered_content = template.render(content)

    print("Saving html")
    html_file = _ROOT_DIR_.joinpath('index.html')
    with open(html_file, "w") as fh:
        fh.write(rendered_content)
