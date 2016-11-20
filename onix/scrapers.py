"""Functionality for pulling information from PS and converting to JSON"""
from __future__ import print_function

import copy
import json
import os

import pkg_resources

from future.moves.urllib.request import urlopen

from py_mini_racer.py_mini_racer import MiniRacer

from onix.utilities import sanitize_string


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
        dict : the data encoded in `formats-data.js`. The keys are the species /
        forme names

    Examples:
        >>> from onix import scrapers
        >>> battle_formats = scrapers.scrape_battle_formats_data()
        >>> print(battle_formats['bulbasaur']['tier'])
        LC
    """
    url = 'data/formats-data.js'
    entry = 'BattleFormatsData'
    filename = '.psdata/formats_data.json'
    return json.loads(_scrape(url, entry, filename))


def scrape_battle_pokedex():
    """
    Grabs data including base stats, types and appearance-only form info, then
    does a little bit of post-processing to unlink Pokemon that cannot move
    between formes during battle (e.g.: Rotom-Wash)

    Returns:
        dict : the data encoded in `pokedex.js`. The keys are the species /
        forme names

    Examples:
        >>> from onix import scrapers
        >>> pokedex = scrapers.scrape_battle_pokedex()
        >>> print(pokedex['bulbasaur']['baseStats']['hp'])
        45
    """

    url = 'data/pokedex.js'
    entry = 'BattlePokedex'
    filename = '.psdata/pokedex.json'
    pokedex = json.loads(_scrape(url, entry))
    baseable_formes = pkg_resources.resource_string('onix.resources',
                                                    'baseable_formes.txt'
                                                    ).decode('utf-8'
                                                             ).splitlines()
    for species in pokedex.keys():
        if 'baseSpecies' not in pokedex[species]:
            continue
        if species.endswith(('mega', 'megax', 'megay')):
            # intentionally left off primal
            continue
        if species not in baseable_formes:
            del pokedex[species]['baseSpecies']

    _write(json.dumps(pokedex, indent=4), filename)
    return pokedex


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


def scrape_battle_abilities():
    """
    Grabs abilities. Used for pretty-print
    lookups.

    Returns:
        dict : the data encoded in `abilities.js`

    Examples:
        >>> from onix import scrapers
        >>> items = scrapers.scrape_battle_abilities()
        >>> print(abilties['shadowshield']['name'])
        Shadow Shield
    """

    url = 'data/abilties.js'
    entry = 'BattleAbilities'
    filename = '.psdata/abilities.json'
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
    Grabs move metadata.

    Returns:
        dict : the data encoded in `moves.js`

    Examples:
        >>> from onix import scrapers
        >>> moves = scrapers.scrape_battle_movedex()
        >>> print(moves['scald']['name'])
        Scald
    """

    url = "https://raw.githubusercontent.com/Zarel/Pokemon-Showdown/master/" \
          "data/moves.js"
    javascript = urlopen(url).read().decode('utf-8')
    destination_filename = '.psdata/moves.json'

    url = 'data/moves.js'
    entry = 'BattleMovedex'
    filename = '.psdata/moves.json'
    return json.loads(_scrape(url, entry, filename))


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
        >>> print(formats['lc']['maxLevel'])
        5
    """

    url = 'config/formats.js'
    entry = 'Formats'
    filename = '.psdata/formats.json'
    raw_data = json.loads(_scrape(url, entry))

    formats = dict()
    for metagame in raw_data:

        # expand out rulesets
        if 'ruleset' in metagame.keys():  # I think this is always True
            for rule in copy.deepcopy(metagame['ruleset']):
                rule_sanitized = sanitize_string(rule)
                if rule_sanitized in formats.keys():
                    metagame['ruleset'].remove(rule)
                    metagame['ruleset'] += formats[rule_sanitized].get(
                        'ruleset', [])

        formats[sanitize_string(metagame['name'])] = metagame

    _write(json.dumps(formats, indent=4), filename)

    return formats
