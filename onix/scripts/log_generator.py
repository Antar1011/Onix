"""Generate mock logs for ease of testing"""
import json
import random

from onix import scrapers
from onix import utilities

from onix.dto import Moveset, PokeStats
from onix.collection.log_reader import _normalize_hidden_power


def _generate_random_ev_list():
    """Generate random EV spread where all EVs are multiples of 4 and are
    less than 255

    Returns:
        :obj:`list` of `int` :
            The 6 EV values
    """

    while True:
        ev_line = [random.randrange(127) for _ in range(5)]
        ev_line = [0] + sorted(ev_line) + [127]

        ev_list = [4*(ev_line[i+1] - ev_line[i]) for i in range(6)]
        if max(ev_list) < 255:
            break

    return ev_list


def generate_pokemon_dict(species, pokedex, formats_data, accessible_formes,
                          natures, sanitizer,
                          level=100, hackmons=False, any_ability=False):
    """
    Randomly generate a Showdown-style Pokemon dict for the given species

    Args:
        species (str) : species or forme name
        pokedex (dict) : data including base stats, species abilities and forme
            info, scraped from Pokemon Showdown
        formats_data (dict) : formats data parsed from PS
            (used to get random moves)
        accessible_formes (dict) : the accessible formes dictionary
        natures (dict) : the natures dictionary
        sanitizer (Sanitizer) : a sanitizer for normalizing the moveset
        level (:obj:`int`, optional) : the Pokemon's desired level.
            Default is 100.
        hackmons (:obj:`bool`, optional) :
            Set to True if this is for a metagame where a battle forme or mega
            evolution can appear outside its base forme. Default is False.
        any_ability (:obj:`bool`, optional) :
            Set to True if the Pokemon can have have "illegal" abilities.
            Default is False.

    Returns:
        (tuple) :
            * dict : A Showdown-style Pokemon dict of the specified species
            * Moveset : The corresponding moveset that should be parsed
    """

    ability_pool = list(pokedex[species]['abilities'].values())
    move_pool = formats_data[species]['randomBattleMoves']
    item_pool = ['leftovers', 'lifeorb', 'focussash', 'choiceband',
                 'choicescarf', 'choicespecs', 'rockyhelmet']
    natures_pool = list(natures.keys())

    ability = random.choice(ability_pool)
    gender = 'u'
    item = sanitizer.sanitize(formats_data[species].get(
        'requiredItem', random.choice(item_pool)))

    moves = random.sample(move_pool, min(4, len(move_pool)))

    if 'return' not in moves:
        happiness = 255
    else:
        happiness = 0

    nature = random.choice(natures_pool)

    stats = ['hp', 'atk', 'def', 'spa', 'spd', 'spe']
    iv_list = [random.randrange(32) for _ in range(6)]
    ev_list = _generate_random_ev_list()

    iv_dict = {stats[i]: iv_list[i] for i in range(6)}
    ev_dict = {stats[i]: ev_list[i] for i in range(6)}

    ivs = PokeStats(*iv_list)
    evs = PokeStats(*ev_list)

    pokemon_dict = {
        'species': pokedex[species]['species'],
        'name': pokedex[species]['species'],
        'ability': ability,
        'nature': natures[nature]['name'],
        'item': item,
        'moves': _normalize_hidden_power(moves, ivs),
        'ivs': iv_dict,
        'evs': ev_dict,
        'level': level,
    }
    if happiness != 255:
        pokemon_dict['happiness'] = happiness

    formes = [forme._replace(stats=utilities.calculate_stats(forme.stats,
                                                             natures[nature],
                                                             ivs, evs, level))
              for forme in utilities.get_all_formes(species, ability, item,
                                                    moves, pokedex,
                                                    accessible_formes,
                                                    sanitizer, hackmons,
                                                    any_ability)]

    moveset = sanitizer.sanitize(Moveset(formes, gender, item, moves,
                                         level, happiness))

    return pokemon_dict, moveset
