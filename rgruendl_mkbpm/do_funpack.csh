#! /bin/csh -f

@ i=1
while ($i < 62)
    @ i++
    set ccdnum=`echo $i | gawk '{printf("%02d",$1);}' `
    echo "Working on funpacking ccdmum=$ccdnum"
    funpack ./Y3_object/Y3-r2353/g/D00*/p02/red/pixcor/D00*_g_c$ccdnum'_'*.fits.fz
end

