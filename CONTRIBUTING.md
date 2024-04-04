How to contribute to switchboard
=====================================

Thank you for considering contributing to this project!

## General guidelines
- Start small, relationships need time to grow
- All new features must come with pytests
- Keep PRs short to simplify review
- Large PRs should be preceded by discussions
- Discuss with core team before proposing core changes
- PRs should include changes only to files related to change
- Comply with coding guidelines/style of project
- Avoid style only code based PRs

#### Reporting issues

Check if this issue is already fixed in the latest release.  If not, please include the following information in your post:

- Describe what you expected to happen.
- Describe what actually happened.
- Include the full traceback if there was an exception.
- List your Python, switchboard, and RTL simulator versions.
- Include a [minimal reproducible example](https://stackoverflow.com/help/minimal-reproducible-example)


## Submitting patches

If there is not an open issue for what you want to submit, prefer opening one
for discussion before working on a PR. You can work on any issue that doesn't
have an open PR linked to it or a maintainer assigned to it. These show up in
the sidebar. No need to ask if you can work on an issue that interests you.

Include the following in your patch:

- Include tests if your patch adds or changes code (should fail without the patch)
- Update any relevant docs pages and docstrings.


## First time setup

- Install [git](https://git-scm.com/downloads)

- Configure your [git username](https://docs.github.com/en/github/using-git/setting-your-username-in-git) and [git email](https://docs.github.com/en/github/setting-up-and-managing-your-github-user-account/setting-your-commit-email-address)
```sh
$ git config --global user.name 'your name'
$ git config --global user.email 'your email'
```
- Make sure you have a [github account](https://github.com/join)


## Clone/Fork Repository

- [Fork switchboard](https://github.com/zeroasiccorp/switchboard/fork) to your GitHub account (external contributors only)

- [Clone](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo#step-2-create-a-local-clone-of-your-fork) the main repository locally.

```sh
$ git clone https://github.com/{username}/switchboard
$ cd switchboard
```

- Retrieve git submodules used in the project

```sh
$ git submodule update --init
```

- Retrieve dependencies for running examples

```sh
$ pip install -r examples/requirements.txt
```

- Add fork as a remote to push your work to (external contributors only)

```sh
$ git remote add fork https://github.com/{username}/switchboard
```



## Install Python Requirements

-  Create a virtualenv.
```sh
$ python3 -m venv env
$ . env/bin/activate
```

- Upgrade pip and setuptools.
```sh
$ python3 -m pip install --upgrade pip setuptools
```

- Install the development dependencies
```sh
$ python3 -m pip install -e .[test]
$ python3 -m pip install -r examples/requirements.txt
```

## Start coding

-  Create a branch to identify the issue you would like to work on.

```sh
$ git fetch origin
$ git checkout -b your-branch-name origin/main
```
- Using your favorite editor, make your changes, and [commit](https://dont-be-afraid-to-commit.readthedocs.io/en/latest/git/commandlinegit.html#commit-your-changes)

- Include tests that cover any code changes you make. Make sure the test fails without your patch. Run the tests as described below.

- Push your commits to your fork on GitHub (external contributors)

```sh
$ git push --set-upstream fork your-branch-name
```

- Push your commits to your switchboard branch on GitHub (team contributors)
```sh
$ git push -u origin your-branch-name
```


## Running the tests

PRs need to pass a regression test suite before they can be merged.

- The full set of tests that will be run can be found in [.github/workflows/regression.yml](.github/workflows/regression.yml).  This currently includes Python-based tests, C-based tests, a test of FPGA emulation infrastructure, Python linting, and C/C++ linting.
- The easiest way to run all of the tests locally is to install [act](https://github.com/nektos/act), and then run `act --rm pull_request` in the top level of the repository.  Omit `--rm` if you want the Docker container where the tests run to stay around after a failure (for debugging purposes).

It is also possible to run specific tests locally.

- To run Python-based tests (requires [Verilator](https://www.veripool.org/verilator/) and [Icarus Verilog](https://github.com/steveicarus/iverilog)):
```sh
$ cd examples
$ pytest -s
$ cd ..
```

- To run C-based tests:
```sh
$ cd tests
$ make
$ cd ..
```

- To run a test of FPGA emulation infrastructure (requires [SystemC](https://www.accellera.org/downloads/standards/systemc)):
```sh
$ cd examples/fpga_loopback
$ make test
$ cd ../..
```

- To run Python linting (requires [flake8](https://flake8.pycqa.org/en/latest/))
```sh
$ flake8 .
```

- To run Verilog linting on specific files (requires [verible](https://github.com/chipsalliance/verible))
```sh
$ verible-verilog-lint --rules_config verible_lint.txt FILE1 FILE2 FILE3 ...
```

## Create a Pull Request

- Create a [pull request](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request) through GitHub.

## Resources

Based on the [SiliconCompiler contribution guidelines](https://github.com/siliconcompiler/siliconcompiler/blob/main/CONTRIBUTING.md)
