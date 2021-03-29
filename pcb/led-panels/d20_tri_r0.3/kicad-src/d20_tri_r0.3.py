# -*- coding: utf-8 -*-

from skidl import *
from string import ascii_uppercase

class matrix():
    def __init__(self, x, y, device):
        self.leds = device(x*y)
        self.col_r = [Net(f'colr_{i}') for i in range(x)]
        self.col_g = [Net(f'colg_{i}') for i in range(x)]
        self.col_b = [Net(f'colb_{i}') for i in range(x)]
        self.row = [Net(f'row_{i}') for i in range(y)]

        for r in range(y):
            for c in range(x):
                self.leds[r*x + c][4,3,2] += self.col_r[c],self.col_g[c],self.col_b[c]
                self.leds[r*x + c][1] += self.row[r]

def _home_greg_projects_GlassUnicorn_hardware_panel_32x32_1515_P1_8_r0_1_panel_32x32_1515_r0_1_sch():

    #===============================================================================
    # Component templates.
    #===============================================================================

    shift = Part('74xx', '74HC595', dest=TEMPLATE, footprint='gkl_misc:TSSOP-16_slim')
    conn = Part('Connector_Generic_Shielded', 'Conn_01x06_Shielded', dest=TEMPLATE, footprint='gkl_conn:5034800600')
    cap_polarised = Part('Device', 'CP1', dest=TEMPLATE, footprint='Capacitor_SMD:CP_Elec_5x3.9')
    cap = Part('Device', 'C', dest=TEMPLATE, footprint='Capacitor_SMD:C_0402_1005Metric')
    rgb = Part('Device', 'LED_ARGB', dest=TEMPLATE, footprint='gkl_led:led_rbag_1515_dense')
    pmos = Part('Device', 'Q_PMOS_GSD', dest=TEMPLATE, footprint='Package_TO_SOT_SMD:SOT-883', value='LP0404N3T5G')
    res = Part('Device', 'R', dest=TEMPLATE, footprint='Resistor_SMD:R_0402_1005Metric')
    tlc59025 = Part('gkl_misc', 'TLC59025', dest=TEMPLATE, footprint='gkl_misc:SSOP-24_slim')
    buff = Part('gkl_misc', 'NC7WZ17', dest=TEMPLATE, footprint='gkl_misc:UDFN-6_1x1mm_P0.35mm')


    vcc, gnd = Net('vcc'), Net('gnd')

    # input connecions
    sclk_in, latch_in, blank_in, data_in = Net('sclk_i'), Net('latch_i'), Net('blank_i'), Net('dat_i')
    sclk, latch, blank, data = Net('sclk'), Net('latch'), Net('blank'), Net('dat')

    #output connections
    data_out = Net('dat_out')

    #===============================================================================
    # Component instantiations.
    #===============================================================================

    bypass = cap(3, value='100nF')
    for c in bypass:
        c[1,2] += vcc, gnd

    inputConnector = conn(name='input')
    outputConnector = conn(name='output')


    inputConnector[1] & outputConnector[1] & vcc
    inputConnector[2] & data_in
    outputConnector[2] & data_out
    inputConnector[3] & blank_in
    inputConnector[4] & latch_in
    inputConnector[5] & sclk_in
    inputConnector[6] & gnd

    outputConnector[3] & blank
    outputConnector[4] & latch
    outputConnector[5] & sclk
    outputConnector[6] & gnd
    inputConnector['Shield'] & outputConnector['Shield'] & gnd
    
    # Matrix Size 
    x = 16
    y = 15

    array = matrix(x,y, rgb)
    drivers = tlc59025(3)

    row_driver = shift(2)
    row_pmos = pmos(y)

    # attach resistors to drivers
    values = ['2.2k', '7.5k', '4.12k']
    i_set = res(3)
    for r,d,v in zip(i_set,drivers, values):
        r.value = v

        Net(f'{d.ref}_r_ext') & r[1] & d['R-EXT']
        r[2] & gnd

        # Misc Pins
        d['VDD','GND'] += vcc, gnd
        d['CLK', 'LE', '~OE'] += sclk, latch, blank
    
    # connect common signals
    for rd in row_driver:
        rd['SRCLK', 'RCLK', '~OE', '~SRCLR'] += sclk, latch, gnd, vcc
        rd['VCC', 'GND'] += vcc, gnd


    # attach serial input
    drivers[0]['SDI'] += data

    # patch serial link through chips
    for src, dst in zip(drivers[0:], drivers[1:]):
        Net(f'sdo_{src.ref}>sdi_{dst.ref}') & src['SDO'] & dst['SDI']
    
    # patch through row driver shift register
    Net(f'sdo_{drivers[-1].ref}') & drivers[-1]['SDO'] & row_driver[0]['SER']
    

    for src, dst in zip(row_driver[0:], row_driver[1:]):
        Net(f'sdo_{src.ref}>sdi_{dst.ref}') & src['QH\''] & dst['SER']
    

    data_out & row_driver[-1]['QH\'']


    driver_list = [f'OUT{i}' for i in range(16)]

    drivers[0][driver_list] += array.col_r[0:16]
    drivers[1][driver_list] += array.col_g[0:16]
    drivers[2][driver_list] += array.col_b[0:16]

    

    for p,anode,driver in zip(row_pmos[0:8],array.row[0:8],row_driver[0][[f'Q{ascii_uppercase[idx]}' for idx in range(8)]]):
        Net(f's{anode.name}') & p['G'] & driver
        p['D'] += anode
        p['S'] += vcc
    for p,anode,driver in zip(row_pmos[8:15],array.row[8:15],row_driver[1][[f'Q{ascii_uppercase[idx]}' for idx in range(7)]]):
        Net(f's{anode.name}') & p['G'] & driver
        p['D'] += anode
        p['S'] += vcc


    inputBuffers = buff(2)
    for b in inputBuffers:
        b['VCC','GND'] += vcc,gnd

    inputBuffers[0]['A1'] & data_in
    inputBuffers[0]['Y1'] & data
    inputBuffers[0]['A2'] & blank_in
    inputBuffers[0]['Y2'] & blank

    inputBuffers[1]['A2'] & latch_in
    inputBuffers[1]['Y2'] & latch
    inputBuffers[1]['A1'] & sclk_in
    inputBuffers[1]['Y1'] & sclk 
    


#===============================================================================
# Instantiate the circuit and generate the netlist.
#===============================================================================

if __name__ == "__main__":
    _home_greg_projects_GlassUnicorn_hardware_panel_32x32_1515_P1_8_r0_1_panel_32x32_1515_r0_1_sch()
    generate_netlist()
