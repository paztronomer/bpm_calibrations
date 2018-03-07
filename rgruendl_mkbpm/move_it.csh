#! /bin/csh -f 

if ($#argv < 4) then
    echo "$0 {idir} {odir} {opref} {osuff} {do_cp}"
    echo " "
    echo "    Assumes input filename look like {idir}/bpm_c{ccdnum}.fits "
    echo "           output filename look like {odir}/{opref}_c{ccdnum}_{osuff}.fits "
    echo " "
    echo "    The value for {do_cp} must be yes in order for the script to actually perform the copy"
    echo " "
    goto TheEnd
endif

set idir=$1
set odir=$2
set opref=$3
set osuff=$4

if ($#argv>4) then
    set tmp_docp=$5
else
    set tmp_docp="no"
endif


@ j=0
while ($j<62)
    @ j++

    set fname=`echo $idir $j | gawk '{printf("%s/bpm_c%02d.fits",$1,$2);}' `
    set gname=`echo $odir $opref $j  $osuff | gawk '{printf("%s/%s_c%02d_%s.fits",$1,$2,$3,$4);}' `

    if (-e $fname ) then
        if ($tmp_docp == "yes") then
            cp $fname $gname 
            echo -n "Copying: "
        endif
        echo $fname $gname
    endif

end

TheEnd:

exit 0
