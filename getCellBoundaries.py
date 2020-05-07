#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 17:04:12 2020

@author: zsolt
"""

surfaces={}
for i in tallies:
    if i not in ['4','14','24','34']:
        cline=os.popen('grep -P "(^|\s)\K%s(?=\s|$)" cellzsNew'%i[:-1]).readlines()
        for cl in cline:
            x=cl.strip().split()
            if x[0]==i[:-1]:
                print(cl)
                surfaces[i]=cl[:cl.find('IMP:N')].strip().split()[3:]
                print(surfaces[i])
                print('-------')

limits={}
for key in surfaces:
    if len(surfaces[key])==6:
        limits[key]={'X':[0,0],'Y':[0,0],'Z':[0,0]}
        for s in surfaces[key]:
            if s[0] == '-':
                #sl=os.popen('grep -P "(^|\s)\K%s(?=\s|$)" surfnew'%s[1:]).readlines()[0].strip().split()
                sl=os.popen('grep "^%s\\b" surfnew'%s[1:]).readlines()[0].strip().split()
                #sl = 3010   PX   -40                  $ Left wall (inner)
                #sl[1][1] = X
                limits[key][sl[1][1]][1]=float(sl[2])
            else:
                #sl=os.popen('grep -P "(^|\s)\K%s(?=\s|$)" surfnew'%s).readlines()[0].strip().split()
                sl=os.popen('grep "^%s\\b" surfnew'%s).readlines()[0].strip().split()
                limits[key][sl[1][1]][0]=float(sl[2])
    elif len(surfaces[key])==1:
        limits[key]={'X':[0,0],'Y':[0,0],'Z':[0,0]}
        sl=os.popen('grep -P "(^|\s)\K%s(?=\s|$)" surfnew'%surfaces[key][0][1:]).readlines()[0].strip().split()
        print(sl)
        limits[key]['X']=[float(sl[2]),float(sl[3])]
        limits[key]['Y']=[float(sl[4]),float(sl[5])]
        limits[key]['Z']=[float(sl[6]),float(sl[7])]
    else:
        print(key)
        
limits['23104']={'X':[180,280],'Y':[385,425],'Z':[0,240]}
