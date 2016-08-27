"""Generate the config file that lists which Pokemon can change formes"""
import json
import pprint
import re

import six

from onix import scrapers


def main():
    try:
        pokedex = json.load(open('.psdata/pokedex.json'))
    except IOError:
        pokedex = scrapers.scrape_battle_pokedex()
    try:
        items = json.load(open('.psdata/items.json'))
    except IOError:
        items = scrapers.scrape_battle_items()

    filter_regex = re.compile('[\W_]+')

    accessible_formes = {}

    # first the megas
    for item, attributes in six.iteritems(items):
        if 'megaStone' not in attributes:
            continue
        start_forme = filter_regex.sub('', attributes['megaEvolves']).lower()
        end_forme = filter_regex.sub('', attributes['megaStone']).lower()

        if start_forme not in accessible_formes.keys():
            accessible_formes[start_forme] = []
        accessible_formes[start_forme].append(({'item': item}, [end_forme]))

    # Charizard and Mewtwo
    accessible_hackmons_formes = {}
    for start_forme, change_paths in six.iteritems(accessible_formes):
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
