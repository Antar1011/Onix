"""Common utilities used across the package"""
from __future__ import print_function, division

import collections
import hashlib
import json
import re

import pkg_resources
import six

from smogonusage import scrapers
from smogonusage.dto import Moveset, PokeStats


class Sanitizer(object):

    filter_regex = re.compile('[\W_]+')  # Translation: any non-"word" character
                                         # or "_"

    def __init__(self, pokedex=None, aliases=None):
        """
        An object which normalizes inputs to ensure consistency, removing or
        replacing invalid characters and de-aliasing

        Args:
            pokedex (Optional[dict]): the Pokedex to use. If none is specified
                will attempt to load from file, and if the file doesn't exist
                will scrape it from the Pokemon Showdown github
            aliases (Optional[dict]): the aliases used by Pokemon Showdown. If
                none is specified will attempt to load from file, and if the
                file doesn't exist will scrape it from the Pokemon Showdown
                github
        """
        if pokedex is None:
            try:
                pokedex = json.load(open('.psdata/pokedex.json'))
            except IOError:
                pokedex = scrapers.scrape_battle_pokedex()

        if aliases is None:
            try:
                aliases = json.load(open('.psdata/aliases.json'))
            except IOError:
                aliases = scrapers.scrape_battle_aliases()

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
            input_object (object): the object to sanitize

        Returns:
            object: the sanitized object, of the same type as the input

        Raises:
            TypeError: if the type of the ``input_object`` is not supported

        Examples:
            >>> from smogonusage import utilities
            >>> sanitizer = utilities.Sanitizer()
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
                if six.PY2:
                    sanitized = sanitized.encode('ascii')

        elif isinstance(input_object, Moveset):
            sanitized_dict = self.sanitize(input_object._asdict())
            sanitized = Moveset(**sanitized_dict)

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
        sanitizer (Optional[Sanitizer]): if no sanitizer is provided,
            ``moveset`` is assumed to be already sanitized. Otherwise, the
            provided ``Sanitizer`` is used to sanitize the moveset.

    Returns:
        str: the corresponding Set ID

    Examples:
        >>> from smogonusage.dto import PokeStats, Moveset
        >>> from smogonusage import utilities
        >>> moveset = Moveset('Mamoswine', 'Thick Fat', 'F', 'Life Orb',
        ... ['Ice Shard', 'Icicle Crash', 'Earthquake', 'Superpower'],
        ... PokeStats(361,394,197,158,156,259), 100, 255)
        >>> equivalent = Moveset('mamo', 'thickfat', 'f', 'lorb',
        ... ['eq', 'IcicleCrash', 'superpower', 'iceshard'],
        ... PokeStats(361,394,197,158,156,259), 100, 255)
        >>> different = Moveset('mamo', 'thickfat', 'f', 'focus sash',
        ... ['eq', 'IcicleCrash', 'superpower', 'iceshard'],
        ... PokeStats(361,394,197,158,156,259), 100, 255)
        >>> sanitizer=utilities.Sanitizer()
        >>> moveset_sid = utilities.compute_sid(moveset, sanitizer)
        >>> moveset_sid # doctest: +ELLIPSIS
        'mamoswine-4a0b...'
        >>> equivalent_sid = utilities.compute_sid(equivalent, sanitizer)
        >>> equivalent_sid
        'mamoswine-4a0b...'
        >>> different_sid = utilities.compute_sid(different, sanitizer)
        >>> different_sid
        'mamoswine-bb16...'
        >>> moveset_sid == equivalent_sid
        True
        >>> moveset_sid == different_sid
        False
    """
    if sanitizer is not None:
        moveset = sanitizer.sanitize(moveset)

    moveset_hash = hashlib.sha512(repr(moveset).encode('utf-8')).hexdigest()

    # may eventually want to truncate hash, e.g.
    # moveset_hash = moveset_hash[:16]

    return '{0}-{1}'.format(moveset.species, moveset_hash)


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
        >>> from smogonusage import utilities
        >>> utilities.stats_dict_to_dto({'hp': 361, 'atk': 394, 'def': 197,
        ... 'spa': 158, 'spd' : 156, 'spe': 259})
        PokeStats(hp=361, atk=394, dfn=197, spa=158, spd=156, spe=259)
    """
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
        >>> from smogonusage.dto import PokeStats
        >>> from smogonusage import utilities
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
    """Loads the natures dictionary

    Returns:
        dict: the natures dictionary

    Examples:
        >>> from smogonusage import utilities
        >>> natures = utilities.load_natures()
        >>> print(natures['mild']['minus'])
        dfn
    """
    json_string = pkg_resources.resource_string('smogonusage.resources',
                                                'natures.json').decode('utf-8')
    return json.loads(json_string)
