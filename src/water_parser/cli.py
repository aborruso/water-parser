from bs4 import BeautifulSoup
import click
import datetime
import logging
import os
import re
import sys


logger = logging.getLogger(__name__)

DAYS = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
MONTHS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
          'septembre', 'octobre', 'novembre', 'décembre']
RE_DAYS = f"({'|'.join(DAYS)})"
RE_MONTHS = f"({'|'.join(MONTHS)})"
ODYSSI_DATE_PARSER = re.compile(rf'^(.*) du {RE_DAYS} ([0-3][0-9]) {RE_MONTHS} ([0-9]{{4}})$')
ODYSSI_INTERVAL_PARSER = re.compile(rf'(.*) du {RE_DAYS} ([0-3][0-9]) {RE_MONTHS}'
                                    rf' au {RE_DAYS} ([0-3][0-9]) {RE_MONTHS} ([0-9]{{4}})$')

ODYSSI_EXCUSES = [
    "ODYSSI met tout en œuvre",
    "ODYSSI prie ses abonnés",
    "ODYSSI s'excuse",
]


def read(f):
    with open(f, 'r') as input:
        page = input.read()
    return page


def french_date_to_date(day_name, day, month_name, year):
    month = MONTHS.index(month_name)
    if month < 0:
        raise f'Date {day_name} {day} {month_name} {year} looks wrong.'
    return datetime.datetime.strptime(f'{year}-{month + 1:02d}-{day}', '%Y-%m-%d').date()


def parse_event_period(soup):
    title = soup.article.find("h2").contents[0].string
    data = []
    if (m := ODYSSI_DATE_PARSER.match(title)):
        date_from = french_date_to_date(m.group(2), m.group(3), m.group(4), m.group(5))
        date_to = date_from
    elif (m := ODYSSI_INTERVAL_PARSER.match(title)):
        date_from = french_date_to_date(m.group(2), m.group(3), m.group(4), m.group(8))
        date_to = french_date_to_date(m.group(5), m.group(6), m.group(7), m.group(8))
    else:
        raise ValueError(f"Unexpected format: {title}")
    if date_from > date_to:
        """
        We have 6 cases [277, 345, 471, 1008, 1301, 1331], most look human error and one is from a year change.
        We keep the first date (date_to).
        """
        date_from = date_to
    return (date_from, date_to)


def identify_reason(full_soup):
    title = full_soup.article.find("h3").get_text()
    messy_text = str(full_soup.article)
    """
    Text is within <p> but sometimes also within multiple <div>
    """
    raw = messy_text[
        messy_text.index('alt="A dynamiser">-->') + len('alt="A dynamiser">-->'):
        messy_text.index('</div><!-- .wysiwyg.cut-article -->')
    ]
    soup = BeautifulSoup(raw, 'html.parser')
    infos = []
    full = soup.get_text().replace('\t', ' ').replace(u'\xa0', '').replace('’', "'")
    reasons = {
        'casse': 0,
        'travaux': 0,
        'secheresse': 0,
        'meteo': 0,
        'approvisionnement': 0
    }
    for r in ["circulation sera alternée", "fête"]:
        if r in full or r in title:
            return False
    for r in ["casse", "rupture", "incident", "dysfonctionnement", "dommages", "problème technique",
              "case réseau", "problème sur le réservoir", "en raison d'une coupure",
              "problème de réservoir", "problème de surpresseur"]:
        if r in full:
            reasons['casse'] = 1
    for r in ["réparation", "travaux", "travau",  # travau in travaux, but it's for the #shame
              "lavage", "entretien", "raccordement", "recherche de fuite", "sectorisation"]:
        if r in full:
            reasons['travaux'] = 1
    for r in ["sécheresse", "sècheresse", "secheresse", "pénurie"]:
        if r in full:
            reasons['secheresse'] = 1
    for r in ["approvisionnement", "remplissage", "baisse du niveau du réservoir", "approvisionner",
              "difficultés de production", "problème de distribution", "usines de production",
              "pas suffisamment alimenté", "problèmes de production", "niveau bas du réservoir",
              "continuent à se remplir", "problème sur le réseau d'adduction",
              "problème d'alimentation de réservoir"]:
        if r in full:
            reasons['approvisionnement'] = 1
    for r in ["intempéries", "intemperies", "conditions météorologiques", "pluies",
              "conditions climatiques", "glissement de terrain"]:
        if r in full:
            reasons['meteo'] = 1

    for prio in ['secheresse', 'meteo', 'casse', 'travaux', 'approvisionnement']:
        if reasons[prio] == 1:
            return prio
    return 'unknown'


def parse(content):
    """
    If the content was properly formatted, we could do it nicer.
    """
    soup = BeautifulSoup(content, 'html.parser')
    if soup.article is None:
        return None
    period = parse_event_period(soup)
    reason = identify_reason(soup)
    if reason is False:
        return None
    return (period, reason)


@click.command()
@click.option('--input_file', default=None, type=str, help="local html file to parse")
@click.option('--input_dir', default=None, type=str, help="local dir to parse")
@click.option('--output_dir', default=None, type=str, help="local dir to output")
@click.option('--print', 'print_activated', is_flag=True, help="print results on console")
@click.option('--debug', is_flag=True, help="Turn on debug logging")
def main(input_file, input_dir, output_dir, print_activated:bool, debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=level)

    files = set()
    if input_dir:
        files |= set([os.path.join(input_dir, f) for f in os.listdir(input_dir)])
    if input_file:
        files.add(input_file)

    res = []
    for f in files:
        if f.split('/')[-1] in ['221', '222', '223', '257', '525']:
            """
            Fucked year:
            - 221: lundi 02 septembre au mercredi 31 décembre 1969
            - 222: lundi 18 février au mercredi 31 décembre 1969
            - 223: vendredi 27 juin au mercredi 31 décembre 1969
            Inverted and long period:
            - 257: lundi 06 octobre au mardi 31 mars 2015
            - 525: jeudi 01 octobre au jeudi 31 mars 2016
            """
            continue
        try:
            parsed = parse(read(f))
        except ValueError as e:
            logging.debug(f)
            logging.debug(e)
            pass
        if not parsed:  # data should be ignored
            logging.debug(f)
            continue
        period, reason = parsed
        res.append((period, reason))

    if output_dir is None or print_activated:
        print("period_from\tperiod_to\treason")
        for (period, reason) in res:
            print(f"{period[0]}\t{period[1]}\t{reason}")

    if output_dir is not None:
        output_file_period = os.path.join(output_dir, "odyssi_periods.csv")
        output_file_day = os.path.join(output_dir, "odyssi_days.csv")
        with open(output_file_period, 'wt') as out_period, open(output_file_day, 'wt') as out_day:
            out_period.write("period_from,period_to,reason\n")
            out_day.write("day,reason\n")
            for (period, reason) in res:
                out_period.write(f"{period[0]},{period[1]},{reason}\n")
                for delta in range((period[1] - period[0]).days + 1):
                    out_day.write(f"{period[0] + datetime.timedelta(days=delta)},{reason}\n")


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
