from platform import *

if system() == "Windows":
	print "You are a Microsoft Device"
if system() == "Darwin":
	print "You are on a Apple/Darwin Device"
if system() == "Linux":
	print "You are on a Linux Device"

