import os
import sys
import time
import logging
import pickle
import datetime
import numpy as np
import pandas as pd
import scipy.spatial.distance as distance
#setup for display visualization
import matplotlib
#matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator, DayLocator, DateFormatter
#
try:
    import despydb.desdbi as desdbi
    dbaccess = 'despydb'
except:
    import easyaccess as ea
    dbaccess = 'easyaccess'
finally:
    pass
# setup logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

class Toolbox():
    @classmethod
    def dbquery(cls, toquery, outdtype=None, dbsection='desoper',
                help_txt=False):
        '''the personal setup file .desservices.ini must be pointed by desfile
        DB section by default will be desoper
        '''
        if (dbaccess == 'despydb'):
            desfile = os.path.join(os.getenv('HOME'), '.desservices.ini')
            section = 'db-' + dbsection
            dbi = desdbi.DesDbi(desfile, section)
            if help_txt: help(dbi)
            cursor = dbi.cursor()
            cursor.execute(toquery)
            cols = [line[0].lower() for line in cursor.description]
            rows = cursor.fetchall()
            outtab = np.rec.array(rows, dtype=zip(cols, outdtype))
            logging.warning('Avoiding period of time around light bulb, Y5')
            outtab = outtab[np.where(np.logical_or(outtab['nite'] < 20171109,
                            outtab['nite'] > 20171125))]
        elif (dbaccess == 'easyaccess'):
            connect = ea.connect(dbsection)
            cursor = connect.cursor()
            outtab = connect.query_to_pandas(toquery)
            # Transform column names to lower case
            outtab.columns = map(str.lower, outtab.columns)
            logging.warning('Avoiding period of time around light bulb, Y5')
            outtab = outtab.loc[(outtab['nite'] < 20171109) |
                                (outtab['nite'] > 20171125)]
            # Remove duplicates
            outtab.drop_duplicates(['expnum'], inplace=True)
            outtab.reset_index(drop=True, inplace=True)
        return outtab

    @classmethod
    def gband_select(cls, niterange):
        q = "with y as ("
        q += "    select fcut.expnum, max(fcut.lastchanged_time) as evaltime"
        q += "    from firstcut_eval fcut"
        q += "    where fcut.analyst!='SNQUALITY'"
        q += "    group by fcut.expnum )"
        q += " select e.nite, e.expnum, e.exptime, fcut.skybrightness,"
        q += "    fcut.accepted, e.band, att.reqnum, fcut.t_eff,"
        q += "    fcut.fwhm_asec, val.key, att.id, att.task_id,"
        q += "    e.radeg, e.decdeg"
        q += " from y, exposure e, pfw_attempt_val val, firstcut_eval fcut, "
        q += "    pfw_attempt att "
        q += " where e.nite between {0} and {1}".format(*niterange)
        q += "    and e.band='g'"
        q += "    and val.key='expnum'"
        q += "    and fcut.expnum=e.expnum"
        q += "    and fcut.expnum=y.expnum"
        q += "    and fcut.lastchanged_time=y.evaltime"
        q += "    and to_number(val.val, '999999')=e.expnum"
        q += "    and val.pfw_attempt_id=att.id"
        q += "    and val.pfw_attempt_id=fcut.pfw_attempt_id"
        q += "    and fcut.program='survey'"
        q += "    and fcut.accepted = 'True'"
        q += "    and fcut.t_eff > 0.3"
        q += " order by e.nite"
        datatype = ['i4', 'i4', 'f4', 'f4', 'a10', 'a5', 'i4', 'f4',
                    'f4', 'a50', 'i4', 'i4', 'f4', 'f4']
        tab = Toolbox.dbquery(q, datatype)
        return tab


class Refine():
    @classmethod
    def reduce_sample(cls, data, label):
        '''Low skybrightness, separation of at least 30 arcsec (0.0083 deg)
        Inputs:
        - arr: structured array coming from DB query
        '''
        if isinstance(data, np.ndarray):
            logging.info('Reducing sample. Record array')
            arr = np.copy(data)
            #first selection: skybrightness below median of distribution
            arr = arr[arr['skybrightness'] <= np.median(arr['skybrightness'])]
            #second selection: by its distance
            #select with distance higher than 30 arcsec
            cumd = []
            neig = []
            idx = []
            # NxN loop
            logging.info('NxN distances {0}'.format(arr.shape[0]**2))
            c = 0L
            for i in range(arr.shape[0]):
                d = []
                for m in range(arr.shape[0]):
                    dist = np.linalg.norm(
                        np.array((arr['radeg'][i], arr['decdeg'][i])) -
                        np.array((arr['radeg'][m], arr['decdeg'][m]))
                        )
                    d.append(dist)
                    c += 1
                    if (c % 1E5 == 0):
                        logging.info('Calculation {0} of {1}'.format(
                            c, arr.shape[0]**2)
                            )
                cumd.append(np.sum(d))
                # Avoid appending the zero-distance
                neig.append(sorted(d)[1])
                if sorted(d)[1] > 0.00833:
                    idx.append(i)
            cumd = np.array(cumd)
            neig = np.array(neig)
            #the above selection don't filter, maybe because of the observig
            #criteria in DES. All obey the condition
            #
            # Save files in case of crash
            pickle.dump(cumd, open('rm_cumd.pickle', 'w+'))
            pickle.dump(neig, open('rm_neig.pickle', 'w+'))
            logging.info('Cutting down to 50 g-band exposures')
            #third selection: select 50 entries from a random sample, flat prob.
            per_nite = np.ceil(50 / np.unique(arr['nite']).shape[0]).astype(int)
            np.random.seed(seed=0)
            expnum = []
            for n in np.unique(arr['nite'][:]):
                arr_aux = arr[arr['nite'] == n]['expnum']
                try:
                    expnum += list(np.random.choice(arr_aux, size=per_nite))
                except:
                    logging.warning('Possible low number g-band per nite')
            # As we probably deal with duplicates because did not drop them
            # in the recarray, fill up to 50 elements
            expnum = list(set(expnum))
            pickle.dump(expnum, open('rm_expnum.pickle', 'w+'))
            while (len(expnum) < 50):
                rdm = np.random.choice(arr['expnum'], size=1)
                if rdm[0] not in expnum:
                    expnum += list(rdm)
            #
            logging.info('Saving table')
            outnm = '{0}_prebpm_gBAND.csv'.format(label)
            np.savetxt(outnm, np.sort(np.array(expnum)), fmt='%d')
            logging.info('CSV expnums table: {0}'.format(outnm))
        elif isinstance(data, pd.DataFrame):
            logging.info('Reducing sample. Data Frame')
            df = data.copy(deep=True)
            #first selection: skybrightness below median of distribution
            df = df.loc[df['skybrightness'] <= np.median(df['skybrightness'])]
            #second selection: by its distance
            #select with distance higher than 30 arcsec
            cumd = []
            neig = []
            idx = []
            # NxN loop
            c = 0L
            logging.info('NxN distances {0}'.format(len(df.index)**2))
            for i in range(len(df.index)):
                d = []
                for m in range(len(df.index)):
                    # With indices following the sequence, the below
                    # expressions are equivalent:
                    # - df.iloc[i]['radeg']
                    # - df['radeg'].values[i]
                    dist = np.linalg.norm(
                        df.iloc[i][['radeg', 'decdeg']].values -
                        df.iloc[m][['radeg', 'decdeg']].values
                        )
                    d.append(dist)
                    c += 1
                    if (c % 1E5 == 0):
                        logging.info('Calculation {0} of {1}'.format(
                            c, len(df.index)**2)
                            )
                cumd.append(np.sum(d))
                # Avoid appending the zero-distance
                neig.append(sorted(d)[1])
                if sorted(d)[1] > 0.00833:
                    idx.append(i)
            cumd = np.array(cumd)
            neig = np.array(neig)
            # Save files in case of crash
            pickle.dump(cumd, open('rm_cumd.pickle', 'w+'))
            pickle.dump(neig, open('rm_neig.pickle', 'w+'))
            #the above selection don't filter, maybe because of the observig
            #criteria in DES. All obey the condition
            #
            logging.info('Cutting down to 50 g-band exposures')
            #third selection: select 50 entries from a random sample, flat prob.
            per_nite = np.ceil(50 / df['nite'].unique().size).astype(int)
            np.random.seed(seed=0)
            expnum = []
            for n in df['nite'].unique():
                df_aux = df.loc[df['nite'] == n, 'expnum']
                try:
                    expnum += list(np.random.choice(df_aux, size=per_nite))
                except:
                    logging.warning('Possible low number g-band per nite')
            # Double safety
            expnum = list(set(expnum))
            pickle.dump(expnum, open('rm_expnum.pickle', 'w+'))
            if (len(expnum) < 50):
                logging.warning('Less than 50 selected exposures. Adding more')
            while (len(expnum) < 50):
                rdm = np.random.choice(df['expnum'].values, size=1)
                if rdm[0] not in expnum:
                    expnum += list(rdm)
            #
            logging.info('Saving table')
            outnm = '{0}_prebpm_gBAND.csv'.format(label)
            pd.DataFrame({'expnum': expnum}).to_csv(
                outnm, index=False, header=False
                )
            logging.info('CSV expnums table: {0}'.format(outnm))
        return expnum, cumd, neig

    @classmethod
    def some_stat(cls, df, nrange_str, sel_expnum, cumdist, neighbor):
        '''Given a DataFrame containig the information from the DB query,
        construct some informative plots
        '''
        if True:
            xdate = [datetime.datetime.strptime(str(int(date)), '%Y%m%d')
                    for date in np.unique(df['nite'])]
            #define the locators for the plot
            months = MonthLocator()
            days = DayLocator()
            dateFmt = DateFormatter('%b-%d')#b if for Month name
            months2 = MonthLocator()
            days2 = DayLocator()
            dateFmt2 = DateFormatter('%b-%d')
            fig = plt.figure()#figsize=(10, 8))
            ax1 = fig.add_subplot(111)
            ndate = np.unique(df['nite'].values)
            N = []
            for nd in ndate:
                if len(df.loc[df['nite']==nd].index):
                    N.append(len(df.loc[df['nite']==nd].index))
                else:
                    N.append(0)
            ax1.plot(xdate, N, 'bo-')
            ax1.set_title('{0}'.format(nrange_str),
                          fontsize=15)
            ax1.set_xlabel('nite')
            ax1.set_ylabel('N')
            ax1.set_ylim([0, 6])
            #im1 = ax1.hist(xdate, 40, facecolor='navy',
            #            histtype='step', fill=True, linewidth=3, alpha=0.8)
            #format the ticks
            ax1.xaxis.set_major_locator(days)
            ax1.xaxis.set_major_formatter(dateFmt)
            ax1.xaxis.set_minor_locator(days)
            ax1.autoscale_view()
            ax1.grid(True)
            fig.autofmt_xdate()
            ax1.autoscale_view()
            outnm = '{0}_nite.pdf'.format(nrange_str)
            plt.savefig(outnm, dpi=150, facecolor='w', edgecolor='w',
                        orientation='portrait', papertype=None, format='pdf',
                        transparent=False, bbox_inches=None, pad_inches=0.1,
                        frameon=None)
            # plt.show()
        #
        if True:
            plt.hist(cumd, 40, facecolor='darkturquoise',
                     histtype='step', fill=True, linewidth=3, alpha=0.8)
            for p in (25, 50, 75):
                plt.axvline(np.percentile(cumd, p),
                            lw=1.5, color='r')
            plt.title('{0}, cumulative dist to neighbors'.format(nrange_str),
                      fontsize=15)
            plt.xlabel('cumulative distance deg')
            plt.ylabel('N')
            outnm = '{0}_cumdistance.pdf'.format(nrange_str)
            plt.savefig(outnm, dpi=150, facecolor='w', edgecolor='w',
                        orientation='portrait', papertype=None, format='pdf',
                        transparent=False, bbox_inches=None, pad_inches=0.1,
                        frameon=None)
            # plt.show()
        #
        if True:
            plt.hist(neig, 40, facecolor='gold',
                     histtype='step', fill=True, linewidth=3, alpha=0.8)
            for p in (25, 50, 75):
                plt.axvline(np.percentile(neig, p),
                            lw=1.5, color='r')
            plt.title('{0}, dist to nearest neighbor'.format(nrange_str),
                      fontsize=15)
            plt.xlabel('distance deg')
            plt.ylabel('N')
            outnm = '{0}_nearest.pdf'.format(nrange_str)
            plt.savefig(outnm, dpi=150, facecolor='w', edgecolor='w',
                        orientation='portrait', papertype=None, format='pdf',
                        transparent=False, bbox_inches=None, pad_inches=0.1,
                        frameon=None)
            #plt.show()
        #
        if True:
            plt.hist(table['skybrightness'], 20, facecolor='yellow',
                    histtype='step', fill=True, linewidth=3, alpha=0.8)
            for p in (25, 50, 75):
                plt.axvline(np.percentile(table['skybrightness'], p),
                        lw=1.5, color='r')
            plt.xlabel('skybrightness')
            plt.ylabel('N')
            plt.title('{0}, skybrightness'.format(nrange_str),
                      fontsize=15)
            outnm = '{0}_skybrightness.pdf'.format(nrange_str)
            plt.savefig(outnm, dpi=150, facecolor='w', edgecolor='w',
                        orientation='portrait', papertype=None, format='pdf',
                        transparent=False, bbox_inches=None, pad_inches=0.1,
                        frameon=None)
            #plt.show()


if __name__ == '__main__':
    print '...starting selection'
    #----------
    label = 'y5'
    niterange = [20170815, 20180222]
    #label = 'y4e2'
    #niterange = [20170103, 20170218]
    #----------
    if not False:
        gsel_ini = Toolbox.gband_select(niterange)
        pickle.dump(gsel_ini, open('rm.pickle', 'w+'))
    else:
        pname = 'rm.pickle'
        logging.info('Loading pickled: {0}'.format(pname))
        gsel_ini = pickle.load(open(pname, 'r+'))
    #
    expnum, cumdist, neig = Refine.reduce_sample(gsel_ini, label)
    #
    logging.warning('Plottong methods NEED to be fixed')
    Refine.some_stat(gsel_ini, '20170815t0222', expnum, cumdist, neig)
