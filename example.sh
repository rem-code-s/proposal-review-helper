#!/bin/zsh
make review \
REPO=https://github.com/dfinity/ic.git \
ID=1 \
START_COMMIT=51dd253fd8b301f849dfc26f77cff6d15acd04c1 \
END_COMMIT=286295f0397521cd59ca7792df446c57379204fa \
REVIEW_PATHS='rs/registry/canister'

