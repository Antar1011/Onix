![Ride the Onix](http://img06.deviantart.net/e96e/i/2014/359/b/8/the_rock_snake_by_twime777-d8b5eu8.png)
[_Image credit: twime777 @ DeviantArt_](http://twime777.deviantart.com/art/The-Rock-Snake-502457696)

[![Build Status](https://travis-ci.org/Antar1011/Onix.svg?branch=master)](https://travis-ci.org/Antar1011/Onix)
[![Coverage Status](https://coveralls.io/repos/github/Antar1011/Onix/badge.svg?branch=master)](https://coveralls.io/github/Antar1011/Onix?branch=master)
[![Documentation Status](https://readthedocs.org/projects/onix/badge/?version=latest)](http://onix.readthedocs.io/en/latest/?badge=latest)

# Onix: the Pokemon data-mining package
When I started generating usage statistics for Smogon, I was a grad student
who'd only ever written academic code (where if it runs, no one really cares
what it looks like or how it's written). I used the project to teach myself
Python, and I knew not one iota of the principles of good software development.
Five years later, I have grown a lot as a programmer, a software developer and a
data scientist, and frankly, I became deeply unhappy with
[my old codebase](https://github.com/Antar1011/Smogon-Usage-Stats). Yes, the
scripts worked (for the most part), and keeping everything running had so far
not been too onerous, but looking at my code just made me feel *embarrassed*. I
can do better. And I feel that I owe it to myself *to* do better.

Just as I wrote the original Smogon Usage Stats scripts to learn how to code
Python, I'm now going to perform a complete rewrite as an exercise in developing
in Python *well*. That means:
  * adhering to PEP 8 and other Python best-practices
  * writing modular, reusable, easy-to-maintain code
  * writing covering tests that ensure robust performance and easy
  troubleshooting

I'm also doing work to make the codebase more performant and extensible, with
the goal of generating more analyses, quicker. This will likely involve
leveraging database infrastructures (likely a mix of RDBMS like SQLite or
MySQL and document stores such as MongoDB). I also hope to expose a public API
to allow players to dig deep and go beyond the static reports the current
scripts generate.

##Design Decisions
 * For development, handle package / dependency management using
 [Anaconda/Miniconda](https://www.continuum.io/why-anaconda)
 * Maintain compatibility with both Python 2.7+ and 3.5+
    * Should also (eventually) be compatible with PyPy (meaning no NumPy)
 * Adhere to [Google docstring style](
 http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
 * Follow PEP-8 / Pylint guidelines (including 80-character width limit)
 * Use `py.test` as the testing framework
    * Doctests should be plentiful and should function as useful examples, but
    test suites should completely cover functionality. That is: it should be
    sufficient to test everything without running doctests.
        * That being said, all doctests should pass (and should pass with all
        supported Python versions)
 * When possible, use Pokemon Showdown's config / data files. That way, when
 PS updates something (updated tiers, new Pokemon / formes / moves), it's
 trivial to pull in those changes.
 * Megas and all other special formes will be counted separately for
 log-reading. It's the responsibility of the stats counter to combine formes.
 Note that this doesn't apply to Hackmons metagames.
 * Rather than seeking to 100% reproduce PS behavior, try to match cartridge
behavior and file a bug report for anything inconsistent
