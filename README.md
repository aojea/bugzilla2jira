# bugzilla2jira

Import bugzilla bugs in JIRA

Simply script to read bugs from Bugzilla and create the corresponding issues in
JIRA, so you can have both tools synced.

The tool is customized to our environment where we need to do http basic auth
against the bugzilla API endpoint and we use a label in JIRA to match the
product in Buzilla. 

It uses a config file to specify the following parameters:

* Bugzilla url, user, password and product.

* JIRA url, user, password, project and product. The product is a label in JIRA.

By default the tool don't write the changes in JIRA to avoid mistakes, you have
to use the `-w` switch to do it.

### Example

```
python bz2jira.py -c config

Found 177 bugs in BugZilla with our query
Quicker query processing time: 5.2857439518
Sync status Bug id=1016972 summary=database create failed with time
out status=CONFIRMED jira_status=Open
Create new Bug id=1048211 summary=metric for cpu.user_perc value does
not match vmstat value when vm have cpu load status=CONFIRMED
Create new Bug id=1050983 summary=Nodes rebooted during deployment status=NEW
```
