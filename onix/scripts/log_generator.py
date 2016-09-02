"""Generate mock logs for ease of testing"""
import datetime
import hashlib
import random
import re

from onix import contexts
from onix import metrics
from onix import utilities

from onix.dto import Moveset, PokeStats, Player
from onix.collection.log_reader import get_all_formes, normalize_hidden_power


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


def generate_pokemon(species, context,
                     level=100, hackmons=False, any_ability=False):
    """
    Randomly generate a Showdown-style Pokemon dict and the corresponding
    `Moveset` DTO for the given species

    Args:
        species (str) : species or forme name
        context (contexts.Context) : The resources needed by the function.
            Requires pokedex, formats_data, accessible_formes, natures and
            sanitizer.
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
    contexts.require(context, 'pokedex', 'formats_data', 'accessible_formes',
                     'natures', 'sanitizer')

    ability_pool = list(context.pokedex[species]['abilities'].values())
    move_pool = context.formats_data[species]['randomBattleMoves']
    item_pool = ['leftovers', 'lifeorb', 'focussash', 'choiceband',
                 'choicescarf', 'choicespecs', 'rockyhelmet']
    natures_pool = list(context.natures.keys())

    ability = random.choice(ability_pool)
    gender = 'u'
    item = context.sanitizer.sanitize(context.formats_data[species].get(
        'requiredItem', random.choice(item_pool)))

    moves = random.sample(move_pool, min(4, len(move_pool)))

    if 'return' not in moves:
        happiness = 255
    else:
        happiness = 0

    nature = random.choice(natures_pool)

    stats = ('hp', 'atk', 'def', 'spa', 'spd', 'spe')
    iv_list = [random.randrange(32) for _ in range(6)]
    ev_list = _generate_random_ev_list()

    iv_dict = dict(zip(stats, iv_list))
    ev_dict = dict(zip(stats, ev_list))

    ivs = PokeStats(*iv_list)
    evs = PokeStats(*ev_list)

    pokemon_dict = {
        'species': context.pokedex[species]['species'],
        'name': context.pokedex[species]['species'],
        'ability': ability,
        'nature': context.natures[nature]['name'],
        'item': item,
        'moves': _normalize_hidden_power(moves, ivs),
        'ivs': iv_dict,
        'evs': ev_dict,
        'level': level,
    }
    if happiness != 255:
        pokemon_dict['happiness'] = happiness

    formes = [forme._replace(
        stats=utilities.calculate_stats(forme.stats, context.natures[nature],
                                        ivs, evs, level))
              for forme in get_all_formes(species, ability, item,
                                                    moves, context, hackmons,
                                                    any_ability)]

    moveset = context.sanitizer.sanitize(Moveset(formes, gender, item, moves,
                                         level, happiness))

    return pokemon_dict, moveset


def generate_player(name, ratings=None):
    """
    Generate a Showdown-style player's rating dict and the corresponding
    `Player` DTO for the given species

    Args:
        name (str) : the player's name
        ratings (:obj:`dict`, optional) : the rating values for the player.
            Missing values will be randomly generated. Defaults to having all
            values randomly generated

    Returns:
        (tuple) :
            * dict : A Showdown-style ratings dict for the specified player
            * Player : The corresponding DTO that should be parsed
    """

    if ratings is None:
        ratings = {}

    pid = ratings.get('userid', re.compile(r'[\W_]+')
                      .sub('', name).lower())
    w = ratings.get('w', random.randrange(100))
    l = ratings.get('l', random.randrange(100))
    t = ratings.get('t', random.randrange(10))
    elo = ratings.get('elo', random.uniform(1000., 1700.))
    r = ratings.get('r', random.uniform(1000., 2000.))
    rd = ratings.get('rd', random.uniform(25., 130.))
    rpr = ratings.get('rpr', r + random.uniform(-25, 25))
    rprd = ratings.get('rprd', rd - random.uniform(0, 25))

    rating_dict = dict(elo=elo,
                       formatid=ratings.get('format', 'randombattle'),
                       l=l, r=r, rd=rd,  rpr=rpr, rprd=rprd,
                       rpsigma=ratings.get('rpsigma', 0),
                       rptime=ratings.get('rptime',
                                          int(datetime.datetime.now()
                                              .strftime("%s"))),
                       sigma=ratings.get('sigma', 0),
                       t=t, userid=pid, username=name, w=w)

    rating_dict['col1'] = ratings.get('col1', rating_dict['w']
                                      + rating_dict['l'] + rating_dict['t']
                                      + random.randrange(20))
    rating_dict['userid'] = pid
    rating_dict['entryid'] = ratings.get('entryid',
                                         int(hashlib.sha512('{0}{1}'.format(
                                             rating_dict['formatid'],
                                             rating_dict['userid'])
                                                            .encode('utf-8'))
                                             .hexdigest()[:7], 16))
    rating_dict['gxe'] = ratings.get('gxe',
                                     metrics.gxe(rating_dict['r'],
                                                 rating_dict['rd']))
    rating_dict['oldelo'] = ratings.get('oldelo', rating_dict['elo']
                                        + random.uniform(-25, 25))

    player = Player(pid, dict(w=w, l=l, t=t, elo=elo,
                              r=r, rd=rd, rpr=rpr, rprd=rprd))

    return rating_dict, player


def generate_log(players, teams, turns=None, end_type=None):
    """
    Generate a mock log.

    Args:
        players (:obj:`list` of :obj:`dict`) :
            The rating dictionaries of the players in the match
        teams (:obj:`list` of :obj:`list` of :obj:`dict`) :
            The Pokemon dictionaries for each player's team. Must have same
            length as `players`.
        turns (:obj:`int`, optional) :
            Number of turns in the battle. Default is a random value.
        end_type (:obj:`str`, optional) :
            End type. Default is "normal"

    Returns:
        dict :
            The mock log

    """

    if len(players) != len(teams):
        raise ValueError('players list and teams list must have same length')

    log = dict(endType=end_type or 'normal',
               log="If you are trying to parse this, "
                   "something has gone horribly wrong",
               seed=[random.randrange(65535) for _ in range(4)],
               turns=turns or random.randrange(128))

    for i in range(len(players)):
        log['p{0}'.format(i+1)] = players[i]['username']
        log['p{0}team'.format(i+1)] = teams[i]
        log['p{0}rating'.format(i+1)] = players[i]
    return log
