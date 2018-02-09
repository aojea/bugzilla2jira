from __future__ import print_function
import sys
import argparse
import ConfigParser
import time
import bugzilla
from jira import JIRA

# Bugzilla data and JIRA fields
# In Bugzilla   In JIRA
# -----------   -------
# Product       Project
# Bug           Issue
# ID            Bugzilla ID
# Summary       Summary
# Description   Description
# Priority/Severity Priority
# Status        Status

# To be able to sync both tools we use the fields
# see_also in Bugzilla to add the link to the JIRA issue
# and the customFieldId=16700 in JIRA to add a link with the Bugzilla #

status_mapping = {
    'NEW' : 'Open',
    'CONFIRMED' : 'Open',
    'IN_PROGRESS' : 'In_progress',
    'RESOLVED' : 'Closed'
}

def sync_bug_status(jira, issue, bz_status, jira_status):
    # TODO support syncing status
    # To be able to graph the issues trend we support only Open and Resolved 
    transitions = jira.transitions(issue)
    for t in transitions:
        print("id: %s name: %s" % (t['id'], t['name']))
    # jira.transition_issue(issue, transitionId=131)

def main(arguments):
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file', required=True)
    parser.add_argument('-w', '--write-jira', action='store_true')
    args = parser.parse_args(arguments)

    settings = ConfigParser.ConfigParser()
    settings.read(args.config_file)
    
    # Connect to Bugzilla 
    bz_url = settings.get('bugzilla', 'url')
    bz_user = settings.get('bugzilla', 'user')
    bz_pass = settings.get('bugzilla', 'pass')
    bz_product = settings.get('bugzilla', 'product')

    bzURL = 'https://%s:%s@%s' % (bz_user, bz_pass, bz_url)
    bzapi = bugzilla.Bugzilla(url=bzURL,
                              user=bz_user,
                              password=bz_pass,
                              sslverify=False,
                              use_creds=False)

    # Connect to JIRA
    jira_url = settings.get('jira', 'url')
    jira_user = settings.get('jira', 'user')
    jira_pass = settings.get('jira', 'pass')
    jira_product = settings.get('jira', 'product')
    jira_project = settings.get('jira', 'project')

    jac = JIRA(server=jira_url,
               basic_auth=(jira_user, jira_pass))

    # Obtain Bugzilla bugs
    query = bzapi.build_query(product=bz_product)

    t1 = time.time()
    bugs = bzapi.query(query)
    t2 = time.time()
    print("Found %d bugs in BugZilla with our query" % len(bugs))
    print("Quicker query processing time: %s" % (t2 - t1))

    # Sync Bugzilla 2 Jira
    cnt_update = 0
    cnt_new = 0
    for bzbug in bugs:
        if bzbug.see_also:
            # Check if the bug exists in Jira and sync status
            for url in bzbug.see_also:
                if jira_url in url:
                    issue = jac.issue(url.rsplit('/',1)[-1])
                    # Sync status
                    if not args.write_jira:
                        print("Sync status Bug id=%s summary=%s status=%s jira_status=%s"
                              % (bzbug.id, bzbug.summary, status_mapping[bzbug.status], issue.fields.status))
                    elif status_mapping[bzbug.status] != issue.fields.status:
                        sync_bug_status(jac, issue, bzbug.status, issue.fields.status)
                        cnt_update += 1
                    else:
                        print("ISSUES ARE SYNCED")
                    break
        else:
            # Create Bugzilla bug in JIRA
            bzbug_url = 'https://%s/show_bug.cgi?id=%i' % (bz_url, bzbug.id)
            if args.write_jira:
                new_issue = jac.create_issue(project=jira_project,
                                              summary=bzbug.summary,
                                              labels=[jira_product, "bugzilla"],
                                              customfield_16700=bzbug_url,
                                              issuetype={'name': 'Bug'})
                issue_url = 'https://%s/browse/%s' % (jira_url, new_issue.key)
                # add the JIRA link to the see_also field
                update = bzapi.build_update(see_also_add=[issue_url])
                bzapi.update_bugs([bzbug.id], update)
                if status_mapping[bzbug.status] != new_issue.fields.status:
                    sync_bug_status(jac, new_issue, bzbug.status, new_issue.fields.status)
            else:
                print("Create new Bug id=%s summary=%s status=%s"
                      % (bzbug.id, bzbug.summary, bzbug.status))                
            cnt_new += 1
    if args.write_jira:
        print("%i bugs will be created in JIRA" % cnt_new)
        print("%i bugs will be synced between JIRA and Bugzilla" % cnt_update)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
