--Step by Step: to create the PRECAL TAG to be used for BPM creation

-- PRECAL TAG
-- ==========

--create the definition for the tag
insert into ops_proctag_def (tag, description) 
    values ('Y4A1_Y4E2_PRECAL', 'PRECAL (nightly) runs for Year 4, Epoch 2, for the Y4A1 Processing campaign');

--insert the above results in the tag
insert into proctag (tag, created_date,created_by,pfw_attempt_id) 
    select 'Y4A1_Y4E2_PRECAL', SYSDATE, 'fpazch', pfw.id 
    from pfw_attempt pfw 
    where pfw.reqnum=2923;

exit
