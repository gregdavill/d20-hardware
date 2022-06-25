#!/usr/bin/python3
# -*- coding: utf-8 -*-

from skidl import *
from string import ascii_uppercase
import subprocess
import csv

# Create LED RGB Matrix
class matrix():
    def __init__(self, x, y, device):
        self.leds = device(x*y)
        self.col_r = [Net(f'colr_{i}') for i in range(y)]
        self.col_g = [Net(f'colg_{i}') for i in range(y)]
        self.col_b = [Net(f'colb_{i}') for i in range(y)]
        self.row = [Net(f'row_{i}') for i in range(y)]

        for r in range(y):
            for c in range(x):

                # On triangular board we remove a triangular section of LEDs from the logical 
                # square matrix arangement, This aids in routing the mess on a 4L board with 
                # through holes.
                if c >= (15 - r):
                    default_circuit.parts.remove(self.leds[r*x + c])
                    continue

                self.leds[r*x + c][4,3,2] += self.col_r[c],self.col_g[c],self.col_b[c]
                self.leds[r*x + c][1] += self.row[r]

def d20_generate_design():
    #===============================================================================
    # Component templates.
    #===============================================================================

    shift = Part('74xx', '74HC595', dest=TEMPLATE, footprint='Led_Panel:TSSOP-16_slim')
    shift.fields['pn'] = '74HC595PW\,118'
    shift.fields['mfg'] = 'Texas Instruments'
    shift.fields['pn_alt0'] = 'HC595 (TSSOP-16)'
    shift.fields['mfg_alt0'] = 'Various'

    conn = Part('Connector_Generic_Shielded', 'Conn_01x06_Shielded', dest=TEMPLATE, footprint='Led_Panel:5034800600')
    conn.fields['pn'] = '5034800600'
    conn.fields['mfg'] = 'molex'
    conn.fields['pn_alt0'] = 'FH34SRJ-6S-0.5SH(50)'
    conn.fields['mfg_alt0'] = 'Hirose'

    cap = Part('Device', 'C', dest=TEMPLATE, footprint='Capacitor_SMD:C_0402_1005Metric')
    rgb = Part('Device', 'LED_ARGB', dest=TEMPLATE, footprint='Led_Panel:LED_1515_RBGA_slim')
    rgb.fields['pn'] = 'MHPA1515RGBDT'
    rgb.fields['mfg'] = 'MEIHUA' 

    pmos = Part('Device', 'Q_PMOS_GSD', dest=TEMPLATE, footprint='Package_TO_SOT_SMD:SOT-883', value='LP0404N3T5G')
    pmos.fields['pn'] = 'LP0404N3T5G'
    pmos.fields['mfg'] = 'LRC'

    res = Part('Device', 'R', dest=TEMPLATE, footprint='Resistor_SMD:R_0402_1005Metric')

    tlc59025 = Part('Led_Panel', 'TLC59025', dest=TEMPLATE, footprint='Led_Panel:SSOP-24_slim')
    tlc59025.fields['pn'] = 'SM16206S'
    tlc59025.fields['mfg'] = 'Sunmoon Micro'

    buff = Part('Led_Panel', 'NC7WZ17', dest=TEMPLATE, footprint='Led_Panel:UDFN-6_1x1mm_P0.35mm')
    buff.fields['pn'] = 'NC7WZ17FHX'
    buff.fields['mfg'] = 'onsemi / Fairchild'
    buff.fields['pn_alt0'] = '74LVC2G34FW5-7'
    buff.fields['mfg_alt0'] = 'Diodes Inc'

    vcc, gnd = Net('vcc', drive=POWER), Net('gnd', drive=POWER)

    # input connecions
    sclk_in, latch_in, blank_in, data_in = Net('sclk_i'), Net('latch_i'), Net('blank_i'), Net('dat_i')
    sclk, latch, blank, data = Net('sclk'), Net('latch'), Net('blank'), Net('dat')

    #output connections
    data_out = Net('dat_out')

    #===============================================================================
    # Component instantiations.
    #===============================================================================

    bypass = cap(3, value='470nF', pn='CC0402KRX5R6BB474', mfg='Yageo')
    for c in bypass:
        c[1,2] += vcc, gnd

    inputConnector = conn(value='input')
    outputConnector = conn(value='output')


    inputConnector[1] & vcc
    inputConnector[2] & data_in
    inputConnector[3] & blank_in
    inputConnector[4] & latch_in
    inputConnector[5] & sclk_in
    inputConnector[6] & gnd
    inputConnector['Shield'] & gnd

    outputConnector[1] & vcc
    outputConnector[2] & data_out
    outputConnector[3] & blank
    outputConnector[4] & latch
    outputConnector[5] & sclk
    outputConnector[6] & gnd
    outputConnector['Shield'] & gnd
    
    # Matrix Size 
    x = 16
    y = 15

    array = matrix(x,y, rgb)
    drivers = tlc59025(3)

    row_driver = shift(2)
    row_pmos = pmos(y)

    # attach resistors to drivers (Preliminary values)
    values = [
        {'r':'2.2k',  'pn':'RC0402FR-072K2L',  'mfg':'Yageo'},
        {'r':'7.5k',  'pn':'RC0402FR-077K5L',  'mfg':'Yageo'},
        {'r':'4.12k', 'pn':'RC0402FR-074K12L', 'mfg':'Yageo'}]
    i_set = res(3)
    for r,d,v in zip(i_set,drivers, values):
        r.value = v['r']
        r.pn = v['pn']
        r.mfg = v['mfg']

        Net(f'{d.ref}_r_ext') & r[1] & d['R-EXT']
        r[2] & gnd

        # Misc Pins
        d['VDD','GND'] += vcc, gnd
        d['CLK', 'LE', '~{OE}'] += sclk, latch, blank
    
    # connect common signals
    for rd in row_driver:
        rd['SRCLK', 'RCLK', '~{OE}', '~{SRCLR}'] += sclk, latch, gnd, vcc
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

    driver_list = [f'OUT{i}' for i in range(15)]
    drivers[0][driver_list] += array.col_r[0:15]
    drivers[1][driver_list] += array.col_g[0:15]
    drivers[2][driver_list] += array.col_b[0:15]

    drivers[0]['OUT15'] += NC
    drivers[1]['OUT15'] += NC
    drivers[2]['OUT15'] += NC

    for p,anode,driver in zip(row_pmos[0:8],array.row[0:8],row_driver[0][[f'Q{ascii_uppercase[idx]}' for idx in range(8)]]):
        Net(f's{anode.name}') & p['G'] & driver
        p['D'] += anode
        p['S'] += vcc
    for p,anode,driver in zip(row_pmos[8:15],array.row[8:15],row_driver[1][[f'Q{ascii_uppercase[idx]}' for idx in range(7)]]):
        Net(f's{anode.name}') & p['G'] & driver
        p['D'] += anode
        p['S'] += vcc
    # Unused pin
    row_driver[1]['QH'] & NC

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

def generate_bom(file):
    parts = []
    netlist = ''
    def equal_dicts(d1, d2, ignore_keys):
        d1_filtered = {k:v for k,v in d1.items() if k not in ignore_keys}
        d2_filtered = {k:v for k,v in d2.items() if k not in ignore_keys}
        return d1_filtered == d2_filtered
    def get_unique(part):
        unique_parts = []
        for p in parts:
            skip = False
            for _p in unique_parts:
                if equal_dicts(p,_p,('ref', 'value')):
                    _p['ref'] += p['ref']
                    skip = True
                    break
            if skip:
                continue
            unique_parts += [dict(p)]
        
        for p in unique_parts:
            p['qty'] = len(p['ref'])
            p['ref'] = ",".join(p['ref'])
        return unique_parts

    def bom_line(self):
        return {
            'ref': [self.ref],
            'value':self.value_str, 
            'name':self.name, 
            'pn': getattr(self, 'pn', ''),
            'mfg': getattr(self, 'mfg', ''),
            'pn_alt0': getattr(self, 'pn_alt0', ''),
            'mfg_alt0': getattr(self, 'mfg_alt0', ''),
        }
        
    for p in default_circuit.parts:
        _p = bom_line(p)
        parts += [_p]


    u = get_unique(parts)
    with open(file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = ['qty', 'ref', 'value', 'name', 'pn', 'mfg', 'pn_alt0', 'mfg_alt0'])
        writer.writeheader()
        writer.writerows(u)

    

#===============================================================================
# Instantiate the circuit and generate the netlist.
#===============================================================================

if __name__ == "__main__":
    d20_generate_design()
    ERC()
    generate_netlist()
    
    # Create a BOM
    generate_bom('../Production/d20_tri_r1.0.csv')
