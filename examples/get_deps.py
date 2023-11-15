#!/usr/bin/env python3

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import json
import subprocess
from pathlib import Path
from argparse import ArgumentParser


def main(dry_run=False, verbose=False):
    """Get dependencies from git repositories."""

    this_dir = Path(__file__).resolve().parent

    deps_dir = this_dir / 'deps'
    deps_dir.mkdir(parents=True, exist_ok=True)

    with open(this_dir / 'dependencies.json', 'r') as f:
        deps = json.load(f)

    for dep in deps:
        dep_dir = deps_dir / dep['name']

        if not dep_dir.exists():
            # clone if the folder doesn't exist
            if dry_run:
                print(f'Would clone {dep["url"]} into {dep_dir}.')
            else:
                git('clone', dep['url'], dep['name'], verbose=verbose, cwd=deps_dir)

        # checkout the specific commit
        if dry_run:
            print(f'Would checkout {dep["name"]} @ {dep["commit"]}.')
        else:
            try:
                git('checkout', dep['commit'], verbose=verbose, cwd=dep_dir)
            except subprocess.CalledProcessError:
                git('fetch', cwd=dep_dir)
                git('checkout', dep['commit'], verbose=verbose, cwd=dep_dir)


def git(*args, verbose=False, cwd=None):
    cmd = ['git']
    cmd.extend(args)
    cmd = [str(elem) for elem in cmd]

    subprocess.run(cmd, check=True, capture_output=(not verbose), cwd=cwd)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-n', '--dry-run', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    main(dry_run=args.dry_run, verbose=args.verbose)
