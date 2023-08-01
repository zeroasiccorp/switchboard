#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path
from argparse import ArgumentParser


def main(dry_run=False, verbose=False):
    """Get dependencies from git repositories."""

    deps_dir = Path(__file__).resolve().parent / 'deps'
    deps_dir.mkdir(parents=True, exist_ok=True)

    with open('dependencies.json', 'r') as f:
        deps = json.load(f)

    for dep in deps:
        dep_dir = deps_dir / dep['name']

        if not dep_dir.exists():
            # clone if the folder doesn't exist
            if verbose or dry_run:
                print(f'Cloning {dep["name"]}')
            if not dry_run:
                git('clone', dep['url'], dep['name'], cwd=deps_dir)
        else:
            # otherwise fetch updates
            if verbose or dry_run:
                print(f'Fetching updates for {dep["name"]}')
            if not dry_run:
                git('fetch', cwd=dep_dir)

        # checkout the specific commit
        if verbose or dry_run:
            print(f'Checking out {dep["name"]} @ {dep["commit"]}')
        if not dry_run:
            git('checkout', dep['commit'], cwd=dep_dir)


def git(*args, **kwargs):
    cmd = ['git']
    cmd.extend(args)
    cmd = [str(elem) for elem in cmd]

    subprocess.run(cmd, check=True, **kwargs)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-n', '--dry-run', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    main(dry_run=args.dry_run, verbose=args.verbose)
