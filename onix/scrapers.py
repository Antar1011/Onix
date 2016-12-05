"""Functionality for pulling information from PS and converting to JSON"""
from __future__ import print_function

import copy
import datetime
import json
import os

import pkg_resources

from future.moves.urllib.request import urlopen
from github import Github
from py_mini_racer.py_mini_racer import MiniRacer

from onix.utilities import sanitize_string


def get_commit_from_timestamp(timestamp):
    """
    Get the PS commit hash corresponding to the last commit to master as of the
    specified timestamp

    Args:
        timestamp (datetime.datetime) : The date and time (in UTC) desired

    Returns:
        str :
            The commit has correspond to the last commit to master as of the
            specified timestamp

    Examples:
        >>> from datetime import datetime
        >>> from onix.scrapers import get_commit_from_timestamp
        >>> print(get_commit_from_timestamp(datetime(2016, 12, 1, 5, 0)))
        841d4c9e135d07d7affb725bf42f81df376b2de1
    """
    g = Github()
    ps = g.get_repo('Zarel/Pokemon-Showdown')
    return ps.get_commits(until=timestamp).get_page(0)[0].sha


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

    json.dump(json.loads(data), open(destination_filename, 'w+'))


def _scrape(url, entry, commit=None, destination_filename=None):
    """
    Pulls javascript from the specified URL, extracts the requested entry
    and returns it as a JSON string. Optionally writes said JSON string to
    the requested file

    Args:
        url (str) : the location of the javascript file on the PS Github
            (url following ``master/``) or the full url to the file
        entry (str) : the ``exports`` entry we seek to extract
        commit (:obj:`str`, optional): if specified, will pull the version of
            the file as of the commit specified by this full hash.

            .. note::
              If a full url is specified in the `url` field, this argument will
              be ignored.

        destination_filename (:obj:`str`, optional): if specified, the JSON
        string will be written to this file

    Returns:
        str : the JSON string representation of the requested data

    """
    url_prefix = \
        "https://raw.githubusercontent.com/Zarel/Pokemon-Showdown/"
    if commit:
        url_prefix += '{}/'.format(commit)
    else:
        url_prefix += 'master/'
    if not url.startswith('https'):
        url = url_prefix + url
    prerun = 'exports={}; '
    postrun = 'JSON.stringify(exports.'+entry+', null, 2)'
    javascript = urlopen(url).read().decode('utf-8')

    json_string = MiniRacer().eval(prerun+javascript+postrun)

    if destination_filename:
        _write(json_string, destination_filename)

    return json_string


def scrape_battle_formats_data(commit=None):
    """
    Grabs data including tier information for Pokemon. Useful for extracting
    banlists for the standard tiers.

    Args:
        commit (:obj:`str`, optional): if specified, will pull the version of
            the file as of the commit specified by this full hash.

    Returns:
        dict : the data encoded in `formats-data.js`. The keys are the species /
        forme names

    Examples:
        >>> from onix import scrapers
        >>> commit = '5c14138b54dddf8bc034433eaef950a1c6eaf734'
        >>> battle_formats = scrapers.scrape_battle_formats_data(commit=commit)
        >>> print(battle_formats['bulbasaur']['tier'])
        LC
    """
    url = 'data/formats-data.js'
    entry = 'BattleFormatsData'
    folder = '.psdata/'
    if commit:
        folder += '{}/'.format(commit)
    filename = folder + 'formats_data.json'
    return json.loads(_scrape(url, entry, commit, filename))


def scrape_battle_pokedex(commit=None):
    """
    Grabs data including base stats, types and appearance-only form info, then
    does a little bit of post-processing to unlink Pokemon that cannot move
    between formes during battle (e.g.: Rotom-Wash)

    Args:
        commit (:obj:`str`, optional): if specified, will pull the version of
            the file as of the commit specified by this full hash.

            .. note::
              In most cases, one shouldn't need to use old versions of the
              Pokedex, as data very rarely gets overwritten or removed. If
              one is looking to pull information from a previous generation, use
              a mod, not an old commit.

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
    folder = '.psdata/'
    if commit:
        folder += '{}/'.format(commit)
    filename = folder + 'pokedex.json'
    pokedex = json.loads(_scrape(url, entry, commit))
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


def scrape_battle_aliases(commit=None):
    """
    Grabs Pokemon aliases.

    Args:
        commit (:obj:`str`, optional): if specified, will pull the version of
            the file as of the commit specified by this full hash.

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
    folder = '.psdata/'
    if commit:
        folder += '{}/'.format(commit)
    filename = folder + 'aliases.json'
    return json.loads(_scrape(url, entry, commit, filename))


def scrape_battle_abilities(commit=None):
    """
    Grabs abilities. Used for pretty-print
    lookups.

    Args:
        commit (:obj:`str`, optional): if specified, will pull the version of
            the file as of the commit specified by this full hash.

            .. note::
              In most cases, one shouldn't need to use old versions of the
              Item dex, as data very rarely gets overwritten or removed. If
              one is looking to pull information from a previous generation, use
              a mod, not an old commit.

    Returns:
        dict : the data encoded in `abilities.js`

    Examples:
        >>> from onix import scrapers
        >>> items = scrapers.scrape_battle_abilities()
        >>> print(abilties['shadowshield']['name'])
        Shadow Shield
    """

    url = 'data/abilities.js'
    entry = 'BattleAbilities'
    folder = '.psdata/'
    if commit:
        folder += '{}/'.format(commit)
    filename = folder + 'abilities.json'
    return json.loads(_scrape(url, entry, commit, filename))


def scrape_battle_items(commit=None):
    """
    Grabs items. Used for determining mega evolutions and for pretty-print
    lookups.

    Args:
        commit (:obj:`str`, optional): if specified, will pull the version of
            the file as of the commit specified by this full hash.

            .. note::
              In most cases, one shouldn't need to use old versions of the
              Item dex, as data very rarely gets overwritten or removed. If
              one is looking to pull information from a previous generation, use
              a mod, not an old commit.

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
    folder = '.psdata/'
    if commit:
        folder += '{}/'.format(commit)
    filename = folder + 'items.json'
    return json.loads(_scrape(url, entry, commit, filename))


def scrape_battle_movedex(commit=None):
    """
    Grabs move metadata.

    Args:
        commit (:obj:`str`, optional): if specified, will pull the version of
            the file as of the commit specified by this full hash.

            .. note::
              In most cases, one shouldn't need to use old versions of the
              Move dex, as data very rarely gets overwritten or removed. If
              one is looking to pull information from a previous generation, use
              a mod, not an old commit.

    Returns:
        dict : the data encoded in `moves.js`

    Examples:
        >>> from onix import scrapers
        >>> moves = scrapers.scrape_battle_movedex()
        >>> print(moves['scald']['name'])
        Scald
    """

    url = 'data/moves.js'
    entry = 'BattleMovedex'
    folder = '.psdata/'
    if commit:
        folder += '{}/'.format(commit)
    filename = folder + 'moves.json'
    return json.loads(_scrape(url, entry, commit, filename))


def scrape_formats(commit=None):
    """
    Grabs rulesets for the various metagames and saves it as `formats.json`.
    Useful for extracting, say, banlists for non-standard tiers. Does a bit
    of post-processing to transform the data from a list to a dict and to expand
    out any inherited rulesets

    Args:
        commit (:obj:`str`, optional): if specified, will pull the version of
            the file as of the commit specified by this full hash.

    Returns:
        dict : the data encoded in `formats.js`, post-processed for increased
        utility

    Examples:
        >>> from onix import scrapers
        >>> commit = '5c14138b54dddf8bc034433eaef950a1c6eaf734'
        >>> formats = scrapers.scrape_formats(commit=commit)
        >>> print(formats['lc']['maxLevel'])
        5
    """

    url = 'config/formats.js'
    entry = 'Formats'
    folder = '.psdata/'
    if commit:
        folder += '{}/'.format(commit)
    filename = folder + 'formats.json'
    raw_data = json.loads(_scrape(url, entry, commit))

    formats = dict()
    for metagame in raw_data:

        if 'name' not in metagame.keys():
            continue

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
