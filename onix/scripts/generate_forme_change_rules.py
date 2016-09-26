"""Generate the config file that lists which Pokemon can change formes. While
we're at it, generate the species lookup dictionary that handles prettifying
species names, labelling forme-concatenations and combining appearance-only
formes"""

import json
import re

from collections import defaultdict

from future.utils import iteritems

from onix import scrapers


def generate_single_forme_species_lookup():
    """
    Generate the species lookup for single formes (that is, combine
    appearance-only formes)

    Returns:
        dict :
            Starting point for species_lookup dictionary (that is, without
            forme-concatenations)
    """
    try:
        pokedex = json.load(open('.psdata/pokedex.json'))
    except IOError:
        pokedex = scrapers.scrape_battle_pokedex()

    # to start, prettify using PS rules
    species_lookup = {pokemon : pokedex[pokemon]['species']
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

    filter_regex = re.compile('[\W_]+')

    accessible_formes = {}
    species_lookup = generate_single_forme_species_lookup()

    # first the megas
    for item, attributes in iteritems(items):
        if 'megaStone' not in attributes:
            continue
        start_forme = filter_regex.sub('', attributes['megaEvolves']).lower()
        end_forme = filter_regex.sub('', attributes['megaStone']).lower()

        if start_forme not in accessible_formes.keys():
            accessible_formes[start_forme] = []
        accessible_formes[start_forme].append(({'item': item}, [end_forme]))

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
    accessible_formes.update(accessible_hackmons_formes)

    # the rest is, unfortunately, manual
    castforms = ['castform{0}'.format(forme) for forme in ['', 'sunny', 'snowy',
                                                           'rainy']]
    for castform in castforms:
        accessible_formes[castform] = [({'ability': 'forecast'},
                                        [forme for forme in castforms if
                                         castform != forme])]

    accessible_formes['cherrim'] = [({'ability': 'flowergift'},
                                     ['cherrimsunshine'])]
    accessible_formes['cherrimsunshine'] = [({'ability': 'flowergift'},
                                             ['cherrim'])]

    accessible_formes['darmanitan'] = [({'ability': 'zenmode'},
                                        ['darmanitanzen'])]
    accessible_formes['darmanitanzen'] = [({'ability': 'zenmode'},
                                           ['darmanitan'])]

    accessible_formes['meloetta'] = [({'move': 'relicsong'},
                                      ['meloettapirouette'])]
    accessible_formes['meloettapirouette'] = [({'move': 'relicsong'},
                                      ['meloetta'])]

    accessible_formes['aegislash'] = [({'ability': 'stancechange'},
                                       ['aegislashblade'])]
    # technically I should have checked that it has an attacking move...
    accessible_formes['aegislashblade'] = [({'ability': 'stancechange',
                                             'move': 'kingsshield'},
                                            ['aegislash'])]

    accessible_formes['rayquaza'] = [({'move': 'dragonascent'},
                                      ['rayquazamega'])]

    accessible_formes['shayminsky'] = [({}, ['shaymin'])]

    json.dump(accessible_formes, open('onix/resources/accessible_formes.json',
                                      'w+'), indent=4)


if __name__ == '__main__':
    main()
