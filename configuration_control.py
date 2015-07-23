#!/usr/bin/python
#
#
# USAGE: 
#     python configuration_control.py
#     CLI argument to run the script is:
#        - python configuration_control.py <controller username> <controller password> [options]
#        - Or ./configuration_control.py <controller username> <controller password> [options]
#
#     To view all the script options, type:
#        - python configuration_control.py --help
#        - Or python configuration_control.py -h
#
#
# SCRIPT OPTIONS:
#     Mandatory variables: 
#        - controller username
#        - controller password
#
#     Optional variables:
#        - If GitHub is enabled, then define GITHUBUSER, GITHUBPWD, GITDIR
#        - If Email is enabled, then define EMAILTO, EMAILFROM, EMAILPWD
#        - Interval: how often to pull the configuration from the controller, default is 1 second
#        - LogUser: log who was the last person to login into the controller, and what configuration changes did he make?
#
#
# PRE-REQUISTES:
#     1) install git on the controller using "sudo apt-get install git" command
#     2) create a git repository to store the configuration files using the git clone command
#        "git clone https://github.com/nenni80/configuration-control-scripts.git"
#     3) setup github on your controller
#        git config --global user.name "nenni80"
#        git config --global user.email mostafa_mans@hotmail.com
#     4) copy the script to the controller. 
#     5) Change the script file permission mode to 755, "chmod 755 configuration_control.py"
#     Note: if you update controller image, you would need to install github and copy the script again.
#     5) add the script to a cron file, so it can start automatically even if the controller reboots
#        edit your crontab by typing "crontab -e and create an entry like this:
#        @reboot /home/admin/configuration_control.py
#        
#
# Script Summary:
#     This script:
#     1) Monitors the configuration running in your SDN controller
#     2) If there are any changes, then the script will ssh to the SDN controller, 
#        and copy/paste to configuration to a text file.
#        - The script can push the new configuration to a github account.
#        - The script can send a notification email if configuration changes.
#
#
# Script Details - Milestones for incremental development:
#        - Monitor the current configuration file using md5sum command. 
#        - If configuration files changes, the script ssh to localhost, then the script types "show run" to collect the config
#        - The script saves the output of show run in "configuration.txt" file in the github folder
#        - If the script is running on standby controller, then the script will exit.
#        - The script will parse the controller log file to see who did the last configuration change, and will save the config in userlog.txt file in the github folder
#        - If github option is enabled, the script will check the github status, and make sure the local github folder is uptodate, then uploads the file.
#        - If send email option is enabled, then the script will send an email
#
#################################################################################

import pexpect             # python implementation of Expect
import time                # library needed for wait/sleep time functions
import os                  # provides functions for interacting with the operating system
import argparse            # add options to the cli argument
import smtplib             # library needed for sending emails
import subprocess          # provides shell commands functions
import sys                 # use sys exit function


# Define Global Variables
SERVER = "localhost"               # Controller IP addresses
CONFFILE = "configuration.txt"     # configuration file to be added to github - to be added to github
LOGFILE = "/log/bigswitch/floodlight/floodlight.log" # logfile on the controller
USERLOG = "userslog.txt"           #logfile that contains user - to be added to github


### This function ssh to the controller and returns the running configuration
def ssh_to_server_and_copy_config(cntlusername,cntlpassword,SERVER):
    child = pexpect.spawn ('ssh -o "UserKnownHostsFile /dev/null" -o "StrictHostKeyChecking no" %s@%s' % (cntlusername, SERVER))
    # Check to see if the controller is active or standby
    opt = child.expect (['Password:', 'SLAVE'])
    if opt == 0:
         child.sendline (cntlpassword)
         child.expect ('>')
         child.sendline ('show run')
         child.expect ('>')
         SHOW_RUN = child.before
         child.sendline ('exit')
         print "SUCCESSFUL: Pull configuration file from the controller"
         return SHOW_RUN
    elif opt == 1:
        print "FAILURE: SLAVE controller. Abort the script"
        return False



### This function check that the github folder is up to date before adding new files to it
def check_github_status(GITDIR,GITWORKTREE,GITHUBUSER,GITHUBPWD):
    # some git commands need to be executed from the git folder.
    # get current directory
    currentdir = os.getcwd();
    # change the directory to go to github directory, push command doesnt work unless you inside github dir
    os.chdir(r'%s' % (GITWORKTREE))
    output = pexpect.run ('git pull')
    if "Already up-to-date" in output:
         #go back to script directory
         os.chdir(r'%s' % (currentdir))
         return "INFORMATION: GitHub pull is already up-to-date"
    else:
         pexpect.run ('git add .')
         pexpect.run ('git commit -m "adding new configuration file"')
         child = pexpect.spawn ('git push origin master')
         output = child.expect (['Username:', pexpect.EOF, 'Traceback'])
         if output == 0:
             child.sendline (GITHUBUSER)
             child.expect ('Password:')
             child.sendline (GITHUBPWD)
             child.expect ([pexpect.EOF, 'Authentication failed'])
             if "fatal" in child.before:
                 os.chdir(r'%s' % (currentdir))
                 return "ERROR: GitHub authentication failed. Please check username and password"
         elif output != 0:
             #print child.before
             os.chdir(r'%s' % (currentdir))
             return "FAILED: was not able to upload new configuration file to github"


### This function uploads the confgiruation file to the github
def github_upload(GITDIR,GITWORKTREE,GITHUBUSER,GITHUBPWD):
    # some git commands need to be executed from the git folder.
    # get current directory
    currentdir = os.getcwd();
    # change the directory to go to github directory, push command doesnt work unless you inside github dir    
    # git --git-dir=configuration-control-scripts/.git --work-tree=configuration-control-scripts push origin master
    os.chdir(r'%s' % (GITWORKTREE))
    output = pexpect.run ('git status')
    if "modified" in output or "Your branch is ahead" in output:
         print "INFORMATION: GitHub status is not uptodate. Push operation will start"
    pexpect.run ('git add .')
    pexpect.run ('git commit -m "adding new configuration file"')
    child = pexpect.spawn ('git push origin master');
    output = child.expect (['Username:', pexpect.EOF, 'Traceback'])
    if output == 0:
         child.sendline (GITHUBUSER)
         child.expect ('Password:')
         child.sendline (GITHUBPWD)
         child.expect ([pexpect.EOF, 'Authentication failed'])
         if "fatal" in child.before:
             os.chdir(r'%s' % (currentdir))
             return "ERROR: GitHub authentication failed. Please check username and password"
    elif output != 0:
         #print child.before
         os.chdir(r'%s' % (currentdir))
         return "FAILED: GitHub push failed, new configuration file was not uploaded"

    #go back to script directory
    os.chdir(r'%s' % (currentdir))
    return "SUCCESSFUL: Push updated configuration file to GitHub"


### This function sends an email 
def send_email(from_addr,to_addr,password):
    subj = "****** Updated Big Tap Configuration ALERT ******"
    message_text = "Hello\n****** A new configuration file has been uploaded to github ******\n\nBye\n"
    msg = "From: %s\nTo: %s\nSubject: %s\n\n%s" % ( from_addr, to_addr, subj, message_text )
    username = from_addr
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username,password)
    server.sendmail(from_addr, to_addr, msg)
    server.quit()
    return "SUCCESSFUL: Notification email sent successfully"


# call the audit file, to see who did the change
def auditfile():
     # search for the last entry in the log file that had an operation change (create, delet, modify)
     cmd = "cat " + LOGFILE + " | grep Session | grep Operation" + " >myuserlog.txt"
     tmp = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
     # sleep for 5 seconds to make sure the log entry is created.
     time.sleep (5)
     output2 = open('myuserlog.txt', 'r')
     line = output2.readlines()
     #print line
     output2_lastline = line[-1]
     #print "\n\n*********last line is: " + output2_lastline

     #find the session id for the last entry 
     lastsessionid_output = (output2_lastline.split("Session@"))[1].split(" User")[0]

     #find the user name for the last entry
     userid = (output2_lastline.split("User="))[1].split(" Operation")[0]
     print "INFORMATION: Last configuration change was done by user: " + userid
     output = "Last configuration change was done by user: " + userid + "\n"

     #find the date for the last entry
     date_tmp = output2_lastline.split(' ')
     date = "%s %s %s" % (date_tmp[0], date_tmp[1], date_tmp[2])
     output = (output + "Date is: " + date + "\n")

     ## search for all operations (create, delete, modify) within last session ID in the log file
     #cmd = "cat myuserlog.txt | grep " + lastsessionid_output + " | grep Operation" + " >mylog2.txt"
     #tmp = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
     #time.sleep (5)
     #output3 = open('mylog2.txt', 'r')
     ##print username, login date, operation performed, operation detail
     #for line in output3:
     #    date_tmp = line.split(' ')
     #    date = "%s %s %s" % (date_tmp[0], date_tmp[1], date_tmp[2])
     #    #operation_status = (line.split("Operation="))[1].split(" Result")[0]
     #    #operation_result = (line.split("Result="))[1].split(" Details")[0]
     #    operation_details = (line.split("Details="))[1].split("\n")[0]
     #    output = (output + "Date is: " + date + "\n"
     #                  "Configuration details: " + operation_details + "\n")
     ##print output
     return output


### start main function
def main():

    # add cli options (email, github, interval) 
    parser = argparse.ArgumentParser()
    parser.add_argument("username", default="myuser", type=str,
                        help="Enter username for the controller")
    parser.add_argument("password", default="mypassword", type=str,
                        help="Enter password for the controller")

    parser.add_argument("-i", "--interval", default=1, type=int,
                        help="how often to pull the configuration from the controller, default is 1 second")
    parser.add_argument("-l", "--loguser", default=1, type=int,
                        help="log who was the last person to login into the controller, and what configuration changes did he make?")

    parser.add_argument("-g", "--github", default=0, type=int,
                        help="If the option is set to 1, then the script will update the github with the configuration file")
    parser.add_argument("-gu", "--githubuser", default="", type=str,
                        help="Enter github username to access the github account")
    parser.add_argument("-gp", "--githubpassword", default="", type=str,
                        help="Enter github password to access the github account")
    parser.add_argument("-gd", "--githubdirectory", default="configuration-control-scripts", type=str,
                        help="Enter the path for the .git directory")

    parser.add_argument("-e", "--email", default=0, type=int,
                        help="If the option is set to 1, then the script will send an email when it detects a configuration change")
    parser.add_argument("-ef", "--emailfrom", default="bigtapdemo1@gmail.com", type=str,
                        help="Enter email from")
    parser.add_argument("-et", "--emailto", default="mostafa.mansour@bigswitch.com", type=str,
                        help="Enter email to")
    parser.add_argument("-ep", "--emailpassword", default="", type=str,
                        help="Enter email password")

    args = parser.parse_args()
    #If you want your option to be set to 1 even if no --option is specified, then include default=1. 

    #print(args)
    #save cli variables
    cliUser = args.username                   
    cliPassword = args.password
    cliInterval = args.interval
    cliLog = args.loguser
    cliGithub = args.github
    cliGITHUBUSER = args.githubuser             
    cliGITHUBPWD = args.githubpassword             
    cliGITDIR = args.githubdirectory + '/.git'         
    cliGITWORKTREE = args.githubdirectory         
    cliEmail = args.email
    cliEmailFrom = args.emailfrom
    cliEmailTo = args.emailto
    cliEmailPWD = args.emailpassword

    if cliGithub == 1:
        if len(cliGITHUBUSER) <=1 or len(cliGITHUBPWD) <= 1:
            print "ERROR: Please enter Github Username and password"
            sys.exit(1)

    if cliEmail == 1:
        if len(cliEmailFrom) <=1 or len(cliEmailTo) <= 1 or len(cliEmailPWD) <= 1:
            print "ERROR: Please enter Email To, FROM, Password"
            sys.exit(1)

    print ("*********************************************************************\n"
           "****              Config Monitor Script has started              ****\n"
           "*********************************************************************")

    #monitor_file change using md5sum command for bigtap
    OLD_HASH = pexpect.run('md5sum /opt/bigswitch/bigdb/db/config-bigtap.json')
    #monitor_file change using md5sum command for bcf
    #OLD_HASH = pexpect.run('md5sum /var/lib/floodlight/db/global-config/root/current.root')

    while True:
        time.sleep(cliInterval)
        NEW_HASH = pexpect.run('md5sum /opt/bigswitch/bigdb/db/config-bigtap.json')
        # if md5 hash values are not matching then ssh to the contrller and get config
        if NEW_HASH != OLD_HASH:
            print "INFORMATION: New configuration has been detected"
            #set the old hash value to be equal to the new hash value
            OLD_HASH = NEW_HASH
            #ssh to the contrller and get config
            SHOW_RUN = ssh_to_server_and_copy_config(cliUser,cliPassword,SERVER)
            if SHOW_RUN == "False":
                print ("*********************************************************************\n")
                #exit()
            else:
                #check that github is up to date
                if cliGithub == 1:
                     print check_github_status(cliGITDIR,cliGITWORKTREE,cliGITHUBUSER,cliGITHUBPWD)
                #open file and write the config in it
                f = open( './%s/%s' % (cliGITWORKTREE, CONFFILE), 'w' ) 
                f.write( SHOW_RUN + '\n' )
                f.close()
                # call the audit file, to see who did the change
                if cliLog == 1:
                     output = auditfile()
                     #check if userlog file exist in the github folder
                     check_if_file_exists = os.path.isfile('./%s/%s' % (cliGITWORKTREE, USERLOG))
                     if (not check_if_file_exists):
                         f = open( './%s/%s' % (cliGITWORKTREE, USERLOG), 'w' )
                     #check file size, then append if file is less than 1,000,000
                     filesize = os.path.getsize('./%s/%s' % (cliGITWORKTREE, USERLOG))
                     if filesize > 1000000:
                         f = open( './%s/%s' % (cliGITWORKTREE, USERLOG), 'w' )
                     else:
                         f = open( './%s/%s' % (cliGITWORKTREE, USERLOG), 'a' )
                     f.write( output + '\n' )
                     f.close()
                #uploads the confgiruation file to the github
                if cliGithub == 1:
                     print github_upload(cliGITDIR,cliGITWORKTREE,cliGITHUBUSER,cliGITHUBPWD)
                if cliEmail == 1:
                     print send_email(cliEmailFrom,cliEmailTo,cliEmailPWD)
                print ("*********************************************************************\n")

    #sys.exit(1)


if __name__ == "__main__":
   main()
