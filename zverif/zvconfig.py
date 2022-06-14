from pathlib import Path
import glob
from typing import Dict
import yaml

class ZvRiscvOpts:
    def __init__(self, path : Path, d : dict):
        riscv = d.get('riscv', {})
        self.isa = riscv.get('isa', 'rv32imc')
        self.abi = riscv.get('abi', 'ilp32')

class ZvSwFile:
    def __init__(self, path, extra_sources, linker_script, include_paths):
        self.path = path
        self.extra_sources = extra_sources
        self.linker_script = linker_script
        self.include_paths = include_paths

class ZvSwOpts:
    def __init__(self, path : Path, d : dict):
        sw = d.get('sw', [])
        self.objs : Dict[str, ZvSwFile] = {}
        for file in sw:
            # convert to absolute path
            file_path = Path(file['file'])
            if not file_path.is_absolute():
                file_path = path / file_path
            
            # add entry for each file to be processed
            for elem in glob.glob(str(file_path)):
                # generate name and check it
                name=Path(elem).stem
                if name in self.objs:
                    raise Exception(f'Test name collision: {name}')
                
                # add to list of software files
                self.objs[name] = ZvSwFile(
                    path=elem,
                    extra_sources=file.get('extra_sources', []),
                    linker_script=file.get('linker_script', None),
                    include_paths=file.get('include_paths', [])
                )

class ZvSpikePlugin:
    def __init__(self, path, extra_sources, include_paths, address):
        self.path = path
        self.extra_sources = extra_sources
        self.include_paths = include_paths
        self.address = address

class ZvSpikeOpts:
    def __init__(self, path : Path, d : dict):
        spike_plugins = d.get('spike_plugins', [])
        self.objs : Dict[str, ZvSpikePlugin] = {}
        for file in spike_plugins:
            # convert to absolute path
            file_path = Path(file['file'])
            if not file_path.is_absolute():
                file_path = path / file_path
            
            # add entry for the plugin
            name=file_path.stem
            if name in self.objs:
                raise Exception(f'Test name collision: {name}')
            
            # determine numeric value for address
            address = file['address']
            if not isinstance(address, int):
                address = int(address, 0)  # can handle hex with a "0x" prefix

            # add to list of software files
            self.objs[name] = ZvSpikePlugin(
                path=file_path,
                extra_sources=file.get('extra_sources', []),
                include_paths=file.get('include_paths', []),
                address=address
            )        

class ZvVerilatorOpts:
    def __init__(self, path : Path, d : dict):
        # find Verilog sources
        self.verilog_sources = []
        for pattern in ['*.v', '*.sv']:
            self.verilog_sources += glob.glob(str(path / 'verilator' / pattern))
        self.verilog_sources = [Path(elem) for elem in self.verilog_sources]

        # find C sources
        self.c_sources = []
        for pattern in ['*.c', '*.cc', '*.cpp']:
            self.c_sources += glob.glob(str(path / 'verilator' / pattern))
        self.c_sources = [Path(elem) for elem in self.c_sources]

class ZvConfig:
    def __init__(self, file_path=None):
        # determine default path if needed
        if file_path is None:
            file_path = Path('zverif.yaml')

        # read YAML file
        with open(file_path, "r") as stream:
            self.data = yaml.safe_load(stream)

        # determine directory where YAML file is stored
        self.path = Path(file_path).resolve().parent

        # gather options for various targets
        self.riscv = ZvRiscvOpts(self.path, self.data)
        self.sw = ZvSwOpts(self.path, self.data)
        self.spike = ZvSpikeOpts(self.path, self.data)
        self.verilator = ZvVerilatorOpts(self.path, self.data)
    
    @property
    def build_dir(self):
        return self.path / 'build'

