
select att.archive_path, att.reqnum, att.unitname, att.attnum
    from pfw_attempt att, proctag tag
    where tag.tag='Y5A1 PRECAL'
        and tag.pfw_attempt_id=att.id
    order by att.unitname, att.archive_path; > precal_y5a1.tab
