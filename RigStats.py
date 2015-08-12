
"""
Created on Thu Jun 04 21:05:21 2015

@author: Aaron

"""

import csv
import matplotlib.pyplot as plt
from datetime import *
import numpy as np


users = ['Aaron Oldre','DiJon Hill','Kristen Trett','Rusty Mann']
days= [0,0,0,0,0]
days_count=[0,0,0,0,0]
cell_count=[0,0,0,0,0]
pipette_count=[0,0,0,0,0]
good_cell_count=[0,0,0,0,0]
bad_cell_count=[0,0,0,0,0]
day_room=0
pipette_std=[]
#where all data is currently stored. I would like to eventually be able to 
#directly access PWA for this
csv_file = 'IVSCC_PWA.csv'



with open(csv_file) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            in_date = (row['Created']).split('/')
            mon=in_date[0] #7
            day=in_date[1] #22
            in_date=in_date[2].split(' ')
            year=in_date[0] #2014
            in_date=date(int(year),int(mon),int(day))
            if in_date > date(2015,1,1):
                if day_room != in_date:
                    day_room = in_date
                    pipette_std.append(1)
                elif day_room == in_date:
                    pipette_std[len(pipette_std)-1] += 1
                users.index(row['Created By'])
                user = users.index(row['Created By'])
                pipette_count[user]+=1
                if days[user] != in_date:
                    days[user] = in_date
                    days_count[user] += 1
                if row['Patched Cells'] == '1':
                    good_cell_count[user] +=1
                if row['Patched cells (human)'] == '1':
                    cell_count[user] +=1
                if row['Patched cells (Practice)'] == '1':
                    bad_cell_count[user] +=1
        except ValueError:
            pass

csvfile.close()

for i in range(len(users)):
    print users[i]
    print 'Days on Rig '  + str(days_count[i])
    cell_count[i] = cell_count[i]+good_cell_count[i]+bad_cell_count[i]
    print 'Cells Patched ' + str(cell_count[i])
    print 'Usable Cells ' + str(good_cell_count[i])
    print 'Bad Cells ' + str(bad_cell_count[i])
    print 'Pipettes Used ' + str(pipette_count[i])
    print 'Pipettes per cell ' + str(float(pipette_count[i])/float(cell_count[i]))
    print 'Pipettes per day ' + str(float(pipette_count[i])/float(days_count[i]))
    print 'Cells per day ' + str(float(cell_count[i])/float(days_count[i]))
    print ' '
    
print 'Room Pipette Avg ' + str(np.average(pipette_std))
print 'Room Pipette Std ' + str(np.std(pipette_std))
