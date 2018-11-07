""" Plot all the ccds from a set of exposures
"""

import os
import glob
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
import gc
import multiprocessing as mp
try:
    from astropy.io import fits
    from astropy.visualization import (ImageNormalize, LogStretch, SqrtStretch, 
                                       HistEqStretch, LinearStretch, 
                                       ZScaleInterval)
except:
    logging.error('Error importing astropy')
try:
    import easyaccess as ea
except:
    logging.error('Error importing easyaccess')
# setup logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
)

def dbquery(toquery, dbsection='desoper',
            help_txt=False):
    '''the personal setup file .desservices.ini must be pointed by desfile
    DB section by default will be desoper
    '''
    connect = ea.connect(dbsection)
    cursor = connect.cursor()
    outtab = connect.query_to_pandas(toquery)
    # Transform column names to lower case
    outtab.columns = map(str.lower, outtab.columns)
    # Remove duplicates
    outtab.reset_index(drop=True, inplace=True)
    return outtab

def get_immask(explist, filetype='red_immask'):
    """ To get the paths for all of the exposures in the input list
    """
    q = "select im.expnum, im.ccdnum, fai.path, im.filename"
    q += " from file_archive_info fai, image im"
    q += " where im.filename=fai.filename"
    q += " and im.filetype='{0}'".format(filetype)
    q += " and im.expnum in ({0})".format(','.join(map(str, explist)))
    q += " order by im.ccdnum"
    df = dbquery(q)
    return df

def plot_all(df, ext=1, root_path='/archive_data/desarchive'):
    """ Plot all the 60 CCDs
    """
    # Construct the path
    aux = []
    for idx, row in df.iterrows():
        aux.append( os.path.join(root_path, row['path'], row['filename']) )
    df['aux'] = aux
    # Go expnum by expnum
    for expnum in df['expnum'].unique():
        gc.collect()
        outnm = '{0}_evalFP.pdf'.format(expnum)
        #
        df_e = df.loc[df['expnum'] == expnum].copy()
        df_e.reset_index(drop=True, inplace=True)
        # Plot
        fig, ax = plt.subplots(4, 16, figsize=(12, 6.5), sharex=True, 
                               sharey=True)
        for idx, axis in enumerate(ax.flatten()):
            if (idx < len(df_e.index)):
                print(idx)
                row = df_e.iloc[idx]
                # Read fits
                with fits.open(row['aux']) as hdu:
                    m = hdu[ext].data
                    h = hdu[ext].header
                # Create a scale for the CCD
                n1 = ImageNormalize(m, interval=ZScaleInterval(),
                                    stretch=LinearStretch())
                axis.imshow(m, norm=n1, origin='lower', cmap='gray_r')
                axis.text(0.5, 0.1, 'c{0:02}'.format(h['CCDNUM']),
                          color='white', 
                          fontweight='bold',
                          transform=axis.transAxes)
                # Remove axis labels
                axis.axes.get_xaxis().set_visible(False)
                axis.axes.get_yaxis().set_visible(False)
            else:
                # To remove the frame
                axis.axis('off')
        # Spacing
        plt.subplots_adjust(left=0.01, bottom=0.01, right=0.99, top=0.96,
                            hspace=0, wspace=0) 
        plt.suptitle('expnum:{0}'.format(expnum), color='dodgerblue')
        if True:
            plt.savefig(outnm, format='pdf', dpi=300)
        else:
            plt.show()
        logging.info('Saved: {0}'.format(outnm))
    return True

def plot_all_parallel(df, ext=1, ccd=None, 
                      root_path='/archive_data/desarchive'):
    """ Plot all CCDs or single CCD, in parallel
    """
    # Construct the path
    aux = []
    for idx, row in df.iterrows():
        aux.append( os.path.join(root_path, row['path'], row['filename']) )
    df['aux'] = aux
    # Go expnum by expnum, to fill a list to be used for plotting
    arg_mp = []
    for expnum in df['expnum'].unique():
        df_e = df.loc[df['expnum'] == expnum].copy()
        df_e.reset_index(drop=True, inplace=True)
        arg_mp.append([ccd, ext, expnum, df_e])  
    # Call the multiprocessing
    poolx = mp.Pool(processes=mp.cpu_count())
    if (ccd is None):
        res = poolx.map_async(fp_parallel, arg_mp)
        # We force wait to end the function: if get() is not used, it will not
        # wait for the processes to end
        res.wait()
        res.get()
    else:
        res = poolx.map_async(ccd_parallel, arg_mp)
        res.wait()
        res.get()
    poolx.close()
    return True

def ccd_parallel(list_arg):
    ccd, ext, expnum, df_e = list_arg
    # Reduce to the target CCD
    df_e = df_e.loc[df_e['ccdnum'] == ccd]
    df_e.reset_index(drop=True, inplace=True)
    #
    outnm = '{0}_evalCCD.pdf'.format(expnum)
    # Plot
    gc.collect()
    fig, ax = plt.subplots(1, figsize=(2, 4.4))
    # Read fits
    with fits.open(df_e['aux'].values[0]) as hdu:
        m = hdu[ext].data
        h = hdu[ext].header
    # Create a scale for the CCD
    n1 = ImageNormalize(m, interval=ZScaleInterval(),
                        stretch=LinearStretch())
    ax.imshow(m, norm=n1, origin='lower', cmap='gray_r')
    ax.text(0.5, 0.1, 'c{0:02}'.format(h['CCDNUM']),
            color='white', 
            fontweight='bold',
            transform=ax.transAxes)
    # Remove axis labels
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    # Spacing
    plt.subplots_adjust(left=0.01, bottom=0.01, right=0.99, top=0.96,
                        hspace=0, wspace=0) 
    plt.suptitle('expnum:{0}'.format(expnum), color='dodgerblue')
    if True:
        plt.savefig(outnm, format='pdf', dpi=300)
        gc.collect()
    else:
        plt.show()
    logging.info('Saved: {0}'.format(outnm))
    return True

def fp_parallel(list_arg):
    ccd, ext, expnum, df_e = list_arg
    outnm = '{0}_evalFP.pdf'.format(expnum)
    # Plot
    gc.collect()
    fig, ax = plt.subplots(4, 16, figsize=(12, 6.5), sharex=True, 
                           sharey=True)
    for idx, axis in enumerate(ax.flatten()):
        if (idx < len(df_e.index)):
            row = df_e.iloc[idx]
            # Read fits
            with fits.open(row['aux']) as hdu:
                m = hdu[ext].data
                h = hdu[ext].header
            # Create a scale for the CCD
            n1 = ImageNormalize(m, interval=ZScaleInterval(),
                                stretch=LinearStretch())
            axis.imshow(m, norm=n1, origin='lower', cmap='gray_r')
            axis.text(0.5, 0.1, 'c{0:02}'.format(h['CCDNUM']),
                      color='white', 
                      fontweight='bold',
                      transform=axis.transAxes)
            # Remove axis labels
            axis.axes.get_xaxis().set_visible(False)
            axis.axes.get_yaxis().set_visible(False)
        else:
            # To remove the frame
            axis.axis('off')
    # Spacing
    plt.subplots_adjust(left=0.01, bottom=0.01, right=0.99, top=0.96,
                        hspace=0, wspace=0) 
    plt.suptitle('expnum:{0}'.format(expnum), color='dodgerblue')
    if True:
        plt.savefig(outnm, format='pdf', dpi=300)
        gc.collect()
    else:
        plt.show()
    logging.info('Saved: {0}'.format(outnm))
    return True

if __name__ == '__main__':
    h0 = 'Script to iteratively plot all the available CCDs per exposure'
    arg = argparse.ArgumentParser(description=h0)
    h1 = 'Table, one column, listing the exposures to be plotted'
    arg.add_argument('--explist', help=h1)
    h2 = 'If no one-column exposure table is provided, then a CSV table having'
    h2 += ' \'expnum, ccdnum, path, filename\' fields should be provided'
    arg.add_argument('--tab', help=h2)
    h3 = 'Options to plot whole focal plane or single CCD. Options: fp (for'
    h3 += ' focal plane plot), fpar (for plotting fp in parallel), ccd (for'
    h3 += ' ccd plotting in parallel)'
    arg.add_argument('--op', help=h3, choices=['fp', 'fpar', 'ccd'])
    h4 = 'If ccd was selected to plot, input the ccd number'
    arg.add_argument('--ccd', help=h4, type=int)
    #
    arg = arg.parse_args()
    # Get the table
    if (arg.explist is not None) and (arg.tab is None):
        y = np.loadtxt(arg.explist, dtype=int)
        df_exp = get_immask(y)
        df_exp.to_csv('g_selection.csv', index=False, header=True)
    elif (arg.tab is not None) and (arg.explist is None):
        df_exp = pd.read_csv(arg.tab)
        df_exp.columns = map(str.lower, df_exp.columns)
    # Append .fz to filename
    df_exp['filename'] += '.fz'
    # Plot them 
    if (arg.op == 'fp'):
        plot_all(df_exp)
    elif (arg.op == 'fpar'):
        plot_all_parallel(df_exp)
    elif (arg.op == 'ccd'):
        plot_all_parallel(df_exp, ccd=arg.ccd)
    else:
        logging.info('Default is to plot in parallel')
        plot_all_parallel(df_exp)
