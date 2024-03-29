#!/usr/bin/env python

import os
import re
import subprocess
import datetime
import sys
import glob
import shutil

ROOT_PATH = '..'
PATH_TO_POM_FILE = os.path.join( ROOT_PATH, 'pom.xml' )


def run_command( cmd, where ):
	print( 'Running %s on %s' % ( cmd, where ) )
	try:
		return subprocess.check_output( cmd, cwd = where, shell = True)
	except subprocess.CalledProcessError as e:
		print( 'Could not run %s on %s' % ( cmd, where ) )

def get_modules():
	modules = []
	regex = (u"\<module\>(.+)\<\/module\>")
	with open( PATH_TO_POM_FILE, 'r' ) as pom_file:
		matches = re.finditer(regex, pom_file.read(), re.MULTILINE)
		for matchNum, match in enumerate(matches, start=1):
			modules.append( match.group(1) )
	return modules

def get_module_version( module ):
	"""Reads the module version in the pom by looking at the dependencies
	section."""
	module_name = module[3:] # skip the ../
	regex = ( u"\<" + module_name + "\.version\>(.+)\</" + module_name + "\.version\>")
	with open( PATH_TO_POM_FILE, 'r' ) as pom_file:
		matches = re.finditer(regex, pom_file.read(), re.MULTILINE)
		for matchNum, match in enumerate(matches, start=1):
			return match.group(1)
	return ""

def check_if_clean( module, skip_up_to_date = False ):
	print( 'Checking module %s ' % module )
	path = os.path.join( ROOT_PATH, module )
	out = run_command( "git status -uno", path ).decode('ISO-8859-1')

	# Get branch name.
	branch_match = re.search( u"^On branch (.+)$", out, re.MULTILINE )
	if branch_match is not None:
		print( 'Current branch: %s' % branch_match.group( 1 ) )
		# Check if we are up to date.
		up_to_date = re.search( u"Your branch is up to date with", out, re.MULTILINE )
	else:
		tag_match = re.search( u"^HEAD detached at (.+)$", out, re.MULTILINE )
		print( 'Current tag: %s' % tag_match.group( 1 ) )
		# Check if we are up to date.
		up_to_date = re.search( u"nothing to commit", out, re.MULTILINE )

	if not skip_up_to_date and not up_to_date:
		print( 'Repo not up to date with remote. Aborting. ' )
		return False
	# Check if there are unstaged commits.
	unstaged = re.search( u"Changes not staged for commit:", out, re.MULTILINE )
	if unstaged:
		print( 'There are unstaged changes. Aborting. ' )
		return False

	print( 'All good.' )
	return True

def git_pull( module ):
	print( 'Pulling in  module %s' % module )
	path = os.path.join( ROOT_PATH, module )
	out = run_command( "git pull", path )

def git_checkout_master( module ):
	path = os.path.join( ROOT_PATH, module )
	out = run_command( "git checkout master", path )

def git_checkout_version( module, version ):
	path = os.path.join( ROOT_PATH, module )
	# Now checkout the desired version.
	module_name = module[3:] # skip the ../
	print( 'Checkout version %s of module %s' % ( version, module_name ) )
	out = run_command( "git -c advice.detachedHead=false checkout %s-%s" % ( module_name, version ), path )

def get_branch_name( module ):
	path = os.path.join( ROOT_PATH, module )
	out = run_command( "git status -uno", path ).decode('ISO-8859-1')
	branch_match = re.search( u"^On branch (.+)$", out, re.MULTILINE )
	if branch_match is not None:
		return branch_match.group( 1 )
	else:
		tag_match = re.search( u"^HEAD detached at (.+)$", out, re.MULTILINE )
		return tag_match.group( 1 )

def install( default_location = True ):
	if not default_location:
		branch_name = get_branch_name( '../mastodon' )
		t = datetime.date.today()
		if branch_name.lower().startswith( 'mastodon' ):
			target_dir = './%s-%s-all' % ( branch_name, t )
		else:
			target_dir = './Mastodon-%s-%s-all' % ( branch_name, t )
		if not os.path.exists( target_dir ):
			os.mkdir( target_dir )
		print( 'Installing to %s' % target_dir )
		cmd = "mvn clean install -Dscijava.app.directory=%s" % os.path.abspath( target_dir )
	else:
		print( 'Installing to default SciJava location' )
		cmd = "mvn clean install"
	subprocess.call( cmd, cwd = ROOT_PATH, shell = True )

	if not default_location:
		subcopy_mastodon_jar( target_dir )

def subcopy_mastodon_jar( target_dir ):
	# Make a separate copy of just the mastodon jar if we have to.
	copy_dir = target_dir[0:-4]
	if not os.path.exists( copy_dir ):
		os.mkdir( copy_dir )

	for file in glob.glob( './' + target_dir + '/jars/mastodon-*.jar' ):
		print( 'Copying %s to %s ' % ( file, copy_dir ) )
		shutil.copy( file, copy_dir )

#-----------------------
# MAIN
#-----------------------

def main():

	modules = get_modules()

	# Read the desired version.
	print( '\n----------------' )
	print( 'Version specified for modules:' )
	for module in modules:
		version = get_module_version( module )
		print( ' %30s -> %s' % ( module, version ) )

	# Check each module.
	print( '\n----------------' )
	print( 'Checking modules' )
	for module in modules:
		if not check_if_clean( module, module == '../mastodon-app' ):
			return

	# Pull each module.
	print( '\n-------------------' )
	print( 'Pulling from remote' )
	for module in modules:
		git_pull( module )
		version = get_module_version( module )
		git_checkout_version( module, version )
	print( 'Done.' )

	print( '\n----------' )
	print( 'Installing' )
	install( True )
	print( 'Done.' )

	# Go back to master.
	print( '\n----------' )
	print( 'Switch back to master branches' )
	for module in modules:
		git_checkout_master( module )
	print( 'Done.')


if __name__ == "__main__":
	main()
