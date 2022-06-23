import sys

from doit.task import dict_to_task
from doit.cmd_base import TaskLoader2
from doit.doit_cmd import DoitMain

from zverif.utils import add_group_task

class MyLoader(TaskLoader2):
    def __init__(self, *args, my_tasks=None, my_group_tasks=None, **kwargs):
        # call the super constructor
        super().__init__(*args, **kwargs)

        # save the tasks for later use
        self._my_tasks = my_tasks if my_tasks is not None else []
        self._my_group_tasks = my_group_tasks if my_group_tasks is not None else {}

    def setup(self, opt_values):
        pass

    def load_doit_config(self):
        return {
            'default_tasks': ['verilator:hello'],
            'verbosity': 2
        }

    def load_tasks(self, cmd, pos_args):
        tasks = [dict_to_task(elem) for elem in self._my_tasks]
        for k, v in self._my_group_tasks.items():
            add_group_task(tasks, basename=k, doc=v)
        return tasks

def doit_main_loop(tasks, group_tasks, args=None, exit=True):
    if args is None:
        args = sys.argv[1:]
    
    loader = MyLoader(my_tasks=tasks, my_group_tasks=group_tasks)
    retval = DoitMain(loader).run(args)

    if exit:
        sys.exit(retval)