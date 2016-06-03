#!/usr/bin/env bash

py.test --cov-config .coveragerc --cov=smogonusage --doctest-modules smogonusage "$@"