#!/bin/bash

cd $(dirname "${0}")
rootdir="$PWD"
export CHANDLERBIN="${rootdir}/linux"
export CHANDLERHOME="${rootdir}/chandler"
"${CHANDLERBIN}/release/RunChandler" --profileDir="${rootdir}/profile" --repodir="${CHANDLERBIN}" --datadir=../../profile/data --logdir=../../profile/logs $@
