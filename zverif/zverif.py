import sys

from doit.cmd_base import ModuleTaskLoader
from doit.doit_cmd import DoitMain

def main():
    import zverif.dodo
    sys.exit(DoitMain(ModuleTaskLoader(zverif.dodo)).run(sys.argv[1:]))

if __name__ == "__main__":
    main()