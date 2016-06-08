# Smogon-Usage-Stats: Rewrite
When I started this project, I was a grad student who'd only ever written
academic code (where if it runs, no one really cares what it looks like or how
it's written). I used this project to teach myself Python, and I knew not one
iota of the principles of good software development. Five years later, I have
grown so much as a programmer, a software developer and a data scientist, and
frankly, I'm unhappy with the status of this codebase. Yes, the scripts work
(for the most part), and keeping everything running has so far not been too
onerous, but when I look at this repo, and I just feel *embarrassed*. I can do
better. And I feel that I owe it to myself *to* do better.

Just as I wrote the original Smogon Usage Stats scripts to learn how to code
Python, I'm now going to perform a complete rewrite as an opportunity to learn
how to code Python *well*. That means:
  * adhering to PEP 8 and other Python best-practices
  * writing modular, reusable, easy-to-maintain code
  * writing covering tests that ensure robust performance and easy
  troubleshooting

None of this is likely to improve performance significantly, but I also have
plans to write versions of the scripts that leverage databases (ideally I'll
have both an RMDBS (MySQL) and a NoSQL (MongoDB) implementation) that should
increase performance dramatically, meaning improved time-to-stats and possibly
an API for performing deep analyses that go beyond the detailed moveset stats.

##Design Decisions
 * Handle package / dependency management using
 [Anaconda/Miniconda](https://www.continuum.io/why-anaconda)
 * Maintain compatibility with both Python 2.7+ and 3.5+
    * Should also be compatible with PyPy (meaning no NumPy)
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