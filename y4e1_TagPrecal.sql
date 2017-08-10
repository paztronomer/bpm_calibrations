--Step by Step: to create the PRECAL TAG to be used for BPM creation

-- PRECAL TAG
-- ==========


--Step 0
--for the nitelycal between 20160921 and 20161003, jira_parent=2438, I have
--one request number per each nite. Some of the unitnames (nites) has more
--than one attnum. The range of reqnum was pulled from emails or from the 
--created folders in the disk
select unitname,reqnum,max(attnum)
from pfw_attempt
    where reqnum between 2863 and 2875
    group by unitname,reqnum;

--Step 1
--create a temporal table to harbor the results
create table RM1_FPAZCH as 
select unitname,reqnum,max(attnum) as max_reqnum
    from pfw_attempt
    where reqnum between 2863 and 2875
    group by unitname,reqnum;

--to delete a table from the DB
--DROP TABLE <table to be deleted> PURGE

--Step 2
--create the definition for the tag
insert into ops_proctag_def (tag, description) 
    values ('Y4A1_Y4E1_PRECAL', 'PRECAL (nightly) runs for Year 4, Epoch 1, for the Y4A1 Processing campaign');

--Step 3
--insert the above results in the tag
insert into proctag (tag, created_date,created_by,pfw_attempt_id) 
    select 'Y4A1_Y4E1_PRECAL', SYSDATE, 'gruendl', a.id 
    from pfw_attempt a, tmp_my_idlist x 
    where a.reqnum=x.reqnum and 
    a.unitname=x.unitname 
    and a.attnum=x.max_attnum;

