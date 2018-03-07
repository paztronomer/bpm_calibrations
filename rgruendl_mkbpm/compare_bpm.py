#! /usr/bin/env python
"""
Query a series of nights to determine the object frames present in order to assses
their availability for constructing supersky calibrations (i.e. illumination and
fringe corrections).

Syntax:
    find_supersky_inputs.py -v [-s section] -f night1 -l night2

    night1 = first archive night to be probed (current in DTS).
    night2 = last  archive night to be probed (current in DTS).

    Three modes are now possible.
       1) if only -f {date} is specified only that date is used
       2) if -f and -l are specified then all exposures in that date range are considered
       3) if -w is used then search is performed starting with that date and then 
            succesively including dates before and after to reach a minimum number of 
            desired exposures (--nummin) for each calibration (currently the number of 
            u-band flats is not considered).  The -f and -l options can be used to restrict 
            range from growing beyond a certain point.
     
Options:
       -v Verbose.
       -s Section of desdbi file.

"""

#################################################################################
def split_section(section):
#
#   Function to split a section keyword string '[x1:x2,y1:y2]' into its component values.
#
        xy_range=section[1:-1].split(',')
        x_range=xy_range[0].split(':')
        y_range=xy_range[1].split(':')
        section_val={}
        section_val["x1"]=int(x_range[0])
        section_val["x2"]=int(x_range[1])
        section_val["y1"]=int(y_range[0])
        section_val["y2"]=int(y_range[1])
        return section_val

#################################################################################
            

if __name__ == "__main__":

    from  optparse import OptionParser
    import os
#    import coreutils.desdbi
    import re
    import stat
    import time
    import sys
    import datetime
    import fitsio
    import numpy
    
    parser = OptionParser(usage=__doc__)

    parser.add_option("-i", "--iroot", dest="iroot", default=None, help="Root name of first exposure to be compared") 
    parser.add_option("-I", "--Isuffix", dest="Isuffix", default=None, help="Suffix (if any) if first exposure name.") 
    parser.add_option("-j", "--jroot", dest="jroot", default=None, help="Root name of second exposure to be compared") 
    parser.add_option("-J", "--Jsuffix", dest="Jsuffix", default=None, help="Suffix (if any) if second exposure name.") 
    parser.add_option("-o", "--oroot", dest="oroot", default=None, help="Output file root name")
    parser.add_option("-O", "--Osuffix", dest="Osuffix", default=None, help="Suffix (if any) for output exposure name.") 

    parser.add_option("-c", "--ccdlist", dest="ccdlist", default="All", help="List of ccds to operate on (default=All or 1-62)")
    parser.add_option("-t", "--type", dest="type_comp", default="ratio", help="Type of comparison to be made (ratio or diff)") 

    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                         help="Print progress messages to stdout")
    parser.add_option("-s", "--section", dest="section",
                        help='section of .desservices file with connection into', default="db-desoper")

    (opts, args) = parser.parse_args()
    
    if (opts.iroot is None):
        print("Root name for first input (-i) is required")
        print("Aborting!")
        exit(1)
    if (opts.jroot is None):
        print("Root name for second input (-j) is required")
        print("Aborting!")
        exit(1)
#    if (opts.oroot is None):
#        print("Output root name (-o) is required")
#        print("Aborting!")
#        exit(1)

    if (opts.ccdlist == "All"):
        ccd_list=range(1,63)
    else:
        tmp_ccd_list=opts.ccdlist.split(",")
        ccd_list=[]
        for ccd in tmp_ccd_list:
            if (re.search("-",ccd)is None):
                ccd_list.append(int(ccd))
            else:
                ccd_subset=ccd.split("-")
                for ccd2 in range(int(ccd_subset[0]),(int(ccd_subset[1])+1)):
                    ccd_list.append(int(ccd2))
    ccd_list=sorted(list(set(ccd_list)))

#
#   Define a dictionary to translate filter/band to an ordinate 
#
#    band2i={"u":0,"g":1,"r":2,"i":3,"z":4,"Y":5}
#
#   Check for DB services 
#
#    try:
#        desdmfile = os.environ["des_services"]
#    except KeyError:
#        desdmfile = None
#    dbh = coreutils.desdbi.DesDbi(desdmfile,opts.section)
#    cur  = dbh.cursor()
#

#
#   Loop over all CCDs in an exposure operating on each in succession.
#   
    print("# bit   value #found1 #found2  %found1  %found2")
    for ccd in ccd_list:
        print("################## CCD={:02d} #####################".format(ccd))
#
#       Form first input image name and check for its existence (or for a compressed version)
#
        if (opts.Isuffix is None):
            ifname=("%s%02d.fits" % (opts.iroot,ccd))
        else:
            ifname=("%s%02d%s.fits" % (opts.iroot,ccd,opts.Isuffix))
        ifound=True
        if (not(os.path.isfile(ifname))):
            fz_fname=("%s.fz" % (ifname))
            if (not(os.path.isfile(fz_fname))):
                gz_fname=("%s.gz" % (ifname))
                if (not(os.path.isfile(gz_fname))):
                    print ifname," not found (or .fz, .gz variant)  Aborting."
                    ifound=False
                else:
                    ifname=gz_fname
            else:
                ifname=fz_fname
        if (ifound):
            if (ifname[-2:] == "fz"):
                isci_hdu, imsk_hdu, iwgt_hdu = (1,2,3) # for .fz
            else:
                isci_hdu, imsk_hdu, iwgt_hdu = (0,1,2) # for .fits (or .gz)
#
#       Form second input image name and check for its existence (or for a compressed version)
#
        if (opts.Jsuffix is None):
            jfname=("%s%02d.fits" % (opts.jroot,ccd))
        else:
            jfname=("%s%02d%s.fits" % (opts.jroot,ccd,opts.Jsuffix))
        jfound=True
        if (not(os.path.isfile(jfname))):
            fz_fname=("%s.fz" % (jfname))
            if (not(os.path.isfile(fz_fname))):
                gz_fname=("%s.gz" % (jfname))
                if (not(os.path.isfile(gz_fname))):
                    print jfname," not found (or .fz, .gz variant)  Aborting."
                    jfound=False
                else:
                    jfname=gz_fname
            else:
                jfname=fz_fname
        if (jfound):
            if (jfname[-2:] == "fz"):
                jsci_hdu, jmsk_hdu, jwgt_hdu = (1,2,3) # for .fz
            else:
                jsci_hdu, jmsk_hdu, jwgt_hdu = (0,1,2) # for .fits (or .gz)
#
#       Form output image name
#
#        if (opts.Osuffix is None):
#            out_fname=("%s_%02d.fits" % (opts.oroot,ccd))
#        else:
#            out_fname=("%s_%02d.%s.fits" % (opts.oroot,ccd,opts.Osuffix))

        if (opts.verbose): 
            if (ifound): 
                print "Found: ",ifname
            else:
                print "Missing: ",ifname
            if (jfound):
                print "Found: ",jfname
            else:
                print "Missing: ",jfname
#
#       Read images
#
        if ((ifound)and(jfound)):
            ifits = fitsio.FITS(ifname,'r') # Change to 'rw' if you want
            ih = ifits[isci_hdu].read_header()
            iSCI=ifits[isci_hdu].read()

            jfits = fitsio.FITS(jfname,'r') # Change to 'rw' if you want
            jh = jfits[jsci_hdu].read_header()
            jSCI=jfits[jsci_hdu].read()
#
#           Check that sizes match.
#
            if (not((iSCI.shape[0]==jSCI.shape[0])and(iSCI.shape[1]==jSCI.shape[1]))):
                print "WARNING: Different shape for images ",ifname," and ",jfname
                print "         shape(s) :",iSCI.shape," vs. ",jSCI.shape
                print "Aborting!"
                exit(1)
            else:
#
#               Perform comparison
#
                npix=iSCI.shape[0]*iSCI.shape[1]
                if (opts.type_comp == "bitwise"):
                    bval=0
                    wsm = numpy.where( iSCI > 0)
                    num_ibit=npix-len(wsm[0])
                    wsm = numpy.where( jSCI > 0)
                    num_jbit=npix-len(wsm[0])
                    print(" Good {:7d} {:7d} {:7d} {:8.3f} {:8.3f} {:7d}".format(bval,num_ibit,num_jbit,(100.*num_ibit/npix),(100.*num_jbit/npix),(num_ibit-num_jbit)))
                    for bit in range(0,15):
                        bval=numpy.uint16(2**bit)
                        ibit=numpy.bitwise_and(iSCI,bval)
                        jbit=numpy.bitwise_and(jSCI,bval)
                        wsm = numpy.where( ibit > 0)
                        num_ibit=len(wsm[0])
                        wsm = numpy.where( jbit > 0)
                        num_jbit=len(wsm[0])
                        print("   {:2d} {:7d} {:7d} {:7d} {:8.3f} {:8.3f} {:7d}".format(bit,bval,num_ibit,num_jbit,(100.*num_ibit/npix),(100.*num_jbit/npix),(num_ibit-num_jbit)))
                elif (opts.type_comp == "ratio"):
                    result_img=iSCI/jSCI
                elif (opts.type_comp == "diff"):
                    result_img=iSCI-jSCI
                else:
                    print "Unknown/unsupported comparison type: ",opts.type_comp
                    print "Aborting"
                    exit(1)
#
#                Write results
#

#                ofits = fitsio.FITS(out_fname,'rw',clobber=True)
#                ofits.write(result_img,header=ih)
#                ofits.close()
    
                ifits.close()
                jfits.close()

    exit(0)


