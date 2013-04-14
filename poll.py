#Poll
#Based on printer polling script from Shubhro Saha
import datetime
import urllib, datetime, time
from bs4 import BeautifulSoup

import pymongo
from pymongo import MongoClient

#Establish database connection
connection = MongoClient()
courseDB = connection.courses
courses = courseDB.fall13

#Columns ordered as:
#class number #; DEP ###; title; distribution; Section; Days; Time;
#                   Location; Enrollment; Max enrollment; Status; Books; Eval

def addClass(datetime,line):
    if (len(line) != 13): return
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
    courseDB.insert(entry)
    return

#Note changed enrollment numbers or add new classes.  Assume only enrollment
# changes
def updateClass(datetime,line):
    if (len(line) != 13): return
    entry = courseDB.find_one({'number' : line[0]})
    if (entry == None):
        addClass(datetime, line)
    else:
        if (entry["enrollment"][-1][1] != line[8]):
            entry["enrollment"].append((datetime,line[8]))
        if (entry["max"][-1][1] != line[9]):
            entry["max"].append((datetime,line[9]))
        if (entry["Status"][-1][1] != line[10]):
            entry["Status"].append((datetime,line[10]))
        courses.save(entry)
    return

#Fall 2013 url
CourseUrl = "http://registrar.princeton.edu/course-offerings/search_results.xml?submit=Search&term=1142"

while True:
    now = datetime.datetime.now()
    #f = urllib.urlopen(CourseUrl)
    f = open("reg.html")
    html = f.read()

    soup = BeautifulSoup(html)

    #Go over every table row
    tr_list = soup.find_all('tr')
    for tr in tr_list[]:
        columns = tr.find_all('td')
        #Construct list of columns for this row
        colText = [entry.get_text(" ",strip=True).replace("\n","") for entry in columns]
        updateClass(now, colText)

    print("Pausing for 10 minutes")
    time.sleep(60)
