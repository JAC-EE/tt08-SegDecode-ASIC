# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

# ToDo:
# Implement testing for screensel, keyplxr, and miso
# 7 segment testing is functional

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from cocotb.triggers import Timer
import csv

# Load csv file
def read_test_values(filename):
    test_values = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            input_value = int(row[0], 16)  # Convert hex string to int
            expected_output = int(row[1], 16)  # Convert hex string to int
            test_values.append((input_value, expected_output))
    return test_values

# Sends DATA of a specific LENGTH through spi. MOSI pin is selected by providing a MASK for ui_in
# MSB first
async def SPI_send(dut, DATA: int, LENGTH: int, MASK: int):
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    # Send SPI data
    for i in range(LENGTH):
        dut._log.info(f"SPI send: {i}")
        if (DATA << i) & 0x80 == 0x80: # Check if highest bit is set
            dut.ui_in.value = 0x6#int(dut.ui_in.value) | MASK # SPI enable
            dut._log.info(f"DATA: 1")
        else:
            dut.ui_in.value = 0x4#int(dut.ui_in.value) & ~MASK #clear bit
            dut._log.info(f"DATA: 0")
        await ClockCycles(dut.clk, 1)

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")
    
    # Load test values from CSV file
    seven_segment_anode = read_test_values('7_segment_anode.csv')

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 1
    
    dut._log.info("Test project behavior")
    
    await ClockCycles(dut.clk, 1)
    
    for input_value, expected_output in seven_segment_anode:
        # Initial tests
        i = input_value
        await ClockCycles(dut.clk, 1)
        dut._log.info(f"Test: {i}")
        dut.ui_in.value = int(dut.ui_in.value) | 0x4 # SPI enable
        await ClockCycles(dut.clk, 1)
        await SPI_send(dut, i, 8, 2) #send loop iteration, 8 bits, bit mask 0000 0010
        dut.ui_in.value = int(dut.ui_in.value) & ~0x4 # SPI disable
        await ClockCycles(dut.clk, 1)
        dut.ui_in.value = int(dut.ui_in.value) | 0x4 # SPI enable
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value & 0x7F == seven_segment_anode[i][1], f"7 Segment result incorrect: {dut.uo_out.value}" #7 Segment test
        dut.ui_in.value = 0 # int(dut.ui_in.value) & ~0x4 # SPI disable
        await ClockCycles(dut.clk, 1)
    #END
    
    #dut.rst_n.value = 0

    

    # Set the input values you want to test
   # dut.ui_in.value = 20
    # dut.uio_in.value = 30
   

    # Wait for one clock cycle to see the output values
    #await ClockCycles(dut.clk, 1)

    # The following assersion is just an example of how to check the output values.
    # Change it to match the actual expected output of your module:
    #assert dut.uo_out.value == 50

    # Keep testing the module by changing the input values, waiting for
    # one or more clock cycles, and asserting the expected output values.


    # assert False, "This testbench is incomplete and needs further development."