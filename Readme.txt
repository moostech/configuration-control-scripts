CONTENTS OF THIS FILE
---------------------
   
 * Introduction
 * Usage
 * Pre-requistes
 * Script Details
 * Script Options
 * Default Global Variables
 * Questions/Comments



INTRODUCTION
------------
This script:
 * Monitors the configuration running in your SDN controller
 * If there are any changes, then the script will ssh to the SDN controller, and copy/paste to configuration to a text file.
 * The script can push the new configuration to a github account.
 * The script can send a notification email if configuration changes.
 


USAGE
-----
CLI argument to run the script is:
 * python configuration_control.py <controller username> <controller password> [options]
 * Or ./configuration_control.py <controller username> <controller password> [options]

To view all the script options, type:
 * python configuration_control.py —-help
 * Or python configuration_control.py -h



PRE-REQUISTES
-------------
  1) Install git on the controller using "sudo apt-get install git" command, before using the script
  2) Create a git repository to store the configuration files using the git clone command. For example:
     “git clone https://github.com/nenni80/configuration-control-scripts.git”
  3) Setup github on your controller
     git config --global user.name "nenni80"
     git config --global user.email mostafa_mans@hotmail.com
  4) Copy the script to the controller. 
  5) Change the script file permission mode to 755, "chmod 755 configuration_control.py"
     Note: if you update controller image, you will need to install github and copy the script again.
  6) Add the script to a cron file, so it can start automatically even if the controller reboots
     edit your crontab by typing "crontab -e and create an entry like this:
     @reboot /home/admin/configuration_control.py admin password123



SCRIPT DETAILS
--------------
 * Monitor the current configuration file using md5sum command. 
 * If configuration files changes, the script ssh to localhost, then the script types "show run" to collect the config
 * The script saves the output of show run in "configuration.txt" file in the github folder
 * If the script is running on standby controller, then the script will exit.
 * The script will parse the controller log file to see who did the last configuration change, and will save the config in userlog.txt file in the github folder
 * If github option is enabled, the script will check the github status, and make sure the local github folder is uptodate, then uploads the file.
 * If send email option is enabled, then the script will send an email



SCRIPT OPTIONS
--------------
 * Mandatory variables: 
      - controller username
      - controller password

 * Optional variables:
      - If GitHub is enabled, then define GITHUBUSER, GITHUBPWD, GITDIR
      - If Email is enabled, then define EMAILTO, EMAILFROM, EMAILPWD
      - Interval: how often to pull the configuration from the controller, default is 1 second
      - LogUser: log who was the last person to login into the controller, and what configuration changes did he make?



DEFAULT GLOBAL VARIABLES
------------------------
 * SERVER = "localhost"               			# Controller IP addresses
 * CONFFILE = "configuration.txt"     			# configuration file to be added to github - to be added to github
 * LOGFILE = "/log/bigswitch/floodlight/floodlight.log" # logfile on the controller
 * USERLOG = "userslog.txt"           			# logfile that contains user - to be added to github



QUESTIONS/COMMENTS
------------------
contact mostafa.mansour@bigswitch.com

