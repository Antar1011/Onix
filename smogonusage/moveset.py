"""Module containing the Moveset class"""
import hashlib
import json

from smogonusage import utilities


class Moveset(object):

    def __init__(self, species, gender, ability, item, moves, stats,
                 level=100, happiness=255, sanitizer=None):
        """
        A Moveset contains all the competitively distinct elements of the
        Pokemon. Things like nicknames, appearance-only variations, move order,
        and extra EVs are ignored.

        Args:
            species (str): the species of Pokemon
            gender (char): the Pokemon's gender (m, f or None)
            ability (str): the Pokemon's ability
            item (str): the item the Pokemon is holding (use None for no item)
            moves (list of str): the Pokemon's moves
            stats (dict of str to int): the Pokemon's ``Battle stats,`` that is,
                the actual stats the Pokemon hass, derived from base stats,
                IVs and EVs
            level (Optional[int]): the Pokemon's level (default: 100)
            happiness (Optional[int]): the Pokemon's happiness (default: 255)
            sanitizer (Optional(Sanitizer)): the sanitizer to use to normalize
                the Moveset. If none is specified, the Moveset will not be
                normalized and the hash will be computed assuming that
                everything's already normalized.

        Raises
            ValueError if an invalid gender is specified
        """
        if sanitizer is not None:
            species = sanitizer.sanitize(species)
            ability = sanitizer.sanitize(ability)
            item = sanitizer.sanitize(item)
            moves = sanitizer.sanitize(moves)

        self.species = species
        if gender is not None:
            gender = gender.lower()
            if gender not in ('m', 'f'):
                raise ValueError('Moveset: Gender must be m, f or None')
        self.gender = gender.lower()
        self.ability = ability
        self.item = item
        self.moves = moves
        self.stats = stats
        self.level = level
        self.happiness = happiness
        self.sid = self._compute_sid()

    def _compute_sid(self):
        """
        Movesets are mostly referred to by their ``set ID,`` which is
        auto-generated based on the moveset. In this case, it's the moveset's
        hash

        Returns:
            str: string representation of the moveset's hash, to be used as
                a ``unique ID`` for the moveset
        """
        return hashlib.sha1(json.dumps(dict(species=self.species,
                                            ability=self.ability,
                                            gender=self.gender,
                                            item=self.item,
                                            moves=self.moves,
                                            stats=self.stats,
                                            level=self.level,
                                            happiness=self.happiness),
                                       sort_keys=True).encode('utf-8')
                            ).hexdigest()
