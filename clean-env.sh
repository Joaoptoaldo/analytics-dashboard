#!/bin/bash
cd "$(dirname "$0")"
export FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch -f --tree-filter 'test -f .env.production && rm .env.production; true' -- --all
git reflog expire --expire=now --all
git gc --prune=now --aggressive
