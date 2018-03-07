#! /bin/csh -f 

if ($#argv < 2) then
    echo "$0 [ccd] [dsuf] "
    goto TheEnd
endif

set ccd=`echo $1 $2 | gawk '{printf("%02d",$1);}' `
set dsuf=`echo $1 $2 | gawk '{printf("%s",$2);}' `

set tmp=$$tmp
#set precal_list=Y2E2_precal.list
#set object_list=Y2E2_object.list

#set precal_list=Y3_precal.ugrizVR.list
#set object_list=Y3_object.list 

set precal_list=Y4E1_precal.list
set object_list=Y4E1_object.list 
#set object_list=Y4E1_object.listhack 

set apath=/archive_data/desarchive


if (! -e out_$dsuf) mkdir out_$dsuf
if (! -e log_$dsuf) mkdir log_$dsuf

#echo "# Working on CCD $ccd"
#echo "# Will write output to out_$dsuf and log_$dsuf "

if (-e $tmp.biascor.list) /bin/rm $tmp.biascor.list
if (-e $tmp.flatcor.list) /bin/rm $tmp.flatcor.list

foreach ddir (`gawk '{if(substr($1,1,1)!="#"){printf("%s ",$1);}}' $precal_list ` )

#    echo $ddir
    ls $apath/$ddir/biascor/*_c$ccd'_'*'_biascor.fits' >> $tmp.biascor.list 
    ls $apath/$ddir/norm-dflatcor/*_g_c$ccd'_'*'_norm-dflatcor.fits' >> $tmp.flatcor.list 

end
    
gawk -v ccd=$ccd '{if (substr($1,1,1)!="#"){if($2==ccd){printf("%s/%s/%s",$4,$5,$6);if (NF>6){printf("%s",$7);}printf("\n");}}}' $object_list > $tmp.objects.list 

wc $tmp.biascor.list | gawk '{printf("Identified %d biascor frames\n",$1);}' >& log_$dsuf/log.bpm_$ccd
wc $tmp.flatcor.list | gawk '{printf("Identified %d flatcor frames\n",$1);}' >>& log_$dsuf/log.bpm_$ccd
wc $tmp.objects.list | gawk '{printf("Identified %d object frames\n",$1);}' >>& log_$dsuf/log.bpm_$ccd

echo "# " >>& log_$dsuf/log.bpm_$ccd 
echo "# " >>& log_$dsuf/log.bpm_$ccd 
#echo "Attempting to build BPM for CCD $ccd"

#set badpix_dir=/des001/home/rgruendl/desdm/devel/scratch/kadrlica/bpm/data
#set edir=/home/rgruendl/desdm/devel/imdetrend/trunk/python

set badpix_dir=/home/rgruendl/desdm/devel/despycal/trunk/data
set edir=/home/rgruendl/desdm/devel/despycal/trunk/bin

#$IMDETREND_DIR/python/mkbpm.py --outfile bpm_attempt0_c$ccd.fits \

$edir/mkbpm.py --outfile out_$dsuf/bpm_c$ccd.fits \
    --ccdnum $ccd \
    --biascor $tmp.biascor.list \
    --flatcor $tmp.flatcor.list \
    --images  $tmp.objects.list \
    --badpix  $badpix_dir/bad_pixel_20160506.lst \
    --funkycol $badpix_dir/funky_column.lst -v 3 >>& log_$dsuf/log.bpm_$ccd 

#    --badpix  $badpix_dir/bad_pixels.lst \
#goto TheEnd

TheEnd:

if (-e $tmp.biascor.list) /bin/rm $tmp.biascor.list
if (-e $tmp.flatcor.list) /bin/rm $tmp.flatcor.list
if (-e $tmp.objects.list) /bin/rm $tmp.objects.list

exit 0
