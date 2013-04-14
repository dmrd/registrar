#Poll the registrar website
#Based on printer polling script from Shubhro Saha
import sys
import datetime
import urllib, datetime, time
from bs4 import BeautifulSoup

import pymongo
from pymongo import MongoClient

#Pause times in changes
minPause = 10
maxPause = 900
timeMultiplier = 2


print("Connecting to database...")
#Establish database connection
connection = MongoClient()
courseDB = connection.courses
print("Connection successful")

#Fall 2013 url
if (sys.argv[1] == "fall"):
    CourseUrl = "http://registrar.princeton.edu/course-offerings/search_results.xml?submit=Search&term=1142"
    courses = courseDB.fall13
    print("Polling fall 2013 courses...")
elif (sys.argv[1] == "spring"):
    CourseUrl = "http://registrar.princeton.edu/course-offerings/search_results.xml?submit=Search&term=1134"
    courses = courseDB.spring13
    print("Polling spring 2013 courses...")
else:
    print("Invalid semester")
    exit()


#Columns ordered as:
#class number #; DEP ###; title; distribution; Section; Days; Time;
#                   Location; Enrollment; Max enrollment; Status; Books; Eval

def addClass(datetime,line):
    if (len(line) != 13): return False
    print("-Entering class {0} into database".format(line[0]))
    entry = {
            'number' : line[0],
            'course' : line[1],
            'title' : line[2],
            'dist' : line[3],
            'section' : line[4],
            'days' : line[5],
            'time' : line[6],
            'loc' : line[7],
            'enrollment' : [(datetime,line[8])], #List of enrollment numbers
            'max' : [(datetime,line[9])],  #Does max enrollment change over time?
            'Status' : [(datetime,line[10])]  #Does max enrollment change over time?
            }
    courses.insert(entry)
    return True

#Note changed enrollment numbers or add new classes.  Assume only enrollment
# changes
def updateClass(datetime,line):
    if (len(line) != 13): return False
    updateFlag = False
    entry = courses.find_one({'number' : line[0]})
    if (entry == None):
        updateFlag = addClass(datetime, line)
    else:
        if (entry["enrollment"][-1][1] != line[8]):
            entry["enrollment"].append((datetime,line[8]))
            updateFlag = True
        if (entry["max"][-1][1] != line[9]):
            entry["max"].append((datetime,line[9]))
            updateFlag = True
        if (entry["Status"][-1][1] != line[10]):
            entry["Status"].append((datetime,line[10]))
            updateFlag = True
        courses.save(entry)
    return updateFlag


print("Entering polling loop...")
pauseTime = minPause
while True:
    sys.stdout.flush()
    updateFlag = False
    changes = 0
    now = datetime.datetime.now()
    print(now)
    f = urllib.urlopen(CourseUrl)
    #f = open("reg.html")
    html = f.read()

    soup = BeautifulSoup(html)

    #Go over every table row
    tr_list = soup.find_all('tr')
    for tr in tr_list:
        columns = tr.find_all('td')
        #Construct list of columns for this row
        colText = [entry.get_text(" ",strip=True).replace("\n","") for entry in columns]
	change  = updateClass(now,colText)
	if (change): #Count changes
            changes += 1
        updateFlag |= change #Has there been any change at all this loop?
    if (updateFlag): #Reset update period 
        pauseTime = minPause
    else: #No changes.  Pause for longer time (or max time, whichever is smaller)
        pauseTime = min(maxPause, pauseTime * timeMultiplier)
    print("Pausing for {0} seconds after {1} changes".format(pauseTime, changes))
    time.sleep(pauseTime)
