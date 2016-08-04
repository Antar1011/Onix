"""Functionality for pulling information from PS and converting to JSON"""
from __future__ import print_function

import copy
import json
import os
from six.moves.urllib.request import urlopen

from py_mini_racer.py_mini_racer import MiniRacer


def _write(data, destination_filename):
    """
    Helper method to write data to file

    Args:
        data (str) : the data to be written
        destination_filename (str) : filename to save to
    """
    directory = os.path.dirname(destination_filename)
    try:
        os.makedirs(directory)
    except OSError:
        if not os.path.isdir(directory):
            raise  # pragma: no cover

    with open(destination_filename, 'w+') as out_file:
        out_file.write(data)


def _scrape(url, entry, destination_filename=None):
    """
    Pulls javascript from the specified URL, extracts the requested entry
    and returns it as a JSON string. Optionally writes said JSON string to
    the requested file

    Args:
        url (str) : the location of the javascript file on the PS Github
            (url following ``master/``) or the full url to the file
        entry (str) : the ``exports`` entry we seek to extract
        destination_filename (Optional[str]): if specified, the JSON string
            will be written to this file

    Returns:
        str : the JSON string representation of the requested data

    """
    url_prefix = \
        "https://raw.githubusercontent.com/Zarel/Pokemon-Showdown/master/"
    if not url.startswith('https'):
        url = url_prefix + url
    prerun = 'exports={}; '
    postrun = 'JSON.stringify(exports.'+entry+', null, 2)'
    javascript = urlopen(url).read().decode('utf-8')

    json_string = MiniRacer().eval(prerun+javascript+postrun)

    if destination_filename:
        _write(json_string, destination_filename)

    return json_string


def scrape_battle_formats_data():
    """
    Grabs data including tier information for Pokemon. Useful for extracting
    banlists for the standard tiers.

    Returns:
        dict : the data encoded in `formats-data.js`. The keys are the species
        names

    Examples:
        >>> from onix import scrapers
        >>> battle_formats = scrapers.scrape_battle_formats_data()
        >>> print(battle_formats['bulbasaur']['tier'])
        LC
    """
    url = 'data/formats-data.js'
    entry = 'BattleFormatsData'
    filename = '.psdata/formats-data.json'
    return json.loads(_scrape(url, entry, filename))


def scrape_battle_pokedex():
    """
    Grabs data including base stats, types, and appearance-only form info.

    Returns:
        dict : the data encoded in `pokedex.js`. The keys are the species
        names

    Examples:
        >>> from onix import scrapers
        >>> pokedex = scrapers.scrape_battle_pokedex()
        >>> print(pokedex['bulbasaur']['baseStats']['hp'])
        45
    """

    url = 'data/pokedex.js'
    entry = 'BattlePokedex'
    filename = '.psdata/pokedex.json'
    return json.loads(_scrape(url, entry, filename))


def scrape_battle_aliases():
    """
    Grabs Pokemon aliases.

    Returns:
        dict : the data encoded in `aliases.js`. The keys are the alternate
        names, the values are the correct names.

    Examples:
        >>> from onix import scrapers
        >>> aliases = scrapers.scrape_battle_aliases()
        >>> print(aliases['forry'])
        Forretress
    """

    url = 'data/aliases.js'
    entry = 'BattleAliases'
    filename = '.psdata/aliases.json'
    return json.loads(_scrape(url, entry, filename))


def scrape_battle_items():
    """
    Grabs items. Used for determining mega evolutions and for pretty-print
    lookups.

    Returns:
        dict : the data encoded in `items.js`

    Examples:
        >>> from onix import scrapers
        >>> items = scrapers.scrape_battle_items()
        >>> print(items['gardevoirite']['megaEvolves'])
        Gardevoir
    """

    url = 'data/items.js'
    entry = 'BattleItems'
    filename = '.psdata/items.json'
    return json.loads(_scrape(url, entry, filename))


def scrape_battle_movedex():
    """
    Grabs move names. Manually scrapes `moves.js` and just pulls the names,
    because js2py can't seem to execute `moves.js`

    Returns:
        dict : the move names from `moves.js`. The keys are the sanitized
        move names, the values are the pretty-printed move names.

    Examples:
        >>> from onix import scrapers
        >>> moves = scrapers.scrape_battle_movedex()
        >>> print(moves['scald'])
        Scald
    """

    url = "https://raw.githubusercontent.com/Zarel/Pokemon-Showdown/master/" \
          "data/moves.js"
    javascript = urlopen(url).read().decode('utf-8')
    destination_filename = '.psdata/moves.json'

    moves = dict()
    current = [None, None]
    for line in javascript.split('\n'):
        line = line.strip()
        split = line.split(':')
        if split[0] == 'id':
            current[0] = split[1].strip()[1:-2]
        elif split[0] == 'name':
            current[1] = split[1].strip()[1:-2]
        else:
            continue  # pragma: no cover
        if current[0] is not None and current[1] is not None:
            moves[current[0]] = current[1]
            current = [None, None]

    if destination_filename:
        with open(destination_filename, 'w+') as out_file:
            out_file.write(json.dumps(moves, indent=4))

    return moves


def scrape_formats():
    """
    Grabs rulesets for the various metagames and saves it as `formats.json`.
    Useful for extracting, say, banlists for non-standard tiers. Does a bit
    of post-processing to transform the data from a list to a dict and to expand
    out any inherited rulesets

    Returns:
        dict : the data encoded in `formats.js`, post-processed for increased
        utility

    Examples:
        >>> from onix import scrapers
        >>> formats = scrapers.scrape_formats()
        >>> print(formats['LC']['maxLevel'])
        5
    """
    url = 'config/formats.js'
    entry = 'Formats'
    raw_data = json.loads(_scrape(url, entry))

    formats = dict()
    for metagame in raw_data:

        # expand out rulesets
        if 'ruleset' in metagame.keys():  # I think this is always True
            for rule in copy.deepcopy(metagame['ruleset']):
                if rule in formats.keys():
                    metagame['ruleset'].remove(rule)
                    metagame['ruleset'] += formats[rule].get('ruleset', [])

        formats[metagame['name']] = metagame

    json_string = json.dumps(formats, indent=4)
    filename = '.psdata/formats.json'
    _write(json_string, filename)

    return formats

