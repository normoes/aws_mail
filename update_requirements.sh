#!/bin/bash

set -Eeuo pipefail

pip-compile --output-file requirements.txt requirements.in
