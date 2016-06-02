"""Functionality for pulling information from PS and converting to JSON"""

from six.moves.urllib.request import urlopen
import json

import js2py


def _scrape(url, entry, destination_filename=None):
    """
    Pulls javascript from the specified URL, extracts the requested entry
    and returns it as a JSON string. Optionally writes said JSON string to
    the requested file

    Args:
        url (str): the location of the javascript file on the PS Github
            (url following ``master/``) or the full url to the file
        entry (str): the ``exports`` entry we seek to extract
        destination_filename (Optional(str)): if specified, the JSON string
            will be written to this file

    Returns:
        str: the JSON string representation of the requested data

    """
    url_prefix = \
        "https://raw.githubusercontent.com/Zarel/Pokemon-Showdown/master/"
    if not url.startswith('https'):
        url = url_prefix + url
    prerun = 'exports={}; '
    postrun = 'JSON.stringify(exports.'+entry+', null, 2)'
    javascript = urlopen(url).read().decode('utf-8')

    json_string = js2py.eval_js(prerun+javascript+postrun)

    if destination_filename:
        with open(destination_filename, 'w+') as out_file:
            out_file.write(json_string)

    return json_string


def scrape_formats():
    """
    Grabs rulesets for the various metagames and saves it as formats.json.
    Useful for extracting, say, banlists for non-standard tiers.

    Returns:
        list(dict): the data encoded in formats.js (each entry in the list
            is a different metagame)

    Examples:
        >>> from smogonusage import scrapers
        >>> formats = scrapers.scrape_formats()
        >>> for metagame in formats:
        ...    if metagame['name'] == 'LC':
        ...        print(metagame['maxLevel'])
        ...        break
        ...
        5
    """
    url = 'config/formats.js'
    entry = 'Formats'
    filename = 'resources/formats.json'
    return json.loads(_scrape(url, entry, filename))


def scrape_battle_formats_data():
    """
    Grabs data including tier information for Pokemon. Useful for extracting
    banlists for the standard tiers.

    Returns:
        dict: the data encoded in formats-data.js. The keys are the species
            names

    Examples:
        >>> from smogonusage import scrapers
        >>> battle_formats = scrapers.scrape_battle_formats_data()
        >>> print(battle_formats['bulbasaur']['tier'])
        LC
    """
    url = 'data/formats-data.js'
    entry = 'BattleFormatsData'
    filename = 'resources/formats-data.json'
    return json.loads(_scrape(url, entry, filename))


def scrape_battle_pokedex():
    """
    Grabs data including base stats, types, and appearance-only form info.

    Returns:
        dict: the data encoded in pokedex.js. The keys are the species
            names

    Examples:
        >>> from smogonusage import scrapers
        >>> pokedex = scrapers.scrape_battle_pokedex()
        >>> print(pokedex['bulbasaur']['baseStats']['hp'])
        45
    """

    url = 'data/pokedex.js'
    entry = 'BattlePokedex'
    filename = 'resources/pokedex.json'
    return json.loads(_scrape(url, entry, filename))


def scrape_battle_aliases():
    """
    Grabs Pokemon aliases.

    Returns:
        dict: the data encoded in aliases.js. The keys are the alternate names,
            the values are the correct names.

    Examples:
        >>> from smogonusage import scrapers
        >>> aliases = scrapers.scrape_battle_aliases()
        >>> print(aliases['forry'])
        Forretress
    """

    url = 'data/aliases.js'
    entry = 'BattleAliases'
    filename = 'resources/aliases.json'
    return json.loads(_scrape(url, entry, filename))
