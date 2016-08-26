"""Common utilities used across the package"""
from __future__ import print_function, division

import collections
import hashlib
import json
import re

import pkg_resources
import six

from onix.dto import Moveset, Forme, PokeStats


class Sanitizer(object):
    """
    An object which normalizes inputs to ensure consistency, removing or
    replacing invalid characters and de-aliasing

    Args:
        pokedex (dict) : the Pokedex to use, scraped from Pokemon Showdown
        aliases (dict) : the alias lookup to use, scraped from Pokemon
            Showdown
    """

    # Translation: any non-"word" character or "_"
    filter_regex = re.compile(r'[\W_]+')

    def __init__(self, pokedex, aliases):

        self.aliases = aliases.copy()
        for pokemon in pokedex.keys():
            if 'otherForms' in pokedex[pokemon].keys():
                for form in pokedex[pokemon]['otherForms']:
                    self.aliases[self._sanitize_string(form)] = pokemon

    def sanitize(self, input_object):
        """
        Sanitizes the given object, sorting it, removing or replacing invalid
        characters, and de-aliasing, as required
        Args:
            input_object (object) : the object to sanitize

        Returns:
            object : the sanitized object, of the same type as the input

        Raises:
            TypeError : if the type of the ``input_object`` is not supported

        Examples:
            >>> import json
            >>> from onix import scrapers
            >>> from onix import utilities
            >>> try:
            ...    pokedex = json.load(open('.psdata/pokedex.json'))
            ... except IOError:
            ...     pokedex = scrapers.scrape_battle_pokedex()
            ...
            >>> try:
            ...     aliases = json.load(open('.psdata/aliases.json'))
            ... except IOError:
            ...     aliases = scrapers.scrape_battle_aliases()
            ...
            >>> sanitizer = utilities.Sanitizer(pokedex, aliases)
            >>> sanitizer.sanitize('Wormadam-Trash')
            'wormadamtrash'
            >>> sanitizer.sanitize(['Volt Switch', 'Thunder', 'Giga Drain'
            ... , 'Web'])
            ['gigadrain', 'stickyweb', 'thunder', 'voltswitch']
        """
        if input_object is None:
            sanitized = input_object

        elif isinstance(input_object, six.string_types):
            sanitized = self._sanitize_string(input_object)
            if sanitized in self.aliases.keys():
                sanitized = self._sanitize_string(self.aliases[sanitized])
                if six.PY2: # pragma: no cover
                    sanitized = sanitized.encode('ascii')

        elif isinstance(input_object, Moveset):
            sanitized_dict = self.sanitize(input_object._asdict())
            sanitized = Moveset(**sanitized_dict)

        elif isinstance(input_object, Forme):
            sanitized_dict = self.sanitize(input_object._asdict())
            sanitized = Forme(**sanitized_dict)

        elif isinstance(input_object, dict):
            sanitized = dict()
            for key in input_object.keys():
                try:
                    sanitized[key] = self.sanitize(input_object[key])
                except TypeError:  # if the value can't be sanitized, leave it
                    sanitized[key] = input_object[key]

        elif isinstance(input_object, collections.Iterable):
            sanitized = sorted([self.sanitize(item) for item in input_object])

        else:
            raise TypeError("Sanitizer: cannot sanitize {0}"
                            .format(type(input_object)))
        return sanitized

    @classmethod
    def _sanitize_string(cls, input_string):
        """
        Strips all non-alphanumeric characters and puts everything in lowercase

        Args:
            input_string (str): string to be sanitized

        Returns:
            str: the sanitized string

        """
        return cls.filter_regex.sub('', input_string).lower()


def compute_sid(moveset, sanitizer=None):
    """
    Computes the Set ID for the given moveset

    Args:
        moveset (Moveset): the moveset to compute the SID for
        sanitizer (:obj:`Sanitizer`, optional): if no sanitizer is provided,
            ``moveset`` is assumed to be already sanitized. Otherwise, the
            provided ``Sanitizer`` is used to sanitize the moveset.
        hackmons (:obj:`bool`, optional): set to `True` if this is for a
            metagame where Pokemon can start in

    Returns:
        str: the corresponding Set ID

    Examples:
        >>> from onix.dto import PokeStats, Forme, Moveset
        >>> from onix import utilities
        >>> moveset = Moveset([Forme('mamoswine','thickfat',
        ...                          PokeStats(361,394,197,158,156,259))],
        ...                   'f', 'lifeorb',
        ...                   ['earthquake', 'iceshard', 'iciclecrash',
        ...                    'superpower'], 100, 255)
        >>> print(utilities.compute_sid(moveset)) #doctest: +ELLIPSIS
        ad9a9fa20...

    """
    if sanitizer is not None:
        moveset = sanitizer.sanitize(moveset)

    moveset_hash = hashlib.sha512(repr(moveset).encode('utf-8')).hexdigest()

    # may eventually want to truncate hash, e.g.
    # moveset_hash = moveset_hash[:16]

    return moveset_hash


def compute_tid(team, sanitizer=None):
    """
    Computes the Team ID for the given group of movesets

    Args:
        team (:obj:`iterable` of :obj:`Moveset`): the team for which to compute
            the TID
        sanitizer (:obj:`Sanitizer`, optional): if no sanitizer is provided, all
            movesets are assumed to be already sanitized. Otherwise, the
            provided ``Sanitizer`` is used to sanitize the movesets.

    Returns:
        str: the corresponding Team ID
    """
    sids = sorted([compute_sid(moveset, sanitizer)
                   for moveset in team])
    team_hash = hashlib.sha512(repr(sids).encode('utf-8')).hexdigest()

    # may eventually want to truncate hash, e.g.
    # team_hash = team_hash[:16]

    return team_hash


def stats_dict_to_dto(stats_dict):
    """
    Converts a Pokemon Showdown-style stats ``dict`` to a ``PokeStats`` DTO.

    Args:
        stats_dict (dict): the object to convert

    Returns:
        PokeStats: the converted object

    Raises:
        TypeError: if ``stats_dict`` doesn't have the correct keys

    Examples:
        >>> from onix import utilities
        >>> utilities.stats_dict_to_dto({'hp': 361, 'atk': 394, 'def': 197,
        ... 'spa': 158, 'spd' : 156, 'spe': 259})
        PokeStats(hp=361, atk=394, dfn=197, spa=158, spd=156, spe=259)
    """
    stats_dict = stats_dict.copy()
    stats_dict['dfn'] = stats_dict.pop('def')
    return PokeStats(**stats_dict)


def calculate_stats(base_stats, nature, ivs, evs, level):
    """
    Calculate a Pokemon's battle stats

    Args:
        base_stats (PokeStats): the Pokemon's base stats
        nature (dict): the nature, with ``plus`` and ``minus`` keys indicating
            the stats that are boosted and hindered (neutral natures will have
            neither key)
        ivs (PokeStats): the Pokemon's individual values
        evs (PokeStats): the Pokemon's effort values
        level (int): the Pokemon's level

    Returns:
        PokeStats: the Pokemon's battle stats

    Examples:
        >>> from onix.dto import PokeStats
        >>> from onix import utilities
        >>> utilities.calculate_stats(PokeStats(108, 130, 95, 80, 85, 102),
        ... {'name': 'Adamant', 'plus': 'atk', 'minus': 'spa'},
        ... PokeStats(24, 12, 30, 16, 23, 5),
        ... PokeStats(74, 195, 86, 48, 84, 23), 78)
        PokeStats(hp=289, atk=279, dfn=192, spa=135, spd=171, spe=171)
    """
    stats = dict()
    if base_stats.hp == 1:  # Shedinja
        stats['hp'] = 1
    else:
        stats['hp'] = (base_stats.hp * 2 + ivs.hp + evs.hp // 4 + 100)\
                      * level // 100 + 10

    for stat in ('atk', 'dfn', 'spa', 'spd', 'spe'):
        stats[stat] = (getattr(base_stats, stat) * 2 + getattr(ivs, stat) +
                       getattr(evs, stat) // 4) * level // 100 + 5

    if 'plus' in nature.keys() or 'minus' in nature.keys():
        # we want it to throw an error if the nature is invalid
        stats[nature['plus']] = int(stats[nature['plus']]*1.1)
        stats[nature['minus']] = int(stats[nature['minus']] * 0.9)

    return PokeStats(**stats)


def load_natures():
    """
    Loads the natures dictionary

    Returns:
        dict: the natures dictionary

    Examples:
        >>> from onix import utilities
        >>> natures = utilities.load_natures()
        >>> print(natures['mild']['minus'])
        dfn
    """
    json_string = pkg_resources.resource_string('onix.resources',
                                                'natures.json').decode('utf-8')
    return json.loads(json_string)


def load_accessible_formes():
    """
    Loads the dictionary of accessible formes

    Returns:
        dict: the accessible formes dictionary

    Examples:
        >>> from onix import utilities
        >>> accessible_formes = utilities.load_accessible_formes()
        >>> print(accessible_formes['charizardmegax'][0][1][0])
        charizardmegay
    """
    json_string = pkg_resources.resource_string('onix.resources',
                                                'accessible_formes.json')\
        .decode('utf-8')
    return json.loads(json_string)


def parse_ruleset(ruleset):
    """
    Extract information from a ruleset dict (an entry from `formats.json`)
    that's relevant to log reading / stat summing, etc.

    Args:
        ruleset (dict): the entry from `formats.json` corresponding to the
            format of interest

    Returns:
        tuple :
            - (str) : what's the game type? That is, `'singles'` vs. `'doubles'`
            vs. whatever
            - (bool) : is it a Hackmons metatame?
            - (bool) : are illegal species / ability combos allowed?
            - (bool) : is Rayquaza allowed to mega-evolve in the metagame?
                .. note::
                   If Rayquaza is banned from the metagame, this is trivial
                   (and will probably return True)

    Examples
        >>> import json
        >>> from onix import scrapers
        >>> from onix import utilities
        >>> try:
        ...     formats = json.load(open('.psdata/formats.json'))
        ... except IOError:
        ...     formats = scrapers.scrape_battle_formats()
        >>> print(utilities.parse_ruleset(formats['nu']))
        ('singles', False, False, True)
        >>> print(utilities.parse_ruleset(formats['almostanyability']))
        ('singles', False, True, True)
        >>> print(utilities.parse_ruleset(formats['doublesuu']))
        ('doubles', False, False, True)
    """
    # defaults
    game_type = 'singles'
    hackmons = True
    any_ability = False
    mega_rayquaza_allowed = True

    if 'gameType' in ruleset.keys():
        game_type = str(ruleset['gameType'])
    if 'Standard' in ruleset['ruleset'] \
            or 'Standard Doubles' in ruleset['ruleset']:
        hackmons = False
    if 'banlist' in ruleset.keys():
        if 'Illegal' in ruleset['banlist']:
            hackmons = False
        if 'Ignore Illegal Abilities' in ruleset['banlist']:
            any_ability = True
    if 'Mega Rayquaza Clause' in ruleset['ruleset']:
        mega_rayquaza_allowed = False

    if hackmons:
        any_ability = True

    return game_type, hackmons, any_ability, mega_rayquaza_allowed


def determine_hidden_power_type(ivs):
    """
    Determine a Pokemon's Hidden Power type from its IVs. One should never
    need to do this (PS automatically detemines the type and puts it in the
    moveset), but it's best to be sure

    Args:
        ivs (PokeStats): The Pokemon's individual values

    Returns:
        str : hidden power type

    Examples:
        >>> from onix import utilities as utl
        >>> from onix.dto import PokeStats
        >>> utl.determine_hidden_power_type(PokeStats(31, 31, 31, 31, 31, 31))
        'dark'
        >>> utl.determine_hidden_power_type(PokeStats(31, 0, 30, 31, 31, 31))
        'ice'

    """
    type_index = 15 * (ivs.hp % 2 + 2 * (ivs.atk % 2) + 4 * (ivs.dfn % 2) + 8 *
                       (ivs.spe % 2) + 16 * (ivs.spa % 2)
                       + 32 * (ivs.spd % 2)) // 63
    return ['fighting', 'flying', 'poison', 'ground', 'rock', 'bug', 'ghost',
            'steel', 'fire', 'water', 'grass', 'electric', 'psychic', 'ice',
            'dragon', 'dark'][type_index]
