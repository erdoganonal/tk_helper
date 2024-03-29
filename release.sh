#!/bin/bash

set -e

function main() {
    python -m pip install --upgrade pip
    python -m pip install --upgrade build
    python -m build
    python -m pip install --upgrade twine
    python -m twine upload --repository pypi dist/*
}

main
