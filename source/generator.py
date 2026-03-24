import datetime
import locale
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS


def _read_json(f_name):
    with open(f_name) as f:
        data = json.loads(f.read())
    return data


_CUR_DIR_ = Path(__file__).parent.resolve()
_ROOT_DIR_ = _CUR_DIR_.parent.resolve()
_STATIC_DIR_ = _ROOT_DIR_.joinpath('static')
_TEMPLATE_FILE_ = 'template.html'
_LABELS_FILE_ = _read_json(_CUR_DIR_.joinpath('labels.json'))
_SUPPORTED_LANGUAGES_ = [{'code': 'en', 'name': 'English', 'locale': 'en_US'}, {'code': 'nl', 'name': 'Nederlands', 'locale': 'nl_NL'}]  # Add your language codes


def _get_content_file(language):
    """Get the content file path for a specific language."""
    return _CUR_DIR_.joinpath(f'content.{language}.json')

def _get_lang_codes():
    """Get a list of supported language codes."""
    return [lang['code'] for lang in _SUPPORTED_LANGUAGES_]


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
            self.end = ''

        self.title = title


class CvRow:
    def __init__(self, period, description):
        super().__init__()
        self.period = period
        self.description = description


def _load_template():
    env = Environment(loader=FileSystemLoader(_CUR_DIR_))
    return env.get_template(_TEMPLATE_FILE_)


def _build_content(lang):
    """Build content for a specific language."""
    print(f"Building content for language: {lang}")
    locale.setlocale(locale.LC_TIME, lang['locale'])
    language = lang['code']
    content_file = _get_content_file(language)
    
    if not content_file.exists():
        raise FileNotFoundError(f"Content file not found for language: {language}")
    
    data = _read_json(content_file)

    content = {
        "titles": data.get('titles'),
        "name": data.get('name'),
        "positions": data.get('positions'),
        "limitations": data.get('limitations'),
        "summaries": data.get('summaries'),
        "contacts": _extract_contacts(data),
        "links": _extract_social_links(data),
        "languages": data.get('languages'),
        "experience": _extract_experience(data, lang),
        "education": _extract_cv_row(data.get('education')),
        "certification": _extract_cv_row(data.get('certification')),
        "hobbies": ", ".join(data.get('hobbies')).lower().capitalize(),
        "language": language,
        "supported_languages": _get_lang_codes()
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
        return 'img/linked-in.png'
    if contact_type == 'GitHub':
        return 'img/git-hub.png'
    if contact_type == 'HackerRank':
        return 'img/hackerrank.png'


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


def _extract_experience(content, lang):
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
            'history': " → ".join([pi.title for pi in positions]) if len(positions) > 1 else "",
            'end': l_pos.end,
            'company': Company(comp.get('name'), comp.get('website'), comp.get('location')),
            'technologies': ', '.join(exp_item.get('technologies')),
            'description': exp_item.get('description')
        })
    return result


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


def _generate_for_language(lang):
    """Generate HTML and PDF for a specific language in a separate folder."""
    language = lang['code']
    print(f"Preparing data for language: {language}")
    template = _load_template()
    content = _build_content(lang)

    print(f"Rendering for {language}")
    rendered_content = template.render(content)

    print(f"Saving HTML and PDF for {language}")
    
    # Create language-specific folder in root directory
    if language == 'en':
        # English goes to root as index.html
        html_file = _ROOT_DIR_.joinpath('index.html')
    else:
        # Other languages go to folders: /nl/, /ru/, etc.
        lang_folder = _ROOT_DIR_.joinpath(language)
        lang_folder.mkdir(exist_ok=True)
        html_file = lang_folder.joinpath('index.html')
    
    # Save HTML
    with open(html_file, "w") as fh:
        fh.write(rendered_content)
    
    print(f"HTML saved to: {html_file}")
    
    # Create static folder if it doesn't exist
    _STATIC_DIR_.mkdir(exist_ok=True)
    
    # Save PDF to static folder with naming convention
    pdf_file = _STATIC_DIR_.joinpath(f'Vlad Vinogradov {language}.pdf')
    
    try:
        HTML(string=rendered_content, base_url=_ROOT_DIR_).write_pdf(pdf_file)
        print(f"PDF saved to: {pdf_file}")
    except Exception as e:
        print(f"Error generating PDF for {language}: {e}")


if __name__ == "__main__":
    # Generate HTML and PDF for all supported languages
    for lang in _SUPPORTED_LANGUAGES_:
        try:
            _generate_for_language(lang)
        except FileNotFoundError as e:
            print(f"Warning: {e}")
    
    print("Done!")
