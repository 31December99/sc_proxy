# -*- coding: utf-8 -*-

from urllib.parse import urlparse


def best_resolution(media: list) -> str:
    """
    Scelgo la miglio resolution disponibile
    :param media:  contiene l'elenco dell'urls disponibile nella playlist master
    :return: l'url della migliore risolution
    """

    resolution = 0
    resolution_url = ''
    for p in media:
        print(p.uri)
        # Splitto query otteno l'intero del valore del parametro rendition
        query = (urlparse(p.uri)).query
        rendition = int((query.split('&')[1].replace("rendition=", '')).replace('p', ''))
        # Memorizzo l'ultima risoluzione disponibile se è maggiore della precedente
        if rendition > resolution:
            resolution = rendition
            resolution_url = p.uri
    return resolution_url
