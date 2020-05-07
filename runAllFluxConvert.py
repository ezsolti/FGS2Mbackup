#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run all flux convert and inventory runs

Things to change if rerun is needed:
    
    - path
    - volumesandmats.txt
"""

import matplotlib.pyplot as plt
import os
import numpy as np

outputfile='NESSA-Neutron-Openo'
path='NESSA0505open'
sourceRate=1e11 #1/s

materials={}
materials['11']={'density': 7.874, 'ref': 'ironRef'}
materials['12']={'density': 11.34, 'ref': 'leadRef'}
materials['3']={'density': 2.30, 'ref': 'concrete3Ref'}
materials['5']={'density': 0.96, 'ref': 'plasticRef'}
materials['6']={'density': 3.35, 'ref': 'concrete6Ref'}
materials['7']={'density': 3.9, 'ref': 'concrete7Ref'}

def tallyread(filename, tallynum):
    mcnpoutput = open(filename,'r')
    energy=[]
    flux=[]
    fluxerr=[]
    
    tallycellFlag=False
    tallyFlag=False
    for line in mcnpoutput:
        x=line.strip().split()
        if len(x)>=2 and x[0]=='1tally' and x[1]==str(tallynum):
            tallycellFlag=True
        if tallyFlag and x[0]=='total':
            total=float(x[1])
            totalerr=float(x[2])
            tallyFlag=False
        if tallyFlag:
            energy.append(float(x[0]))
            flux.append(float(x[1]))
            fluxerr.append(float(x[2]))   
        if tallycellFlag and len(x)==1 and x[0]!='volumes' and x[0]!='energy':
            volume=float(x[0])
        if tallycellFlag and len(x)>0 and x[0]=='energy':
            tallyFlag=True
            tallycellFlag=False
    return np.array(energy),np.array(flux),np.array(fluxerr),total,totalerr,volume


tallies=[line.strip().split()[1] for line in os.popen('grep 1tally %s'%outputfile).readlines() if line.strip().split()[1].isdecimal()]
tally={}
#plt.figure()
for i in tallies:
    tally[i]={}
    tally[i]['energy'],tally[i]['flux'],tally[i]['error'],tally[i]['total'],tally[i]['totalerr'],tally[i]['volume']=tallyread('%s'%outputfile,i)
    if i not in ['4','14','24','34']:
        volmat=os.popen('grep -w %s volumesandmats.txt'%i[:-1]).readlines()[0].strip().split()
        tally[i]['mat']=volmat[2]
        tally[i]['density']=materials[volmat[2]]['density']
        tally[i]['mass']=tally[i]['volume']*tally[i]['density']
    elif i =='14':
        volmat=os.popen('grep -w %s volumesandmats.txt'%1310).readlines()[0].strip().split()
        tally[i]['mat']=volmat[2]
        tally[i]['density']=materials[volmat[2]]['density']
        tally[i]['mass']=tally[i]['volume']*tally[i]['density']
    elif i =='24':
        volmat=os.popen('grep -w %s volumesandmats.txt'%2430).readlines()[0].strip().split()
        tally[i]['mat']=volmat[2]
        tally[i]['density']=materials[volmat[2]]['density']
        tally[i]['mass']=tally[i]['volume']*tally[i]['density']
    elif i =='34':
        volmat=os.popen('grep -w %s volumesandmats.txt'%2060).readlines()[0].strip().split()
        tally[i]['mat']=volmat[2]
        tally[i]['density']=materials[volmat[2]]['density']
        tally[i]['mass']=tally[i]['volume']*tally[i]['density']
    else:
        volmat=os.popen('grep -w %s volumesandmats.txt'%2310).readlines()[0].strip().split()
        tally[i]['mat']=volmat[2]
        tally[i]['density']=materials[volmat[2]]['density']
        tally[i]['mass']=tally[i]['volume']*tally[i]['density']
    print('-----')
    print(sum(tally[i]['flux']),tally[i]['total'],tally[i]['totalerr'])
    print(tally[i]['volume'])
    print(tally[i]['mass'])
    print(tally[i]['density'])
    print(tally[i]['mat'])
    if tally[i]['totalerr']<1/100:
        tally[i]['fluxes']='/home/zsolt/FISPACT-II/%s/flux_convert_tally%s/fluxes'%(path,i)
    else:
        tally[i]['fluxes']='/home/zsolt/FISPACT-II/%s/flux_convert_tally%s/fluxes'%(path,'30004')
    
    
#####
#
# FLux convert runs
#
#####

for i in tally.keys():
    en=np.flip(1e6*tally[i]['energy'])
    flux=np.flip(tally[i]['flux'][1:]) #dropping the 710th group 0-1e-11
    arbstr=''
    for eg in en:
        arbstr+='%.4e\n'%eg
    for fl in flux:
        arbstr+='%.4e\n'%fl
    arbstr+='1.00\nNessa Spectrum'
    
    os.chdir('/home/zsolt/FISPACT-II/%s'%path)
    os.mkdir('flux_convert_tally%s'%i)
    os.system('cp fluxconvertRef/files.convert flux_convert_tally%s/files.convert'%i)
    os.system('cp fluxconvertRef/convert.i flux_convert_tally%s/convert.i'%i)
    os.system('cp fluxconvertRef/fisprun.sh flux_convert_tally%s/fisprun.sh'%i)
    
    filename='flux_convert_tally%s/arb_flux'%i
    arbfile=open(filename,'w')
    arbfile.write(arbstr)
    arbfile.close()
    
    os.chdir('/home/zsolt/FISPACT-II/%s/flux_convert_tally%s'%(path,i))
    os.system('./fisprun.sh')


#####
#
# Inventory runs
#
#####

for i in tally.keys():
    
    os.chdir('/home/zsolt/FISPACT-II/%s'%path)
    os.mkdir('inventory%s'%i)
    os.system('cp collapse.i inventory%s/collapse.i'%i)
    os.system('cp condense.i inventory%s/condense.i'%i)
    os.system('cp print_lib.i inventory%s/print_lib.i'%i)
    os.system('cp fisprun.sh inventory%s/fisprun.sh'%i)
    os.system('cp files inventory%s/files'%i)
    
    os.system('cp %s inventory%s/fluxes'%(tally[i]['fluxes'],i))
    
    with open ('/home/zsolt/FISPACT-II/%s/'%path+materials[tally[i]['mat']]['ref'], "r") as reffile:
        inpRef=reffile.read()
        
    inpRef=inpRef.replace('MassStr',str(tally[i]['mass']/1000))
    
    fluxi=sourceRate*(tally[i]['total']+tally[i]['total']*tally[i]['totalerr'])
    inpRef=inpRef.replace('FluxStr',str(fluxi))
    
    filename='inventory%s/inventory.i'%i
    invfile=open(filename,'w')
    invfile.write(inpRef)
    invfile.close()
    
    print('-----------------')
    print(i)
    print('-----------------')
    os.chdir('/home/zsolt/FISPACT-II/%s/inventory%s'%(path,i))
    os.system('./fisprun.sh')
    os.system('rm ARRAYX')
    os.system('rm COLLAPX')


