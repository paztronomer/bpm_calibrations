#! /bin/csh -f 

if ($#argv < 2) then
    echo "$0 [ccd] [dsuf] "
    goto TheEnd
endif

set ccd=`echo $1 $2 | gawk '{printf("%02d",$1);}' `
set dsuf=`echo $1 $2 | gawk '{printf("%s",$2);}' `

set tmp=$$tmp

echo "# " >>& log_$dsuf/log.bpm_$ccd 
echo "# " >>& log_$dsuf/log.bpm_$ccd 
#echo "Attempting to build BPM for CCD $ccd"

#set badpix_dir=/des001/home/rgruendl/desdm/devel/scratch/kadrlica/bpm/data
#set edir=/home/rgruendl/desdm/devel/imdetrend/trunk/python

set badpix_dir=/home/rgruendl/desdm/devel/despycal/trunk/data
set edir=/home/rgruendl/desdm/devel/despycal/trunk/bin

#$IMDETREND_DIR/python/mkbpm.py --outfile bpm_attempt0_c$ccd.fits \

@ j=0
while ($j < 62) 
    @ j++
    set ccd=`echo $j | gawk '{printf("%02d",$1);}' `

    $edir/mkbpm.py --outfile null_bpm/null_c$ccd'_r2896p01_bpm.fits' \
        --badpix $badpix_dir/bad_pixel_20160506.lst \
        -v 3 --ccdnum $ccd >& log_$dsuf/log.bpm_$ccd 

#    add_keyword.sa inlist=null_bpm/null_c$ccd'_r2896p01_bpm.fits' keyword=CCDNUM type=i value=$ccd comment=0

end

#    --badpix  $badpix_dir/bad_pixels.lst \

#goto TheEnd

TheEnd:

if (-e $tmp.biascor.list) /bin/rm $tmp.biascor.list
if (-e $tmp.flatcor.list) /bin/rm $tmp.flatcor.list
if (-e $tmp.objects.list) /bin/rm $tmp.objects.list

exit 0
