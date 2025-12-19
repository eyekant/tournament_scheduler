#!/bin/bash

set -e
export PYTHONPATH=$(pwd)
python3 one_instance.py "$1" "$2"