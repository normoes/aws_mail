#!/bin/bash

#######3
##
## Update python dependencies using 'pip-tools'('pip-compile').
##   Considering a given Python environment by:
##     * host
##     * existing 'virtualenv'
##     * docker container
##       - Assumes no 'virutalenv' is used.
##
#######3

set -Eeuo pipefail

# The docker environment is marked by the environment variable 'DOCKER_ENV'.
if [ -z "${DOCKER_ENV+x}" ]; then
    # If this is not the docker environment,
    # either use a pre-defined (system, virtualenv) 'pip-compile' by
    #  ./update_requirements.txt -s ./venv/bin/
    #  or
    #  ./update_requirements.txt -s ~/.local/bin/
    #  or simply use the host's installation of 'pip-compile`'.
    system=""
    while getopts ":s:" opt; do
        case $opt in
          s) system="$OPTARG"
          ;;
        esac
    done
    if [ -n "$system" ]; then
        interpreter="$system"
    else
        interpreter=""
    fi
else
    # If this is the docker environment,
    # expect 'pip-compile' to be known system-wide.
    interpreter=""
fi

if [ -n "$interpreter" ]; then
    echo "Using 'pip-compile' in: '$interpreter'."
else
    echo "Using: '$(command -V pip-compile | cut -d ' ' -f 3)'."
fi

echo -e "\e[32mCompile service dependencies.\e[39m"
# Using '--upgrade' to auto-upgrade dependencies
# defined as '>='/'>'.
"$interpreter"pip-compile --upgrade --output-file requirements.txt --pip-args "--no-cache-dir" requirements.in
if [ -f "./requirements.test.in"  ];then
    echo -e "\e[32mCompile service test dependencies.\e[39m"
    "$interpreter"pip-compile --upgrade --output-file requirements.test.txt --pip-args "--no-cache-dir" requirements.test.in
fi
if [ -f "./requirements.deploy.in"  ];then
    echo -e "\e[32mCompile service deploy dependencies.\e[39m"
    "$interpreter"pip-compile --upgrade --output-file requirements.deploy.txt --pip-args "--no-cache-dir" requirements.deploy.in
fi

# Prepend the compiled requirements file with the current date (UTC).
# Force same locale for every one.
current_date=$(LC_ALL=en_US.utf8 date --utc)
# platform=$(uname)
# if [ "$platform" == "Linux" ]; then
sed -i "1i# Compile date: $current_date" requirements.txt requirements.test.txt
# fi

echo -e "\e[32mDone.\e[39m"
