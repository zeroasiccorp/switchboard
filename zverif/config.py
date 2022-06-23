from pathlib import Path
import yaml

class ZvConfig:
    def __init__(self, cfg_file='zverif.yaml'):
        # read config file if available
        try:
            with open(cfg_file, 'r') as f:
                d = yaml.safe_load(f)
        except:
            d = {}
        
        # simple set defaults (those that do not depend on how other
        # defaults are set.  adding 
        self.riscv_prefix = d.get('riscv_prefix', 'riscv64-unknown-elf-')
        self.riscv_abi = d.get('riscv_abi', 'ilp32')
        self.riscv_isa = d.get('riscv_isa', 'rv32im')
        self.build_dir = d.get('build_dir', Path('.') / 'build')
        self.gcc = d.get('gcc', 'gcc')
        self.spike = d.get('spike', 'spike')
        self.verilator = d.get('verilator', 'verilator')
        self.rtl_top = d.get('rtl_top', 'zverif_top')

        # set dependent defaults
        self.riscv_gcc = d.get('riscv_gcc', f'{self.riscv_prefix}gcc')
        self.riscv_objcopy = d.get('riscv_objcopy', f'{self.riscv_prefix}objcopy')
        self.sw_dir = d.get('sw_dir', Path(self.build_dir) / 'sw')
        self.spike_dir = d.get('spike_dir', Path(self.build_dir) / 'spike')
        self.verilator_dir = d.get('verilator_dir', Path(self.build_dir) / 'verilator')
