from pathlib import Path
import yaml
from zverif.zvconfig import ZvConfig
from zverif.riscv import ZvRiscv
from zverif.spike import ZvSpike
from zverif.verilator import ZvVerilator

DOIT_CONFIG = {
    'default_tasks': ['verilator:hello'],
    'verbosity': 2
}

# read YAML configuration
TOP_DIR = Path(__file__).resolve().parent
file_path = TOP_DIR / 'zverif.yaml'
with open(file_path, 'r') as stream:
    data = yaml.safe_load(stream)
cfg = ZvConfig(file_path=file_path, data=data)

def task_elf():
    '''Build software ELF files.'''
    return ZvRiscv(cfg).task_elf()

def task_bin():
    '''Build software BIN files.'''
    return ZvRiscv(cfg).task_bin()

def task_hex():
    '''Build software HEX files.'''
    return ZvRiscv(cfg).task_hex()

def task_spike():
    return ZvSpike(cfg).task_spike()

def task_spike_plugins():
    '''Build Spike plugins'''
    return ZvSpike(cfg).task_spike_plugins()

def task_verilator_build():
    '''Build Verilator simulation binary.'''
    return ZvVerilator(cfg).task_verilator_build()

def task_verilator():
    '''Run Verilator simulation'''
    return ZvVerilator(cfg).task_verilator()