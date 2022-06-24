# To run, open the KiCad scripting console and type: exec(open('pcbnew_placement.py').read())
# 
# This script will re-position D[1-1024] into a matrix filling the specified width and height, at the location provided below.
# After running you will have to press F11/F12 to force the screen to re-render.

import sys
from pcbnew import *
pcb = GetBoard()

spacingX = FromMM(2.246)
spacingY = 0-FromMM(1.946)

initialX = FromMM(102) + spacingX/2
initialY = FromMM(116) - FromMM(1.69)

count = 15


print(f'Spacing X,Y = {spacingX},{spacingY}')


nCount = 0

print('Start Place')
for y in range(count):
    for x in range(count):
        Ref = f'D{1 + x*15+y}'
        nCount = nCount + 1

        x_offset = ((y-1)/2) * spacingX
        #print(Ref)
        try:
            nPart = pcb.FindModuleByReference(Ref)
            nPart.SetPosition(wxPoint(initialX - x*spacingX + x_offset, initialY + y*spacingY))  # Update XY
        except:
            print(f'Error {Ref} (x,y) = {x},{y}')
            pass

        if x == y:
            break;
        
        
print('Finished Place')

