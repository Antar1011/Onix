#!/usr/bin/env bash

py.test --cov-config .coveragerc --cov=onix "$@" tests

#py.test --cov-config .coveragerc --cov=onix --doctest-modules onix "$@" tests
