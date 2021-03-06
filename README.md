# DES Bad Pixel Masks
Auxiliary scripts for DES BPM generation, as part of the yearly calibrations

## Instructions to create BPM
1. Run the selection of 50 g-band pre BPM by running a call similar to this
`python preBPM_select.py --lab y6 --nites 20180912 20181106 --flag1 --exclude y6_exclude_expnum.csv`

1. Visually inspect the selected exposures
If the table of paths needs to be generated, use:
`python plot_exposures_preBPM.py --explist y6_prebpm_gBAND.csv ...`
If not, then use:
`python plot_exposures_preBPM.py --tab g_selection.csv --op ccd --ccd 41`

1. Tag Supercal, Precal, preBPM

1. Set some environment variables
```bash
set dsuf=Y5A1
set badpix_dir=/work/devel/fpazch/desdmSVN_copy/devel/despycal/trunk/data
set exe_dir=/work/devel/fpazch/desdmSVN_copy/devel/despycal/trunk/bin
```

1. Create a table of *red_pixcor* files, the *object* list
```sql
spool y5a1_object.tab
select im.expnum, im.ccdnum, im.band,
  oa.root, fai.path, im.filename, fai.compression
  from file_archive_info fai, ops_archive oa, image im, proctag tag
  where tag.tag='Y5A1 PREBPM'
    and tag.pfw_attempt_id=im.pfw_attempt_id
    and im.filetype='red_pixcor'
    and im.filename=fai.filename
    and fai.archive_name=oa.name
    order by im.expnum, im.filename;
``` or
```sql
select {...}; > y5a1_object.tab
```
1. Create a table of *precal*
```sql
spool y5a1_precal.tab
select att.archive_path, att.reqnum, att.unitname, att.attnum
  from pfw_attempt att, proctag tag
  where tag.tag='Y5A1 PRECAL'
    and tag.pfw_attempt_id=att.id
    order by att.unitname, att.archive_path;
``` or
```sql
select {...}; > y5a1_precal.tab
```
1. To call the creation of BPMs
```bash
python createBPM.py y5a1_object.tab y5a1_precal.tab --label Y5A1
```
1. After created, rename the BPMs (using a newly created reqnum), and compare against some previous season
```bash
python compare_bpm.py --iroot bpm_a/D_n20170915t0930_c --jroot bpm_b/D_20160101t0115_c --Isuffix _r9999p01_bpm --Jsuffix _r8888p01_bpm  --type bitwise
```
