"""Generate the config file that lists which Pokemon can change formes. While
we're at it, generate the species lookup dictionary that handles prettifying
species names, labelling forme-concatenations and combining appearance-only
formes"""

import json
import re

from collections import defaultdict

from future.utils import iteritems

from onix import scrapers
from onix.utilities import sanitize_string


def generate_single_forme_species_lookup():
    """
    Generate the species lookup for single formes (that is, combine
    appearance-only formes)

    Returns:
        dict :
            Starting point for `species_lookup` dictionary (that is, without
            forme-concatenations)
    """
    try:
        pokedex = json.load(open('.psdata/pokedex.json'))
    except IOError:
        pokedex = scrapers.scrape_battle_pokedex()

    # to start, prettify using PS rules
    species_lookup = {pokemon: pokedex[pokemon]['species']
                      for pokemon in pokedex.keys()}

    # now gather formes by dex no
    formes = defaultdict(list)
    for pokemon, entry in iteritems(pokedex):
        formes[entry['num']].append((pokemon, entry['baseStats'],
                                    entry['types']))

    # policy: formes get combined iff they have the same base stats and typing
    for num, formes in iteritems(formes):
        if len(formes) < 2:
            continue
        formes = sorted(formes, key=lambda x:len(x[0]))
        base = formes[0]
        for forme in formes[1:]:
            if base[1:] == forme[1:]:
                species_lookup[forme[0]] = species_lookup[base[0]]

    return species_lookup


def main():
    try:
        items = json.load(open('.psdata/items.json'))
    except IOError:
        items = scrapers.scrape_battle_items()

    accessible_formes = {}
    species_lookup = generate_single_forme_species_lookup()

    # first the megas
    for item, attributes in iteritems(items):
        if 'megaStone' not in attributes:
            continue
        start_forme = sanitize_string(attributes['megaEvolves'])
        end_forme = sanitize_string(attributes['megaStone'])

        if start_forme not in accessible_formes.keys():
            accessible_formes[start_forme] = []
        accessible_formes[start_forme].append(({'item': item}, [end_forme]))
        species_lookup['{0},{1}'.format(
            start_forme, end_forme)] = species_lookup[end_forme]
        # this borks Charizard/Mewtwo, but we'll fix it in a sec
        species_lookup[end_forme] = 'Mega-{0}'.format(
            species_lookup[start_forme])

    # Charizard and Mewtwo
    accessible_hackmons_formes = {}
    for start_forme, change_paths in iteritems(accessible_formes):
        if len(change_paths) < 2:
            continue
        megas = [change_path[1][0] for change_path in change_paths]
        for mega in megas:
            accessible_hackmons_formes[mega] = [change_path
                                                for change_path in change_paths
                                                if change_path[1][0] != mega]
            species_lookup[mega] = 'Mega-{0}-{1}'.format(
                species_lookup[start_forme], mega[-1].upper())

            for end_forme in [change_path[1][0]
                             for change_path
                             in accessible_hackmons_formes[mega]]:
                forme_concat = '{0},{1}'.format(mega, end_forme)
                species_lookup[forme_concat] = '{0}{1}'.format(
                    species_lookup[mega],
                    species_lookup['{0},{1}'.format(start_forme,
                                                   end_forme)][-7:])

    accessible_formes.update(accessible_hackmons_formes)

    # the rest is, unfortunately, manual
    castforms = ['castform{0}'.format(forme) for forme in ('', 'rainy', 'snowy',
                                                           'sunny')]
    for castform in castforms:
        accessible_formes[castform] = [({'ability': 'forecast'},
                                        [forme for forme in castforms if
                                         castform != forme])]

    species_lookup[','.join(castforms)] = 'Castform'

    accessible_formes['cherrim'] = [({'ability': 'flowergift'},
                                     ['cherrimsunshine'])]
    accessible_formes['cherrimsunshine'] = [({'ability': 'flowergift'},
                                             ['cherrim'])]

    species_lookup['cherrim,cherrimsunshine'] = 'Cherrim'

    accessible_formes['darmanitan'] = [({'ability': 'zenmode'},
                                        ['darmanitanzen'])]
    accessible_formes['darmanitanzen'] = [({'ability': 'zenmode'},
                                           ['darmanitan'])]

    species_lookup['darmanitan,darmanitanzen'] = 'Darmanitan-Zen'
    species_lookup['darmanitanzen'] = 'Zen-Darmanitan'

    accessible_formes['meloetta'] = [({'move': 'relicsong'},
                                      ['meloettapirouette'])]
    accessible_formes['meloettapirouette'] = [({'move': 'relicsong'},
                                      ['meloetta'])]

    species_lookup['meloetta,meloettapirouette'] = 'Meloetta'

    # note that Aegislash-Shield can always struggle
    accessible_formes['aegislash'] = [({'ability': 'stancechange'},
                                       ['aegislashblade'])]

    accessible_formes['aegislashblade'] = [({'ability': 'stancechange',
                                             'move': 'kingsshield'},
                                            ['aegislash'])]

    species_lookup['aegislash,aegislashblade'] = 'Aegislash'

    accessible_formes['rayquaza'] = [({'move': 'dragonascent'},
                                      ['rayquazamega'])]

    species_lookup['rayquaza,rayquazamega'] = 'Rayquaza-Mega'
    species_lookup['rayquazamega'] = 'Mega-Rayquaza'

    accessible_formes['shayminsky'] = [({}, ['shaymin'])]
    del species_lookup['shayminsky']
    species_lookup['shayminsky,shaymin'] = 'Shaymin-Sky'

    json.dump(accessible_formes, open('onix/resources/accessible_formes.json',
                                      'w+'), indent=4)
    json.dump(species_lookup, open('onix/resources/species_lookup.json',
                                   'w+'), indent=4)


if __name__ == '__main__':
    main()
