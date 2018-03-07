'''Script to create BPM based in preBPM and Precal products, using the 
BPM code creation wrote by RGruendl
'''

import os
import sys
import socket
import uuid
import subprocess
import time
import logging
import numpy as np
import shlex
# setup logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                   )


class Listed():
    def __init__(self, 
                 fn_pixcor=None, 
                 fn_precal=None, 
                 ccd=None,
                 badpix=None,
                 bindir=None,
                 band=None,
                 root_dir='/archive_data/desarchive/'):
        '''
        Load the two inputs tables, assuming no compression in the 
        pixcor (fn_pixcor) files. Also define variables for the execution
        of mkbpm
        '''
        # Pending improvemet: accept user-defined dtypes and tables with
        # and use only selected columns
        aux_dt1 = [('expnum', 'i4'),
                   ('ccdnum', 'i4'),
                   ('band', '|S10'),
                   ('root', '|S100'),
                   ('path', '|S100'),
                   ('filename', '|S50'),
                   ('compression', '|S50'),
                  ]
        # if compression:
        #     aux_dt1.append(('compression','|S10'))
        dt1 = np.dtype(aux_dt1)
        dt2 = np.dtype([('archive_path', '|S100'),
                        ('reqnum', 'i4'),
                        ('unitname', 'i4'),
                        ('attnum', 'i4')])
        A = np.loadtxt(fn_pixcor, 
                       dtype=dt1, 
                       comments='#',
                       skiprows=0,
                       usecols=None)
        B = np.loadtxt(fn_precal,
                       dtype=dt2,
                       comments='#',
                       skiprows=0,
                       usecols=None)
        self.obj = A
        self.precal = B
        logging.info('{0} and {1} loaded as recarray'.format(badpix, bindir))
        # For the variables
        self.ccd = ccd
        self.badpix = badpix
        self.bindir = bindir
        self.band = band
        self.root_dir = root_dir
    
    def progress_bar(self, iterator, Nposit, wait_time=0.25):
        '''
        Function receives the actual iterator and the max number of itemss
        then displays a progress bar.
        Idea from: http://stackoverflow.com/questions/3002085/
        python-to-print-out-status-bar-and-percentage
        '''
        sys.stdout.write('\r')
        aux = (iterator * 100 / Nposit) - 1
        sys.stdout.write('|{0:{1}}| {2}%'.format('=' * iterator,
                                                 Nposit, aux))
        sys.stdout.flush()
        time.sleep(wait_time)
        return True

    def feed_list(self):
        '''Create lists to be used as inputs for the BPM creation code
        '''
        aux_m = 'Creating lists of biascor, norm-dflatcor, and pixcor.'
        aux_m += ' Note the first two can be easily achieved with DB queries'
        logging.info(aux_m)
        biascor = []
        flatcor = []
        for n in xrange(self.precal.shape[0]):
            for iter_ccd in self.ccd:
                # Construct biascor list from precal list. One per CCD
                # Here unitname is nite
                reqnum = self.precal['reqnum'][n]
                unitname = self.precal['unitname'][n]
                attnum = self.precal['attnum'][n]
                fn_bias = 'D_n{0}_c{1:02}_r{2}p{3:02}'.format(unitname,
                                                              iter_ccd,
                                                              reqnum,
                                                              attnum)
                fn_bias += '_biascor.fits'
                aux_line = os.path.join(self.root_dir,
                                        self.precal['archive_path'][n],
                                        'biascor',
                                        fn_bias)
                biascor.append((aux_line, iter_ccd))
                # Create list of norm-dflatcor 
                fn_flat = 'D_n{0}_{1}_c{2:02}_r{3}p{4:02}'.format(unitname,
                                                                  self.band,
                                                                  iter_ccd,
                                                                  reqnum,
                                                                  attnum)
                fn_flat += '_norm-dflatcor.fits'
                tmp_line = os.path.join(self.root_dir,
                                        self.precal['archive_path'][n],
                                        'norm-dflatcor',
                                        fn_flat)
                flatcor.append((tmp_line,   iter_ccd))
        # Using the objects list (from preBPM), merge the path and filename.
        # Also save the ccdnum for eachi full path
        f_merge = lambda x, y, z, ccd: (os.path.join(x, y, z), ccd)
        obj = [f_merge(x['root'], x['path'], x['filename'], x['ccdnum']) 
               for x in self.obj]
        dt = np.dtype([('path', '|S200'),
                       ('ccdnum', 'i4')])
        obj = np.array(obj,dtype=dt) 
        biascor = np.array(biascor,dtype=dt)
        flatcor = np.array(flatcor,dtype=dt)
        return biascor, flatcor, obj
    
    def make_bpm(self, clean_tmp=True):
        '''Method to run the code and fill the logs, using the PID as 
        auxiliary for filename/path creation
        '''
        PID = os.getpid()
        bias_aux, flat_aux, obj_aux = self.feed_list()
        # Create output folders
        dir_out = 'out_{0}_pid{1}'.format(label, PID)
        dir_log = 'log_{0}_pid{1}'.format(label, PID)
        #
        if os.path.exists(os.path.dirname(dir_out)):
            aux_m1 = 'Directory {0} exists. Creating new name'.format(dir_out)
            logging.warning(aux_m1)
            dir_out = 'out_{0}_{1}'.format(label, str(uuid.uuid4())) 
            aux_m2 = 'Created: {0}'.format(dir_out)
        else:
            try:
                os.makedirs(os.path.dirname(dir_out))
            except:
                e = sys.exc_info()[0]
                logging.error(e)
                exit(1)
        #
        if os.path.exists(os.path.dirname(dir_log)):
            aux_m1 = 'Directory {0} exists. Creating new name'.format(dir_log)
            logging.warning(aux_m1)
            dir_log = 'out_{0}_{1}'.format(label, str(uuid.uuid4())) 
            aux_m2 = 'Created: {0}'.format(dir_log)
        else:
            try:
                os.makedirs(os.path.dirname(dir_log))
            except:
                e = sys.exc_info()[0]
                logging.error(e)
                exit(1)
        # BPM call, per CCD
        logging.info('Call of BPM creation')
        for m in self.ccd:
            self.progress_bar(m, len(self.ccd), wait_time=0.5)
            # Write out tmp files, using auxiliary arrays created in 
            # feed_list() method
            out_bias = 'pid{0}.biascor.csv'.format(PID)
            np.savetxt(out_bias, 
                       biascor[biascor['ccdnum'] == m]['path'],
                       fmt='%s')
            out_flat = 'pid{0}.flatcor.csv'.format(PID)
            np.savetxt(out_flat,flatcor[flatcor['ccdnum']==m]['path'],fmt='%s')
            out_obj = 'pid{0}.objects.csv'.format(PID)
            np.savetxt(out_obj,obj[obj['ccdnum']==m]['path'],fmt='%s')

            badpix = os.path.join(badpix_dir,'bad_pixel_20160506.lst')
            funky = os.path.join(badpix_dir,'funky_column.lst')
            
            cmds = os.path.join(exe_dir,'mkbpm.py')
            cmds += ' --outfile {0}/bpm_c{1:02}.fits'.format(dir_out,m)
            cmds += ' --ccdnum {0}'.format(m)
            cmds += ' --biascor {0}'.format(out_bias)
            cmds += ' --flatcor {0}'.format(out_flat)
            cmds += ' --images {0}'.format(out_obj)
            cmds += ' --badpix {0}'.format(badpix)
            cmds += ' --funkycol {0}'.format(funky)
            cmds += ' --verbose 3'

            #shlex to more refinated way to take care of tokenization
            cmds = shlex.split(cmds)
            #Notes:
            #i) remember to *maybe* use stdin for communicate different args
            #to mkbpm
            logbpm = open('{0}/log.bpm_c{1:02}'.format(dir_log,m),'w+')
            job = subprocess.Popen(cmds,stdin=None,
                                stdout=logbpm,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True,
                                shell=False,bufsize=-1)
            job.wait()
            logbpm.close()
            
            #erase the tmp files
            if clean_tmp:
                rm_bias = subprocess.check_call(['rm',out_bias]) 
                rm_flat = subprocess.check_call(['rm',out_flat]) 
                rm_obj = subprocess.check_call(['rm',out_obj]) 
        print '\n\tOutput directory: {0}\n\tLOG directory: {1}'.format(dir_out,
                                                                    dir_log)

    @classmethod
    def fill_log(cls):
        pass


if __name__=='__main__':
    logging.info('Running on {0}'.format(socket.gethostname()))
    #
    ccd_list = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,
                21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,
                41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,
                62]
    badpix_dir = '/work/devel/fpazch/desdmSVN_copy/devel/despycal/trunk/data'
    exec_dir='/work/devel/fpazch/desdmSVN_copy/devel/despycal/trunk/bin'
    band = 'g'
    #
    desc = 'Script to collect lists and iteratively call RGruendl \'mkbpm\''
    desc += ' for BPM creation, CCD by CCD. This uses PRECAL and PREBPM'
    desc += ' products as ingredients. Note BPMs are constructed based on'
    desc += ' g-band'
    abc = argparse.ArgumentParser(description=desc)
    #
    t0 = 'Object table harboring \'red_pixcor\' information, from PREBPM.'
    t0 += ' Columns must be (in order): EXPNUM, CCDNUM, BAND, ROOT, PATH'
    t0 += ' FILENAME, COMPRESSION'
    abc.add_argument('objects', help=t0, type=str)
    t1 = 'Precal table harboring PRECAL products information. Columns must'
    t1 += ' be (in order): ARCHIVE_PATH, REQNUM, UNITNAME, ATTNUM'
    abc.add_argument('precal', help=t1, type=str)
    t2 = 'Label to be used for generated BPM'
    abc.add_argument('--label', help=t2, metavar='')
    t3 = 'Space separated list of CCD numbers to be used. Default:'
    t3 += ' {0}'.format(ccd_list)
    abc.add_argument('--ccd', help=t3, nargs=+)
    t4 = 'Directory for badpixel lists definitions. Default: '
    t4 += ' {0}'.format(badpix)
    abc.add_argument('--badpix', help=t4, metavar='', default=badpix_dir)
    t5 = 'Directory for executables. Default: {0}'.format(exec_dir)
    abc.add_argument('--bindir', help=t5, metavar='', default=exec_dir)
    t6 = 'Band. Default: {0}'.format(band)
    abc.add_argument('--band', help=t6, metavar='', default=band)
    # Parse
    abc = abc.parse_args()
    #
    if (abc.label is None):
        label = str(uuid.uuid4())
    else:
        label = abc.label
    if (str.lower(abc.band) != 'b'):
        logging.warning('Band is not g-band')
    #
    L = Listed(
            fn_pixcor=abc.objects,
            fn_precal=abc.precal,
            ccd=abc.ccd,
            badpix=abc.badpix,
            bindir=abc.bindir,
            band=abc.band
        )
    L.make_bpm()
