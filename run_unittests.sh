#!/usr/bin/env bash

py.test --cov-config .coveragerc --cov=onix "$@"

#py.test --cov-config .coveragerc --cov=onix --doctest-modules onix "$@"