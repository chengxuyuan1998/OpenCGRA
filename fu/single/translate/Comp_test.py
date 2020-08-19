"""
==========================================================================
Comp_test.py
==========================================================================
Test cases for functional unit Phi.

Author : Cheng Tan
  Date : November 27, 2019

"""

from pymtl3 import *
from pymtl3.stdlib.test           import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcRTL
#from pymtl3.stdlib.test.test_sinks import TestSinkRTL

from ..Comp                       import Comp
from ....lib.opt_type             import *
from ....lib.messages             import *

from pymtl3.passes.backends.verilog import TranslationPass, VerilatorImportPass, TranslationImportPass
from pymtl3.passes.PassGroups import *

#-------------------------------------------------------------------------
# Test harness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, FunctionUnit, DataType, CtrlType, num_inports, num_outports,
                 data_mem_size, src_data, src_ref, src_opt, sink_msgs ):

    s.src_data = TestSrcRTL( DataType, src_data  )
    s.src_ref  = TestSrcRTL( DataType, src_ref   )
    s.src_opt  = TestSrcRTL( CtrlType, src_opt   )
    s.sink_out = TestSinkCL( DataType, sink_msgs )

    s.dut = FunctionUnit( DataType, CtrlType, num_inports, num_outports,
                          data_mem_size )

    connect( s.src_data.send, s.dut.recv_in[0]  )
    connect( s.src_ref.send,  s.dut.recv_in[1]  )
    connect( s.src_opt.send,  s.dut.recv_opt    )
    connect( s.dut.send_out[0], s.sink_out.recv )

  def done( s ):
    return s.src_data.done() and s.sink_out.done()
#    return s.src_data.done() and s.src_ref.done() #and\
#           s.src_opt.done()  and s.sink_out.done()

  def line_trace( s ):
    return s.dut.line_trace()

#  test_harness.dut.verilog_translate = True
#  test_harness.dut.verilog_import = True
#  test_harness.apply( SimpleSimPass() )

def run_sim( test_harness, max_cycles=10 ):
  test_harness.elaborate()
  test_harness.dut.verilog_translate_import = True
#  test_harness.apply( TranslationPass() )
#  test_harness = VerilatorImportPass()( test_harness )
  test_harness.dut.config_verilog_import = VerilatorImportConfigs(vl_Wno_list = ['UNSIGNED', 'UNOPTFLAT', 'WIDTH', 'WIDTHCONCAT', 'ALWCOMBORDER'])
  test_harness = TranslationImportPass()(test_harness)
  test_harness.apply( SimulationPass() )
  test_harness.sim_reset()

  # Run simulation

  ncycles = 0
  print()
  print( "{}:{}".format( ncycles, test_harness.line_trace() ))
  while not test_harness.done() and ncycles < max_cycles:
    test_harness.tick()
    ncycles += 1
    print( "{}:{}".format( ncycles, test_harness.line_trace() ))

  # Check timeout

  assert ncycles < max_cycles

  test_harness.tick()
  test_harness.tick()
  test_harness.tick()

import platform
import pytest

@pytest.mark.skipif('Linux' not in platform.platform(),
                    reason="requires linux (gcc)")
def test_Comp():
  FU = Comp
  DataType   = mk_data( 32, 1 )
  CtrlType = mk_ctrl()
  num_inports   = 2
  num_outports  = 2
  data_mem_size = 8
  FuInType = mk_bits( clog2( num_inports + 1 ) )
  pickRegister = [ FuInType( x+1 ) for x in range( num_inports ) ]
  src_data   = [ DataType(9, 1), DataType(3, 1), DataType(3, 1) ]
  src_ref    = [ DataType(9, 1), DataType(5, 1), DataType(2, 1) ]
  src_opt    = [ CtrlType( OPT_EQ, pickRegister ),
                 CtrlType( OPT_LE, pickRegister ),
                 CtrlType( OPT_EQ, pickRegister ) ]
  sink_out   = [ DataType(1, 1), DataType(1, 1), DataType(0, 1) ]
  th = TestHarness( FU, DataType, CtrlType, num_inports, num_outports,
                    data_mem_size, src_data, src_ref, src_opt, sink_out )
  run_sim( th )

