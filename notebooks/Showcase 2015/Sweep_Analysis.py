# -*- coding: utf-8 -*-
"""
Created on Fri Jan 30 13:50:37 2015

@author: jamesb
"""

import argparse
import psycopg2
import h5py
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
import os
import csv
import scipy.signal as sg
import Image
from allensdk.core.nwb_data_set import NwbDataSet

#import etay_extractor as fx
# def getSpecList():
#     conn = psycopg2.connect('host=limsdb2 dbname=lims2 user=limsreader password=limsro')
#     cur = conn.cursor()
#     cur.execute("SELECT err.workflow_state, spc.name FROM ephys_roi_results err JOIN ephys_specimen_roi_plans esrp\
#                 ON err.ephys_specimen_roi_plan_id = esrp.id JOIN specimens spc ON esrp.specimen_id = spc.id\
#                 WHERE err.workflow_state in('auto_passed','manual_passed')")
#     specs = [err[1] for err in cur.fetchall()]
#     print specs
#     for spec in specs:
#         plotSweeps(spec+".01")

def get_Reses(start_time, i):

    BLa = []
    Peaka = []
    SSta = []

    BLa.append(np.mean(i[((start_time - 10)*200):((start_time - 5)*200)]))
    Peaka.append(max(i[((start_time - 5)*200):((start_time + 10)*200)]))
    SSta.append(np.mean(i[((start_time + 7)*200):((start_time + 9)*200)]))

    BLa.append(np.mean(i[((start_time - 10 + 60)*200):((start_time - 5 + 60)*200)]))
    Peaka.append(max(i[((start_time - 5 + 60)*200):((start_time + 10 + 60)*200)]))
    SSta.append(np.mean(i[((start_time + 7 + 60)*200):((start_time + 9 + 60)*200)]))

    BLa.append(np.mean(i[((start_time - 10 + 120)*200):((start_time - 5 + 120)*200)]))
    Peaka.append(max(i[((start_time - 5 + 120)*200):((start_time + 10 + 120)*200)]))
    SSta.append(np.mean(i[((start_time + 7 + 120)*200):((start_time + 9 + 120)*200)]))

    Peaka_mean = np.mean(Peaka)
    SSta_mean = np.mean(SSta)
    BLa_mean = np.mean(BLa)
   
    Peak_R = 10000/(Peaka_mean - BLa_mean)
    SSt_R = 10000/(SSta_mean - BLa_mean)
  
    return Peak_R, SSt_R


def Find_Critical_Sweeps(specimen):
    conn = psycopg2.connect('host=limsdb2 dbname=lims2 user=limsreader password=limsro')
    cur = conn.cursor()
    
    cur.execute("SELECT s.name, s.ephys_roi_result_id, s.id FROM specimens s WHERE s.name LIKE %s", ('%' + specimen,))
    result = cur.fetchone()
    if result is None:
        print "Could not find specimen result for " + specimen + ". Skipping..."
        return None
    print "Specimen: " + result[0]
    # print "EphysRoiResult: " + str(result[1])
    specimen_name = result[0]
    ephys_roi_result_id = result[1]
    specimen_id = result[2]
    
    cur.execute("SELECT f.filename, f.storage_directory FROM well_known_files f \
                 WHERE f.attachable_type = 'EphysRoiResult' AND f.attachable_id = %s AND f.filename LIKE '%%nwb'", 
                 (ephys_roi_result_id,))
    result = cur.fetchone()

    if result is None:
        print "Could not find orca or nwb file for " + specimen + ". Skipping..."
        return None
    WinP = LinuxtoWindow(result[1])
    nwb_path = WinP + result[0]
    
    cur.execute("SELECT sw.sweep_number FROM ephys_sweeps sw JOIN ephys_stimuli stim \
                ON stim.id = sw.ephys_stimulus_id\
                WHERE sw.specimen_id = %s AND stim.description SIMILAR TO '%%C1%%|%%C2%%'AND sw.workflow_state SIMILAR TO '%%pass%%|%%fail%%'", 
                (specimen_id,))
    Pass_sweeps = [s[0] for s in cur.fetchall()]
    Pass_sweeps.sort()
    last = Pass_sweeps[(len(Pass_sweeps)-1)]
    mid = Pass_sweeps[(len(Pass_sweeps)/2)]
    #Get the sweep number for position = length and position length/2
    #Return the leak current for these 2 sweeps

    cur.execute("SELECT sw.leak_pa FROM ephys_sweeps sw \
         WHERE sw.specimen_id = %s AND sw.sweep_number = %s", (specimen_id, last))
    last_bias = cur.fetchone()
    if last_bias[0] is None:
        last_bias = [0.0,]

    cur.execute("SELECT sw.leak_pa FROM ephys_sweeps sw \
         WHERE sw.specimen_id = %s AND sw.sweep_number = %s", (specimen_id, mid))
    mid_bias = cur.fetchone()
    if mid_bias[0] is None:
        mid_bias = [0.0,]



    cur.execute("SELECT sw.stimulus_amplitude FROM ephys_sweeps sw JOIN ephys_stimuli stim \
                ON stim.id = sw.ephys_stimulus_id\
                WHERE sw.specimen_id = %s AND stim.description LIKE '%%C1SSF%%' AND sw.num_spikes = '1'", 
                (specimen_id,))
    SS_Amps = [s[0] for s in cur.fetchall()]

    if not SS_Amps:
        SS_return = 'error'
    elif SS_Amps[0] is None:
        SS_return = 'error'
    else:
        SS_return = min(SS_Amps)
   
    cur.execute("SELECT sw.sweep_number FROM ephys_sweeps sw JOIN ephys_stimuli stim \
                ON stim.id = sw.ephys_stimulus_id\
                WHERE sw.specimen_id = %s AND stim.description LIKE '%%EXTPINBATH%%'", 
                (specimen_id,))
    Bath_sweeps = [s[0] for s in cur.fetchall()]

    if not Bath_sweeps:
        Bath_return = 'error'
    elif Bath_sweeps[0] is None:
        Bath_return = 'error'
    else:
        Bath_return = max(Bath_sweeps)

    cur.execute("SELECT sw.sweep_number FROM ephys_sweeps sw JOIN ephys_stimuli stim \
                ON stim.id = sw.ephys_stimulus_id\
                WHERE sw.specimen_id = %s AND stim.description LIKE '%%EXTPBREAKN%%'", 
                (specimen_id,))
    Breakin_sweeps = [s[0] for s in cur.fetchall()]

    if not Breakin_sweeps:
        Breakin_return = 'error'
    elif Breakin_sweeps[0] is None:
        Breakin_return = 'error'
    else:
        Breakin_return = max(Breakin_sweeps)

    cur.execute("SELECT sw.sweep_number FROM ephys_sweeps sw JOIN ephys_stimuli stim \
                ON stim.id = sw.ephys_stimulus_id\
                WHERE sw.specimen_id = %s AND stim.description LIKE '%%EXTPEXPEND%%'", 
                (specimen_id,))
    End_sweeps = [s[0] for s in cur.fetchall()]

    if not End_sweeps:
        End_return = 'error'
    elif End_sweeps[0] is None:
        End_return = 'error'
    else:
        End_return = max(End_sweeps)

    cur.execute("SELECT sw.sweep_number FROM ephys_sweeps sw JOIN ephys_stimuli stim \
                ON stim.id = sw.ephys_stimulus_id\
                WHERE sw.specimen_id = %s AND stim.description LIKE '%%EXTPGGAEND%%'", 
                (specimen_id,))
    Giga_sweeps = [s[0] for s in cur.fetchall()]

    if not Giga_sweeps:
        Giga_return = 'error'
    elif Giga_sweeps[0] is None:
        Giga_return = 'error'
    else:
        Giga_return = max(Giga_sweeps)
    
    # load_experiment(nwb_path, max(Breakin_sweeps))

    return nwb_path, Bath_return, Breakin_return, End_return, Giga_return, last_bias[0], mid_bias[0], SS_return, specimen_name
        

def load_experiment(specimen):

    path, bath, breakin, end, giga, last_bias, mid_bias, SS_amp, spec_name = Find_Critical_Sweeps(specimen)

    ds = NwbDataSet(path)

    if bath is 'error':
        bath_peak = 9999999
        bath_ss = 9999999
    else:
        bath_sweep = ds.get_sweep(bath)
        bath_i = bath_sweep['response'] * 1e12
        bath_peak, bath_ss = get_Reses(70, bath_i)

    if breakin is 'error':
        breakin_peak = 9999999
        breakin_ss = 9999999
    else:
        breakin_sweep = ds.get_sweep(breakin)
        breakin_i = breakin_sweep['response'] * 1e12
        breakin_peak, breakin_ss = get_Reses(70, breakin_i)

    if end is 'error':
        end_peak = 9999999
        end_ss = 9999999
        end_leak = 9999999
    else:
        end_sweep = ds.get_sweep(end)
        end_i = end_sweep['response'] * 1e12
        end_peak, end_ss = get_Reses(70, end_i)
        end_leak = np.mean(end_i[0:100])


    if giga is 'error':
        giga_peak = 9999999
        giga_ss = 9999999
    else:
        giga_sweep = ds.get_sweep(giga)
        giga_i = giga_sweep['response'] * 1e12
        giga_peak, giga_ss = get_Reses(70, giga_i)

    features = []
    features.append(spec_name)
    features.append(bath_ss)
    features.append(breakin_peak)
    features.append(breakin_ss)
    features.append(end_peak)
    features.append(end_ss)
    features.append(end_leak)
    features.append(giga_ss)
    features.append(last_bias)
    features.append(mid_bias)
    features.append(SS_amp)

    return features


    
def LinuxtoWindow(Linuxpath):
    SplitLinux = Linuxpath.split('/')
    #I should be able to link to \\titan, but I can't figure it out, so I mapped //titan/cns to y:    
    WindowsP = os.path.join('y:/','mousecelltypes',SplitLinux[4],SplitLinux[5],'')
    #WindowsP = os.path.join('\\titan','cns','mousecelltypes',SplitLinux[4],SplitLinux[5],'')    
    return (WindowsP)
    

with open('speclist3.csv', "rb") as csvfile:

    FeatSumm = ['Name', 'R(electrode)', 'RS(init)', 'RI(init)', 'RS(final)', 'RI(final)', 'End_leak', 'Final_seal', 'Final_bias', 'Mid_bias', 'SS_amp']

    for specimen in csvfile:
     
        try:
            features = load_experiment(specimen.strip() + ".01")
            FeatSumm = np.vstack([FeatSumm,features])
        except:
            print  specimen.strip() + " has an error"

     

    myfile = open('c:/Summary_Sep21.csv', 'wb')
    wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
    for values in FeatSumm:
        wr.writerow(values)

myfile.close()    