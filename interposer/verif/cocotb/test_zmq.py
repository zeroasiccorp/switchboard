from pathlib import Path
from cocotb_test.simulator import run

from zverif.utils import file_list

# folder structure 
TOP_DIR = Path(__file__).resolve().parent.parent.parent
RTL_DIR = TOP_DIR / 'rtl'
VERIF_DIR = TOP_DIR / 'verif'
VERILOG_DIR = VERIF_DIR / 'verilog'
VERILOG_AXI = VERILOG_DIR / 'verilog-axi' / 'rtl'
UMI_DIR = VERILOG_DIR / 'umi' / 'umi' / 'rtl'

def test_zmq():
    # determine Verilog sources
    verilog_sources = [
        RTL_DIR / '*.v',
        UMI_DIR / 'umi_decode.v',
        UMI_DIR / 'umi_pack.v',
        UMI_DIR / 'umi_unpack.v',
        VERILOG_DIR / 'axi_to_umi.v',
        VERILOG_DIR / 'umi_to_axi.v',
        VERILOG_AXI / 'arbiter.v',
        VERILOG_AXI / 'priority_encoder.v',
        VERILOG_AXI / 'axil_interconnect.v',
        VERILOG_AXI / 'axil_dp_ram.v',
        VERILOG_DIR / 'axil_interconnect_wrap_*.v',
        VERILOG_DIR / 'zverif_top.v'
    ]
    verilog_sources = file_list(verilog_sources, convert_to_path=False)

    run(
        verilog_sources=verilog_sources,
        toplevel="zverif_top",
        module="zmq_server"
    )