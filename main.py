#!/usr/bin/env python
# encoding: utf-8
"""
main.py

Created by Martin Hammerschmied on 2012-09-09.
Copyright (c) 2012. All rights reserved.
"""
from AdStore import *
from AdAssessor import *
from WillhabenObserver import *
from Logger import *
from Config import *
from threading import Thread
import md5
import sys
import os

if __name__ == "__main__":
	
	# Create the 'files/' directory if it doesn't exist yet
	if not os.path.exists("./files/"): os.mkdir("files")
	
	# Load configuration
	if len(sys.argv) > 1:
		config_path = sys.argv[1]
	else:
		config_path = "./files/willhaben.cfg"
	config = Config(config_path)
	
	# Initialize logging
	logger = Logger(path = "files/observer.log")
	logger.append("Setting up observer")
	
	# ----------------------------------------------
	# Set up of the platform independent components
	# ----------------------------------------------
	
	# Ads that have already been processed are registered in this file
	if config.ads_store:
		save_file = "files/" + md5.new(config.url).hexdigest() + ".save"
	else: 
		save_file = None	
	store = AdStore(path = save_file)
	
	# Search criteria setup
	assessor = AdAssessor()
	if len(config.title_keywords_all) > 0:
		assessor.add_criterion(AdCriterionTitleKeywordsAll(config.title_keywords_all))
	if len(config.title_keywords_any) > 0:
		assessor.add_criterion(AdCriterionTitleKeywordsAny(config.title_keywords_any))
	if len(config.title_keywords_not) > 0:
		assessor.add_criterion(AdCriterionTitleKeywordsNot(config.title_keywords_not))
	if config.price_limit > 0:
		assessor.add_criterion(AdCriterionPriceLimit(config.price_limit))

	# The observer is the core of the system
	observer = WillhabenObserver(url = config.url, 
								 store = store, 
								 assessor = assessor, 
								 logger = logger, 
								 update_interval = config.update_interval)
	
	# ---------------------------------------------------------------
	# Set up of the platform dependent components and run event loop
	# ---------------------------------------------------------------
	
	if config.runmode == "auto":
		if sys.platform == "linux2":
			runmode = "gtk"
		elif sys.platform == "darwin":
			runmode = "osx"
		else:
			runmode = "server"
	else:
		runmode = config.runmode

	if runmode == "gtk":
		from platform_dependant.Linux import GTKNotification
		import gtk, gobject
		GTKNotify = GTKNotification(icon = "./logo.png")
		observer.notification = GTKNotify
		print "Starting observer thread now"
		observer.start()
		gobject.threads_init()
		gtk.main()

	elif runmode == "osx":
		import Foundation, objc, AppKit
		from PyObjCTools import AppHelper
		from platform_dependant.MacOS import MountainLionNotification
		MLNotify = MountainLionNotification.alloc().init()
		observer.notification = MLNotify
		observer.start()
		app = AppKit.NSApplication.sharedApplication()
		AppHelper.runEventLoop()
	
	elif runmode == "server":
		from platform_dependant.Server import EmailNotification
		emailNotify = EmailNotification(config.smtp_host,
										config.smtp_port,
										config.smtp_user,
										config.smtp_pass,
										config.email_from,
										config.email_to,
										config.email_subject,
										config.email_body)
		observer.notification = emailNotify
		observer.run()