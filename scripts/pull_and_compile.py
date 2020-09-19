#!/usr/bin/env python

import os
import re
import subprocess

ROOT_PATH = '..'
PATH_TO_POM_FILE = os.path.join( ROOT_PATH, 'pom.xml' )


def run_command( cmd, where ):
	return  subprocess.check_output( cmd, cwd = where, shell = True)


def get_modules():
	modules = []
	regex = (ur"\<module\>(.+)\<\/module\>")
	with open( PATH_TO_POM_FILE, 'r' ) as pom_file:
		matches = re.finditer(regex, pom_file.read(), re.MULTILINE)
		for matchNum, match in enumerate(matches, start=1):
			modules.append( match.group(1) )
	return modules

def check_if_clean( module ):
	print( '\033[1mChecking module %s \033[0m' % module )
	path = os.path.join( ROOT_PATH, module )
	out = run_command( "git status -uno", path )
	
	# Get branch name.
	branch_match = re.search( ur"^On branch (.+)$", out, re.MULTILINE )
	print( 'Current branch: %s' % branch_match.group( 1 ) )
	
	# Check if we are up to date.
	up_to_date = re.search( ur"Your branch is up to date with", out, re.MULTILINE )
	if not up_to_date:
		print( 'Repo not up to date with remote. Aborting. ' )
		return False

	# Check if there are unstaged commits.
	unstaged = re.search( ur"Changes not staged for commit:", out, re.MULTILINE )
	if unstaged:
		print( 'There are unstaged changes. Aborting. ' )
		return False
	
	print( 'All good.' )
	return True

def git_pull( module ):
        print( '\033[1mPulling in  module %s \033[0m' % module )                    
        path = os.path.join( ROOT_PATH, module )                                 
        out = run_command( "git pull", path )  	

def install():
        cmd = "mvn clean install"  	
	subprocess.call( cmd, cwd = ROOT_PATH, shell = True ) 

#-----------------------
# MAIN
#-----------------------

def main():

	modules = get_modules()

	# Check each module.
	print( '\n----------------' )
	print( 'Checking modules' )
	for module in modules:
		if not check_if_clean( module ):
			return 
	
	# Pull each module.
	print( '\n-------------------' )
	print( 'Pulling from remote' )
	for module in modules:
		git_pull( module )	
	print( 'Done.' )
	

	print( '\n----------' )
	print( 'Installing' )
	install()
	print( 'Done.' )

if __name__ == "__main__":
    main()

