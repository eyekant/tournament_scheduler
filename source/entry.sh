#!/bin/bash

set -e
export PYTHONPATH=$(pwd)
if [[ "$1" == "one" ]]; then 
    ./run_one_instance.sh "${@:2}"
elif [[ "$1" == "all" ]]; then 
    ./run_all_instances.sh "${@:2}"
elif [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: {one|all} [solvers] [teams]"
    echo "   Examples:"
    echo "      one \"base_cbc\" 8   # Run one instance using base cbc model with 8 teams"
    echo "      all                # Run all instances"
    exit 0
else
    echo "Usage: {one|all} [solvers] [teams]"
    echo "   Examples:"
    echo "      one \"base_cbc\" 8   # Run one instance using base cbc model with 8 teams"
    echo "      all                # Run all instances"
    exit 1
fi