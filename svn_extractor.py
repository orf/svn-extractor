#!/bin/python

import requests
import sys
import argparse
import os
import sqlite3

def readsvn(data,urli):
    old_line=""
    file_list=""
    dir_list=""
    user = ""
    if not urli.endswith('/'):
        urli = urli + "/"    
    for a in data.text.splitlines():
        #below functionality will find all usernames from svn entries file
        #if (a == "has-props"):
            #print "UserName found : " + old_line
        if (a == "file"):
            print urli + old_line
            save_url_svn(urli,old_line)
            file_list=file_list + ";" +  old_line
        if (a == "dir"):
            if old_line != "":
                folder_path="output\\" + urli.replace("http://","").replace("/","\\") + "\\" + old_line
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                dir_list = dir_list + ";" + old_line
                print urli + old_line
                d=requests.get(urli+old_line + "/.svn/entries")
                readsvn(d,urli+old_line)
        old_line = a
    return file_list,dir_list,user

def readwc(data,urli):
    folder = "output\\" + urli.replace("http://","").replace("/","\\")
    if not folder.endswith('\\'):
        folder = folder  + "\\"
    with open(folder + "wc.db","wb") as f:
        f.write(data.content)
    conn = sqlite3.connect(folder + "wc.db")
    c = conn.cursor()
    c.execute('select local_relpath, ".svn/pristine/" || substr(checksum,7,2) || "/" || substr(checksum,7) || ".svn-base" as alpha from NODES;')
    list_items = c.fetchall()
    c.execute('select distinct changed_author from nodes;')
    auther_list = c.fetchall()
    c.close()
    for filename,url_path in list_items:
        print urli + filename
        save_url_wc(urli,filename,url_path)
    return 0

def save_url_wc(url,filename,svn_path):
    if filename != "":
        if svn_path is None:
            folder_path="output\\" + url.replace("http://","").replace("/","\\")+ filename.replace("/","\\")
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
	else:
            folder = "output\\" + url.replace("http://","").replace("/","\\") + os.path.dirname(filename).replace("/","\\")
            if not os.path.exists(folder):
                os.makedirs(folder)
	    if not folder.endswith('\\'):
		folder = folder  + "\\"
            r=requests.get(url + svn_path)
            with open(folder+os.path.basename(filename),"wb") as f:
                f.write(r.content)
    return 0

def save_url_svn(url,filename):
    folder="output\\" + url.replace("http://","").replace("/","\\")
    if not folder.endswith('\\'):
        folder = folder  + "\\" 
    r=requests.get(url + "/.svn/text-base/" + filename + ".svn-base")
    with open(folder + filename,"wb") as f:
        f.write(r.content)
    return 0

def main(argv):
    target=''
    desc="""This program is used to extract the hidden SVN files from a webhost considering
either .svn entries file (<1.6)
or wc.db (> 1.7) are available online.
This program actually automates the directory navigation and text extraction process"""
    epilog="""Credit (C) Anant Shrivastava http://anantshri.info
    Greets to Amol Naik, Akash Mahajan, Prasanna K, Lava Kumar for valuable inputs"""
    parser = argparse.ArgumentParser(description=desc,epilog=epilog)
    parser.add_argument("--url",help="Provide URL",dest='target',required=True)
    x=parser.parse_args()
    url=x.target
    print url
    if not url.endswith('/'):
        url = url + "/"
    if url is None:
	exit()
    print "Checking if URL is correct"
    try:
	r=requests.get(url)
    except:
	e = sys.exc_info()[0]
	print "Invalid url specified"
	print e
	exit()
    if r.status_code == 404:
	print "URL returns " + str(r.status_code)
	exit()
    else:
	print "URL is active"
        folder_path="output\\" + url.replace("http://","").replace("/","\\")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
	print "Checking for presence of wc.db"    
	r=requests.get(url + "/.svn/wc.db")
	if r.status_code == 200:
		print "WC.db found"
		readwc(r,url)
		exit()
	print "FAILED"
	print "lets see if we can find .svn/entries"
	r=requests.get(url + "/.svn/entries")
	if r.status_code == 200:
		print "SVN Entries Found"
		data=readsvn(r,url)
		exit();
	print "FAILED"
	print (url + " doesn't contains any SVN repository in it")
	
if __name__ == "__main__":
   main(sys.argv[1:])