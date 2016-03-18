#!/bin/sh

sphinx-apidoc -f -o ./doc/source ./kollacli
python setup.py build_sphinx
