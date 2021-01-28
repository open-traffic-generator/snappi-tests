#!/bin/sh

if [ -z ${1} ]; then
    PYTHON=python
else
    PYTHON=${1}
fi

rm -rf env
${PYTHON} -m pip install --upgrade virtualenv \
&& ${PYTHON} -m virtualenv env \
&& env/bin/python -m pip install --upgrade "snappi[ixnetwork]" \
&& env/bin/python -m pip install --upgrade -r requirements.txt
