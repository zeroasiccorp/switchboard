import sys

from doit.task import dict_to_task
from doit.cmd_base import TaskLoader2
from doit.doit_cmd import DoitMain

class MyLoader(TaskLoader2):
    def __init__(self, *args, my_tasks=None, **kwargs):
        # call the super constructor
        super().__init__(*args, **kwargs)

        # save the tasks for later use
        self._my_tasks = my_tasks if my_tasks is not None else []

    def setup(self, opt_values):
        pass

    def load_doit_config(self):
        return {
            'default_tasks': ['verilator:hello'],
            'verbosity': 2
        }

    def load_tasks(self, cmd, pos_args):
        return list(self._my_tasks)

def doit_main_loop(tasks, args=None, exit=True):
    if args is None:
        args = sys.argv[1:]
    
    loader = MyLoader(my_tasks=tasks)
    retval = DoitMain(loader).run(args)

    if exit:
        sys.exit(retval)