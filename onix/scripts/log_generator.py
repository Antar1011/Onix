"""Generate mock logs for ease of testing"""
import json
import random

from onix import scrapers
from onix.dto import Moveset


def generate_pokemon_dict(species, pokedex, formats_data):
    """
    Randomly generate a Showdown-style Pokemon dict for the given species

    Args:
        species (str) : species or forme name
        pokedex (dict) : data including base stats, species abilities and forme
            info, scraped from Pokemon Showdown
        formats_data (dict) : formats data parsed from PS
            (used to get random moves)

    Returns:
        (tuple) :
            * dict : A Showdown-style Pokemon dict of the specified species
            * Moveset : The corresponding moveset that should be parsed
    """
