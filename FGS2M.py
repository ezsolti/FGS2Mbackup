#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FGS2M module
"""
import numpy as np

def isFloat(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def addStr(old,new):
    #TODO try if it is string
    lastN=old.rfind('\n') #last occurance of \n, returns -1 if not present
    if len(old[lastN+1:]+new+' ') >= 80:
        return old+'\n     '+new+' '
    else:
        return old+new+' '

class Cell(object):
    """A class used to represent an MCNP cell in which the neutron spectrum was
    tallied and a subsequent FISPACT-II calculation was run to obtain the
    emission gamma spectrum of the cell.
    Parameters
    ----------
    *args : str
      Cell ID number
    Attributes
    ----------
    name : str
        ID of the cell
    density : float
        density of material filled in cell (g/cm3)
    mass : float
        mass of material filled in cell (g)
    volume : float
        volume of material filled in cell (cm3)
    inventory : str
        path to FISPACT-II inventory.out like file
    """

#TODO def fromDict():
    
    def __init__(self, name, inventory='',volume='',x=[],y=[],z=[]):
        if isinstance(name, str):
            self._name = name
        else:
            raise ValueError('name has to be number as a str')
            
        self._volume = volume #TODO, could be set_volume here
        self._mass = None
        self._density = None
        self._inventory=inventory
        self._x=x  #TODO add property, add set functions, set_coord, set_x, set_y, set_z
        self._y=y
        self._z=z
        self._gammaspectrum=[] #TODO not used. maybe a large dict for all ct should be scraped upon init?

    def __repr__(self):
        return "Cell #%s" %(self._name)

    @property
    def name(self):
        return self._name

    @property
    def mass(self):
        return self._mass

    @property
    def volume(self):
        return self._volume

    @property
    def density(self):
        return self._density

    @property
    def inventory(self):
        return self._inventory

    def set_volume(self, volume=None): #TODO: give unit with 'cm3', 'm3' etc
        """The function to set the density of the Material
        Parameters
        ----------
        density : float
            volume of material in cm3
        """

        if isFloat(volume):
            self._volume=volume
        else:
            raise ValueError('Volume has to be float for Cell')

    def set_density(self, density=None):
        """The function to set the density of the Material
        Parameters
        ----------
        density : float
            density of material in g/cm3
        """

        if isFloat(density):
            self._density=density
        else:
            raise ValueError('density has to be float for Cell')

    def set_inventory(self, path=None):
        """The function to set the path to Fispact-II inventory.out
        Parameters
        ----------
        path : str
            the path of the file.
        """
        if isinstance(path, str):
            self._path=path
        else:
            raise ValueError('Path has to be str')

#TODO : extend it to irradiation times
#TODO: list all available irradiation and cdelIDsFromDictooling times
    def getGS(self, ct):
        """Function extracts GS from output at cooling time ct
        If ct is not available in the output, it returns empty list.
        
        ct : float
           cooling time in seconds
           
        >>> import matplotlib.pyplot as plt
        >>> a,b=getGSzs(filename,60)
        >>> plt.stem(a[1:],b)
        """
        
        times={'s':1,'m':60,'h':60*60,'d':60*60*24}
        output=open(self.inventory, 'r')
        energy=[]
        elows=[]
        ehighs=[]
        rate=[]
        tallycellFlag=False
        tallyFlag=False
        for line in output:
            
            x=line.strip()
            if "COOLING TIME IS" in x:
                n, m = x.find('ELAPSED TIME IS'), x.find('* * * FLUX AMP IS')
                tstr=x[n+len('ELAPSED TIME IS'):m].strip().split()
                t=float(tstr[0])*times[tstr[1]]
                if np.abs(ct-t)<=1e-7:
                    tallycellFlag=True
            if tallyFlag and len(x)==0:
                tallyFlag=False    
            if tallyFlag:
                #MORE DIFFICULT
                n,m = x.find('('), x.find('MeV)') #energy in (  0.000-  0.010 MeV) format
                ebin=x[n+1:m].strip().split()
                elows.append(float(ebin[0][:-1]))
                ehighs.append(float(ebin[1]))
                rate.append(float(x.split()[-1]))
            if tallycellFlag and 'TOTAL GAMMA POWER' in x:
                tallyFlag=True
                tallycellFlag=False
        if len(rate)==0:
            print('Cooling time is not present')
            return [],[]
        else:
            energy=elows
            energy.append(ehighs[-1])
            return energy, rate




class Source(object):
    """Collectiction of Cells for which the sdef has to be created"""
    #TODO a lot, probably i need nicer add_cell etc functions
    
    def __init__(self, *argv):
        self._cells=[]
        for arg in argv:
            if not isinstance(arg,Cell):
                 raise TypeError('Inputs need to be Cell() objects')
            else:
                self._cells.append(arg)

    @property
    def cells(self):
        return self._cells
                
    def createSDEF(self,ct):
        """creates an sdef card for cooling time ct"""
        #the header of the string is fix.
        N=len(self._cells)
        sdefStr='SDEF CEL=d1 X=FCEL d2 Y=FCEL d3 Z=FCEL d4 ERG=FCEL d5 PAR=P\n'
        sdefStrW='     WGT=%f\n'
        SI1='SI1 L '
        SP1='SP1   '
        DS2='DS2 S '
        DS3='DS3 S '
        DS4='DS4 S '
        DS5='DS5 S '
        Sref='S'
        DX=''
        DY=''
        DZ=''
        DE=''
        j=6
        totwgt=0
        datadict={}
        for cell in self._cells:
            energy, rate = cell.getGS(ct)
            rate.insert(0,0.0) #needed to match length, mcnp wants 0 at the beginning
            if abs(sum(rate))>=1e-7:
                datadict[cell.name]={'gs':{'energy':energy,'rate':rate},'total':sum(rate),'totalv':sum(rate)*cell._volume}
                SI1 = addStr(SI1,cell.name)
                SP1 = addStr(SP1,str(sum(rate)*cell._volume)) #TODO check! What if volume is not given?
                totwgt=totwgt+sum(rate)*cell._volume
                DS2 = addStr(DS2,str(j))
                DX=DX+'SI%d %.2f %.2f \nSP%d 0 1\n'%(j,cell._x[0],cell._x[1],j)
                
                DS3 = addStr(DS3,str(j+N))
                DY=DY+'SI%d %.2f %.2f \nSP%d 0 1\n'%(j+N,cell._y[0],cell._y[1],j+N)
                
                DS4 = addStr(DS4,str(j+2*N))
                DZ=DZ+'SI%d %.2f %.2f \nSP%d 0 1\n'%(j+2*N,cell._z[0],cell._z[1],j+2*N)
                
                DS5 = addStr(DS5,str(j+3*N))
                SIE='SI%d H '%(j+3*N)
                SPE='SP%d D '%((j+3*N))
                for e,r in zip(energy,rate):
                    SIE=addStr(SIE,str(e))
                    SPE=addStr(SPE,str(r))
                DE=DE+SIE+'\n'+SPE+'\n'
                
                j+=1
                
        #Bringing everything together
        sdefStr=sdefStr+sdefStrW%totwgt+'%s\n%s\n%s\n%s%s\n%s%s\n%s%s\n%s'%(SI1,SP1,DS2,DX,DS3,DY,DS4,DZ,DS5,DE)
        return sdefStr,datadict
            
            
    

    
if __name__ == "__main__":
    #unittest.main()
    ending='/inventory.out'
    path='/home/zsolt/FISPACT-II/NESSA0505open/'
#    iron2265=Cell('2265',volume=6.00000E+05,
#                  x=[80,180],y=[385,425],z=[0,140],inventory=path+'2020_IronFrontWall_RPIrradiation'+ending)
#    iron2310=Cell('2310',volume=947433.6293856408,
#                  x=[180,280],y=[385,425],z=[0,240],inventory=path+'2020_IronFrontWall_RPIrradiation'+ending)
#    lead2430=Cell('2430', volume=3.32500E+05,
#                  x=[270,280],y=[242.5,382.5],z=[0,237.5],inventory=path+'2020_LeadInnerBunker_RPIrradiation'+ending)
#    source=Source(iron2265,iron2310,lead2430)
#    print(source.createSDEF(60))
    source=Source()
    for i in tally:  #comes from runAllFluxConvert for example, limits from getCellBoundaries
        if i not in ['4','14','24','34']:
            source._cells.append(Cell(i[:-1],volume=tally[i]['volume'],
                                      x=limits[i]['X'],
                                      y=limits[i]['Y'],
                                      z=limits[i]['Z'],
                                      inventory=path+'inventory%s'%i+ending))
    
    t={'1min':60,
       '10mins':10*60,
       '2hours':2*60*60,
       '1day':24*60*60,
       '7days':7*24*60*60,
       '100days':100*24*60*60}
    for ti in t:
        sdefStr,sdefdict=source.createSDEF(t[ti])
#        sdeffile=open('/run/user/1000/gvfs/sftp:host=galactica.physics.uu.se/home/elter/NESSA/mcnp202005/opencollimator/gamma/sdefzsOpen%s'%ti,'w')
#        sdeffile.write(sdefStr)
#        sdeffile.close()
        #print(sdefStr)
        #print('---------------------------')
        
        
        
        ####plot
        totals=[]
        for c in sdefdict:
            totals.append(sdefdict[c]['totalv'])
        
        import  matplotlib
        cmap = matplotlib.cm.get_cmap('Reds')
        print(max(totals))
        norm = matplotlib.colors.Normalize(vmin=min(np.log10(totals)), vmax=max(np.log10(totals)))
        plt.figure(figsize=(8,10))
        for c in sdefdict:
            col=cmap(norm(np.log10(sdefdict[c]['totalv'])), bytes=False)
            plt.loglog(sdefdict[c]['gs']['energy'][4:],sdefdict[c]['gs']['rate'][4:],c=col,label=c)
        plt.legend()
        plt.title(ti)
        plt.xlabel('Energy (MeV)')
        plt.ylabel('Gamma emission spectrum (gammas per cc per s)')
        plt.savefig('gammaspect_%s.png'%ti,dpi=300)
        plt.show()
        #####ROOM Source rate
        zcut=151
        fig = plt.figure(figsize=(10,14.1))
        ax = fig.add_subplot(1, 1, 1)
        minx=source._cells[0]._x[0]
        maxx=source._cells[0]._x[1]
        miny=source._cells[0]._y[0]
        maxy=source._cells[0]._y[1]
        
        for ce in source._cells:
            if ce.name in sdefdict:
                col=cmap(norm(np.log10(sdefdict[ce.name]['totalv'])), bytes=False)
            else:
                col='white'
            if min(ce._z)<zcut and max(ce._z)>zcut:
                polygon = plt.Polygon([[ce._x[0],ce._y[0]],[ce._x[1],ce._y[0]],[ce._x[1],ce._y[1]],[ce._x[0],ce._y[1]]],True,color=col,ec='black')
                ax.add_artist(polygon)
                if ce._x[0]<minx:
                    minx=ce._x[0]
                if ce._x[1]>maxx:
                    maxx=ce._x[1]
                if ce._y[0]<miny:
                    miny=ce._y[0]
                if ce._y[1]>maxy:
                    maxy=ce._y[1]
        for ce in source._cells:
            if min(ce._z)<zcut and max(ce._z)>zcut and ce.name in sdefdict:
                if ce._x[1]-ce._x[0]>=ce._y[1]-ce._y[0]:
                    plt.annotate('%.2e'%sdefdict[ce.name]['totalv'],((ce._x[0]+5),(ce._y[1]+ce._y[0])/2),size=12)
                else:
                    plt.annotate('%.2e'%sdefdict[ce.name]['totalv'],((ce._x[1]+ce._x[0])/2-4,(ce._y[1]+ce._y[0])/2+19),rotation=90,size=12)
        plt.xlim(minx,maxx)
        plt.ylim(miny,maxy)
        plt.title(ti)
        plt.savefig('sourceRateMap_%s.png'%ti,dpi=300)
        plt.show()
                
        #####ROOM Source rate XZ
        ycut=475
        fig = plt.figure(figsize=(10,14.1))
        ax = fig.add_subplot(1, 1, 1)
        minx=source._cells[0]._x[0]
        maxx=source._cells[0]._x[1]
        minz=source._cells[0]._z[0]
        maxz=source._cells[0]._z[1]
        
        for ce in source._cells:
            if ce.name in sdefdict:
                col=cmap(norm(np.log10(sdefdict[ce.name]['totalv'])), bytes=False)
            else:
                col='white'
            if min(ce._y)<ycut and max(ce._y)>ycut:
                polygon = plt.Polygon([[ce._x[0],ce._z[0]],[ce._x[1],ce._z[0]],[ce._x[1],ce._z[1]],[ce._x[0],ce._z[1]]],True,color=col,ec='black')
                ax.add_artist(polygon)
                if ce._x[0]<minx:
                    minx=ce._x[0]
                if ce._x[1]>maxx:
                    maxx=ce._x[1]
                if ce._z[0]<minz:
                    minz=ce._z[0]
                if ce._z[1]>maxz:
                    maxz=ce._z[1]
        for ce in source._cells:
            if min(ce._y)<ycut and max(ce._y)>ycut and ce.name in sdefdict:
                if ce._x[1]-ce._x[0]>=ce._z[1]-ce._z[0]:
                    plt.annotate('%.2e'%sdefdict[ce.name]['totalv'],((ce._x[0]+5),(ce._z[1]+ce._z[0])/2),size=12)
                else:
                    plt.annotate('%.2e'%sdefdict[ce.name]['totalv'],((ce._x[1]+ce._x[0])/2-4,(ce._z[1]+ce._z[0])/2+19),rotation=90,size=12)
        plt.xlim(minx,maxx)
        plt.ylim(minz,maxz)
        plt.title(ti)
        plt.savefig('sourceRateMapXZ_%s.png'%ti,dpi=300)
        plt.show()    