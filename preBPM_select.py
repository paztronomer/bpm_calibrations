import os
import sys
import time 
import logging
import numpy as np
import pandas as pd
import despydb.desdbi as desdbi
import scipy.spatial.distance as distance
#setup for display visualization
import matplotlib
#matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

class Toolbox():
    @classmethod
    def dbquery(cls,toquery,outdtype,dbsection='db-desoper',help_txt=False):
        '''the personal setup file .desservices.ini must be pointed by desfile
        DB section by default will be desoper
        '''
        desfile = os.path.join(os.getenv('HOME'),'.desservices.ini')
        section = dbsection
        dbi = desdbi.DesDbi(desfile,section)
        if help_txt: help(dbi)
        cursor = dbi.cursor()
        cursor.execute(toquery)
        cols = [line[0].lower() for line in cursor.description]
        rows = cursor.fetchall()
        outtab = np.rec.array(rows,dtype=zip(cols,outdtype))
        return outtab

    @classmethod
    def gband_select(cls,niterange):
        q = "with y as ("
        q += "    select fcut.expnum, max(fcut.lastchanged_time) as evaltime"
        q += "    from firstcut_eval fcut"
        q += "    where fcut.analyst!='SNQUALITY'"
        q += "    group by fcut.expnum )"
        q += " select e.nite,e.expnum,e.exptime,fcut.skybrightness,"
        q += "    fcut.accepted,e.band,att.reqnum,fcut.t_eff,fcut.fwhm_asec,"
        q += "    val.key,att.id,att.task_id,e.radeg,e.decdeg"
        q += " from y, exposure e, pfw_attempt_val val, firstcut_eval fcut,"
        q += "    pfw_attempt att "
        q += " where e.nite between {0} and {1}".format(*niterange)
        q += "    and e.band='g'"
        q += "    and val.key='expnum'"
        q += "    and fcut.expnum=e.expnum"
        q += "    and fcut.expnum=y.expnum"
        q += "    and fcut.lastchanged_time=y.evaltime"
        q += "    and to_number(val.val,'999999')=e.expnum"
        q += "    and val.pfw_attempt_id=att.id"
        q += "    and val.pfw_attempt_id=fcut.pfw_attempt_id"
        q += "    and fcut.program='survey'"
        q += "    and fcut.accepted = 'True'"
        q += "    and fcut.t_eff > 0.3"
        q += " order by e.nite"
        datatype = ['i4','i4','f4','f4','a10','a5','i4','f4','f4','a50','i4',
                'i4','f4','f4']
        tab = Toolbox.dbquery(q,datatype)
        return tab


class Refine():
    @classmethod
    def reduce_sample(cls,arr,label):
        '''Low skybrightness, separataion of at least 30 arcsec (0.0083 deg)
        Inputs:
        - arr: structured array coming from DB query
        '''
        #first selection: skybrightness below median of distribution
        arr = arr[arr['skybrightness']<=np.median(arr['skybrightness'])]
        
        #second selection: by its distance 
        #select with distance higher than 30 arcsec
        cumd = []
        neig = []
        idx = []
        for i in range(arr.shape[0]):
            d = []
            for m in range(arr.shape[0]):
                dist = np.linalg.norm(
                    np.array((arr['radeg'][i],arr['decdeg'][i]))-
                    np.array((arr['radeg'][m],arr['decdeg'][m])))
                d.append(dist)
            cumd.append(np.sum(d))
            neig.append(sorted(d)[1])
            if sorted(d)[1] > 0.00833:
                idx.append(i)
        cumd = np.array(cumd)
        neig = np.array(neig)
        #the above selection don't filter, maybe because of the observig
        #criteria in DES. All obey the condition

        #third selection: select 50 entries from a random sample, flat prob.
        per_nite = np.ceil(50/np.unique(arr['nite']).shape[0]).astype(int)
        np.random.seed(seed=19860312)
        expnum = []
        for n in np.unique(arr['nite'][:]):
            arr_aux = arr[arr['nite']==n]['expnum']
            try:
                expnum += list(np.random.choice(arr_aux,size=per_nite))
            except:
                logging.warning('Possible low number g-band per nite')
        
        '''as we probably deal with duplicates, fill up to 50 elements
        '''
        expnum = list(set(expnum))
        while len(expnum)<50:
            rdm = np.random.choice(arr['expnum'],size=1)
            if rdm[0] not in expnum:
                expnum += list(rdm)
       
        outnm = '{0}_prebpm_gBAND.csv'.format(label)
        np.savetxt(outnm,np.sort(np.array(expnum)),fmt='%d')
        logging.info('CSV expnums table: {0}'.format(outnm))
        return True

    @classmethod
    def some_stat(cls,df):
        '''Given a DataFrame containig the information from the DB query,
        construct some informative plots
        '''
        if False:
            import datetime
            from matplotlib.dates import MonthLocator,DayLocator,DateFormatter
            xdate = [datetime.datetime.strptime(str(int(date)),'%Y%m%d')
                    for date in np.unique(df['nite'])]
            #define the locators for the plot
            months = MonthLocator()
            days = DayLocator()
            dateFmt = DateFormatter('%b-%d')#b if for Month name
            months2 = MonthLocator()
            days2 = DayLocator()
            dateFmt2 = DateFormatter('%b-%d')
            fig = plt.figure()#figsize=(10,8))
            ax1 = fig.add_subplot(111)
            ndate = np.unique(df['nite'].values)
            N = []
            for nd in ndate:
                if len(df.loc[df['nite']==nd].index):
                    N.append(len(df.loc[df['nite']==nd].index))
                else:
                    N.append(0)
            ax1.plot(xdate,N,'bo-')
            ax1.set_title('20160921t1003, nitely selection of expnum',
                        fontsize=15)
            ax1.set_xlabel('nite')
            ax1.set_ylabel('N')
            ax1.set_ylim([0,6])
            #im1 = ax1.hist(xdate,40,facecolor='navy',
            #            histtype='step',fill=True,linewidth=3,alpha=0.8)
            #format the ticks
            ax1.xaxis.set_major_locator(days)
            ax1.xaxis.set_major_formatter(dateFmt)
            ax1.xaxis.set_minor_locator(days)
            ax1.autoscale_view()
            ax1.grid(True)
            fig.autofmt_xdate()
            ax1.autoscale_view()
            outnm = '20160921t1003_nite.pdf'
            plt.savefig(outnm,dpi=150,facecolor='w',edgecolor='w',
                    orientation='portrait', papertype=None, format='pdf',
                    transparent=False, bbox_inches=None, pad_inches=0.1,
                    frameon=None)
            plt.show()
        
        if False:
            plt.hist(cumd,40,facecolor='darkturquoise',
                    histtype='step',fill=True,linewidth=3,alpha=0.8)
            for p in (25,50,75):
                plt.axvline(np.percentile(cumd,p),
                        lw=1.5,color='r')
            plt.title('20160921t1003, cumulative distance to neighbors',
                    fontsize=15)
            plt.xlabel('cumulative distance deg')
            plt.ylabel('N')
            outnm = '20160921t1003_cumdistance.pdf'
            plt.savefig(outnm,dpi=150,facecolor='w',edgecolor='w',
                    orientation='portrait', papertype=None, format='pdf',
                    transparent=False, bbox_inches=None, pad_inches=0.1,
                    frameon=None)
            plt.show()

        if False:
            plt.hist(neig,40,facecolor='gold',
                    histtype='step',fill=True,linewidth=3,alpha=0.8)
            for p in (25,50,75):
                plt.axvline(np.percentile(neig,p),
                        lw=1.5,color='r')
            plt.title('20160921t1003, distance to nearest neighbor',fontsize=15)
            plt.xlabel('distance deg')
            plt.ylabel('N')
            outnm = '20160921t1003_nearest.pdf'
            plt.savefig(outnm,dpi=150,facecolor='w',edgecolor='w',
                    orientation='portrait', papertype=None, format='pdf',
                    transparent=False, bbox_inches=None, pad_inches=0.1,
                    frameon=None)
            plt.show()

        if False:
            plt.hist(table['skybrightness'],20,facecolor='yellow',
                    histtype='step',fill=True,linewidth=3,alpha=0.8)
            for p in (25,50,75):
                plt.axvline(np.percentile(table['skybrightness'],p),
                        lw=1.5,color='r')
            plt.xlabel('skybrightness')
            plt.ylabel('N')
            plt.title('20160921t1003, skybrightness',fontsize=15)
            outnm = '20160921t1003_skybrightness.pdf'
            plt.savefig(outnm,dpi=150,facecolor='w',edgecolor='w',
                    orientation='portrait', papertype=None, format='pdf',
                    transparent=False, bbox_inches=None, pad_inches=0.1,
                    frameon=None)
            plt.show()
        

if __name__ == '__main__':
    print '...starting selection'
    #----------
    label = 'y4e1'
    niterange = [20160813,20161208]
    #label = 'y4e2'
    #niterange = [20170103,20170218]
    #----------
    gsel_ini = Toolbox.gband_select(niterange)
    gsel = Refine.reduce_sample(gsel_ini,label)
