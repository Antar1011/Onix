# Contributor's Guide

Re-architecting Smogon's data mining apparatus is an enormous task, and I could
definitely use help. Whether you're an experienced Python dev or if you're new 
to programming and are just looking to something to cut your teeth on, you're 
more than welcome. This document lays out a bit of background in terms of how 
I'm doing things. I'm aiming to make it accessible and informative for people 
of all experience levels, so if something is unclear, please let me know.

If, after reading through this document, you're interested in contributing,
please [contact me directly through the Smogon forums](http://www.smogon.com/forums/members/antar.45129/).

## Purpose of Onix

The purpose of Onix is for Smogon and Pokemon Showdown to have a stats system
that is:
  - accurate, computing stats correctly and taking into account various 
  generation- and metagame-specific mechanics to compute metrics that 
  competitive battlers can use and trust
  - robust, that is, it handles errors cleanly, in ways that, when possible, 
  allow un-affected processes to continue to run and make it quick and easy to 
  rerun "broken" analyses without having to rerun everything for the month
  - ...
  
## The Onix Ecosystem
  - python (natch)
    - py3 esp, pypy targeted for future
  - conda virtual environments
  - sqlalchemy for backend flexibility
  - `py.test`
  - Sphinx for building docs, hosting on RTD
  - TravisCI for comprehensive testing
  - ZenHub for project management
  
### Style Guide
  - readible
  - Google docstring style
  - docs compile cleanly with Sphinx
  - Try to keep to pep8, pylint, other best-practices but don't kill yourself
  - Tests should be thorough (100% coverage is necessary but not sufficient)

## Ways to Contribute
  - CLA?

### Bug Reports, Feature Requests
  - If you're non-technical, opening an issue where you lay out the problem / 
  request in words is great
  - If you feel comfortable, fork / branch, write failing tests, then submit a
  Pull Request

### Take on an Existing Issue
  - Check ZenHub for top priority
  - Assign to yourself
  - Make sure you 100% understand the issue.
    - If you'd like, I can write the tests, so intent is clearer
  - Fork / branch
  - TDD is optimal, but don't feel like you need to write tests first
  - Implement the feature / fix the bug!
  - More tests to cover edge-cases
  - Pull Request
    - Feel free to PR early to get feedback
  - I may fix minor stylistic things, but I'll ask you to fix / rewrite anything
  major
  - Once everything's good stylistically and all tests pass, it gets merged in, 
  and you've officially contributed to Onix!


### Add a New Analysis
  - Best to submit a feature request, get the green light, then assign it to 
  yourself

  
