# calibration
Auxiliary scripts for DES BPM generation

## Instructions to create BPM

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
```
or
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
```
or
```sql
select {...}; > y5a1_precal.tab
```
