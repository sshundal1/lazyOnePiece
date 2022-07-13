import click
import animdl
import logging
import requests
import re
import regex
from animdl.core.cli.helpers.processors import process_query
from animdl.core.cli.helpers.searcher import search_9anime, search_animepahe, search_allanime, search_animixplay
from animdl.core.cli.http_client import client
from animdl.core.cli.helpers import ensure_extraction

from animdl.core.codebase.providers import get_appropriate

session = client


def animdl_search(name):
    nine_anime_results = search_animixplay(session, name)

    search_results = [item for item in nine_anime_results]

    search_buffer = {i['name']: i['anime_url'] for i in search_results}
    print(search_results)
    return search_results


def get_range_conditions(range_string):
    for matches in regex.finditer(r"(?:([0-9]*)[:\-.]([0-9]*)|([0-9]+))", range_string):
        start, end, singular = matches.groups()
        if start and end and int(start) > int(end):
            start, end = end, start
        yield (lambda x, s=singular: int(s) == x) if singular else (
            lambda x: True
        ) if not (start or end) else (
            lambda x, s=start: x >= int(s)
        ) if start and not end else (
            lambda x, e=end: x <= int(e)
        ) if not start and end else (
            lambda x, s=start, e=end: int(s) <= x <= int(e)
        )


def get_check(range_string):
    if not range_string:
        return lambda *args, **kwargs: True
    return lambda x: any(
        condition(x) for condition in get_range_conditions(range_string)
    )



if __name__ == '__main__':
    name = 'One Piece'
    results = animdl_search(name)
    stream_links = {}

    for result in results:
        if result['name'] == name:
            anime_url = result['anime_url']

    for stream_url_caller, episode in get_appropriate(session, anime_url,
                                                      get_check("398 399 400 401 402 403 404 405")):
        stream_url = list(ensure_extraction(session, stream_url_caller))

        all_stream_urls = requests.get(stream_url[-1]['stream_url']).text
        split_urls = all_stream_urls.splitlines()

        for i in range(0, len(split_urls), 1):
            if re.findall(r"RESOLUTION=1920x1080", split_urls[i]):
                stream_links[episode] = split_urls[i+1]
                break


    print(stream_links[398])
    meow = requests.get(stream_links[398])
    print(meow.headers.get('content-type'))

    open('OnePieceEpisode398.m3u8', 'wb').write(meow.content)