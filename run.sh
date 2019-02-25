#!/bin/sh

git clone --depth 1 https://github.com/niranjan94/codebuild-extras.git ../codebuild-extras
pip install -r ../codebuild-extras/requirements.txt
. ../codebuild-extras/load-codebuild-env.sh
python ../codebuild-extras/run-tests.py