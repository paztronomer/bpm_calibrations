select im.expnum, im.ccdnum, im.band,
        oa.root, fai.path, im.filename, fai.compression
    from file_archive_info fai, ops_archive oa, image im, proctag tag
    where tag.tag='Y5A1 PREBPM'
        and tag.pfw_attempt_id=im.pfw_attempt_id
        and im.filetype='red_pixcor'
        and im.filename=fai.filename
        and fai.archive_name=oa.name
    order by im.expnum, im.filename; > objects_y5a1.tab

