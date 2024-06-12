import re
from bs4 import BeautifulSoup
# from exceptions import NotParsedException


def parsing(content: str) -> BeautifulSoup:
    return BeautifulSoup(content, 'html.parser')


def scws(content: str) -> int:
    """ Classe per fare il parsing delle pagine web"""

    parsed = BeautifulSoup(content, 'html.parser')

    #if not parsed:
        #raise NotParsedException

    div_app = parsed.find('div', id='app')
    if not div_app:
        return 0
    data_page = div_app['data-page']
    scws_id_pattern = re.compile(r'"scws_id":(\d+)')
    scws_id_matches = scws_id_pattern.findall(data_page)
    if scws_id_matches:
        return scws_id_matches[0]



