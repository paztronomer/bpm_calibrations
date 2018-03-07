#! /bin/csh -f 

if ($#argv < 3) then
    echo "$0 [ccd] [dsuf] [rsuf] "
    goto TheEnd
endif

set ccd=`echo $1 $2 $3 | gawk '{printf("%02d",$1);}' `
set dsuf=`echo $1 $2 $3 | gawk '{printf("%s",$2);}' `
set rsuf=`echo $1 $2 $3 | gawk '{printf("%s",$3);}' `

set tmp=$$tmp

set ddir=out_$dsuf
set rdir=out_$rsuf

if (! -e $ddir) then
    echo "Missing $ddir "
endif
if (! -e $rdir) then
    echo "Missing $rdir "
endif
if ((! -e $ddir)||(! -e $rdir)) goto TheEnd

foreach ccdnum ( `echo $ccd | '{if ($1 == "all"){i=0;while(i<62){i++;printf(" %02d ",i)}}else{printf("%02d",$1);}}' ` )
    $edir/mkbpm.py --outfile out_$dsuf/bpm_c$ccd.fits \
    --biascor $tmp.biascor.list \
    --flatcor $tmp.flatcor.list \
    --images  $tmp.objects.list \
    --badpix  bad_pixels.lst \
    --funkycol $badpix_dir/funky_column.lst -v 3 >>& log_$dsuf/log.bpm_$ccd 

#goto TheEnd


end
    
TheEnd:

if (-e $tmp.biascor.list) /bin/rm $tmp.biascor.list
if (-e $tmp.flatcor.list) /bin/rm $tmp.flatcor.list
if (-e $tmp.objects.list) /bin/rm $tmp.objects.list

exit 0
