-- SUPERCAL TAG
-- ============
-- 20160921t1003, reqnum 2877, attnum 5
--Step 1
--create a temporal table to harbor the results
create table SUPERCAL_Y4E2 as 
select unitname, reqnum, attnum
    from pfw_attempt
    where reqnum=2922
    and attnum=1
    and unitname='20170201t0213'
    group by unitname,reqnum;

--to delete a table from the DB
--DROP TABLE <table to be deleted> PURGE

--Step 2
--create the definition for the tag
insert into ops_proctag_def (tag, description) 
    values ('Y4A1_Y4E2_SUPERCAL', 'SUPERCAL run for Year 4, Epoch 2, for the Y4A1 Processing campaign');

--Step 3
--insert the above results in the tag
insert into proctag (tag, created_date, created_by, pfw_attempt_id) 
    select 'Y4A1_Y4E2_SUPERCAL', SYSDATE, 'fpazch', a.id 
    from pfw_attempt a, SUPERCAL_Y4E1 x 
    where a.reqnum=x.reqnum 
    and a.unitname=x.unitname 
    and a.attnum=x.attnum;

