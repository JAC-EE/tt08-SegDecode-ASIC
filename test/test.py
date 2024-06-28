# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

# ToDo:
# COMPLETE Fix bit setting in SPI_send
# Implement testing for screensel, keyplxr, and miso
# 7 segment testing is functional

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from cocotb.triggers import Timer
import csv

# Set the clock period to 10 us (100 KHz)
clock_period = 10

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
    # Set the clock period
    #clock = Clock(dut.clk, clock_period, units="us")
    #cocotb.start_soon(clock.start())
    # Send SPI data
    dut._log.info(f"SPI send: {bin(DATA)}")
    for i in range(LENGTH):
        #dut._log.info(f"SPI send: {i}")
        if (DATA << i) & 0x80 == 0x80: # Check if highest bit is set
            dut.ui_in.value = int(dut.ui_in.value) | int(MASK) # SPI enable 0x6
            dut._log.info(f"DATA: 1")
        else:
            dut.ui_in.value = int(dut.ui_in.value) & ~int(MASK) #clear bit 0x4
            dut._log.info(f"DATA: 0")
        #await ClockCycles(dut.clk, 1)
        await Timer(clock_period, units='us') 
    dut.ui_in.value = 4#int(dut.ui_in.value) & ~MASK #clear bit

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")
    
    # Load test values from CSV file
    seven_segment_anode = read_test_values('7_segment_anode.csv')
    screenselect_test = read_test_values('screenselect.csv')

    # Set the clock period
    clock = Clock(dut.clk, clock_period, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 1
    
    dut._log.info("Test project behavior")
    
    #await ClockCycles(dut.clk, 1)
    await Timer(0.75 * clock_period, units='us') # Put serial system 1/4 clock cycles ahead. Simulates similar setup and hold times
    
    errors = 0
    
    for input_value, expected_output in seven_segment_anode:
        # Test 7 Segment display logic
        i = input_value
        #await ClockCycles(dut.clk, 1)
        await Timer(clock_period, units='us') 
        dut._log.info(f"Test: {i}")
        dut.ui_in.value = int(dut.ui_in.value) | 0x4 # SPI enable
        #await ClockCycles(dut.clk, 1)
        await Timer(clock_period, units='us') 
        await SPI_send(dut, screenselect_test[i][0] | i, 8, 2) #send loop iteration, 8 bits, bit mask 0000 0010
        dut._log.info(f"SPI send: {bin(screenselect_test[i][0])}")
        dut.ui_in.value = int(dut.ui_in.value) & ~0x4 # SPI disable
        #await ClockCycles(dut.clk, 1)
        dut.rst_n.value = 0 # Activate reset (prevents SCK functioning) DEBUG
        await Timer(clock_period, units='us') 
        dut.ui_in.value = int(dut.ui_in.value) | 0x4 # SPI enable
        #await ClockCycles(dut.clk, 1)
        await Timer(clock_period, units='us') 
        try:
            assert dut.uo_out.value & 0x7F == seven_segment_anode[i][1], f"7 Segment result incorrect: Was: {hex(dut.uo_out.value & 0x7F)} Should be: {hex(seven_segment_anode[i][1])}" #7 Segment test
        except AssertionError as e:
            dut._log.error(str(e))
            errors += 1
        dut.ui_in.value = int(dut.ui_in.value) & ~0x4 # SPI disable
        dut.rst_n.value = 1 # Deactivate reset (returns SCK to functioning) DEBUG
        #await ClockCycles(dut.clk, 1)
        await Timer(clock_period, units='us') 
        # END 7 Segment display logic test
    
    
    # Check if any errors occured
    if errors:
        dut._log.error(f"{errors} test cases failed")
        assert 0,  f"Testbench encountered errors. Test failed."
    else:
        dut._log.info("All test cases passed")


    # assert False, "This testbench is incomplete and needs further development."