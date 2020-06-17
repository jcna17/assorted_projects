# -*- coding: utf-8 -*-
"""
Created on Mon May  4 20:41:06 2020

@author: jakec
"""
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime, timedelta
from pushbullet import Pushbullet
import time


def open_webpage(page_num="page=1"):
    #read the first page of the mountain project buy/sell/trade forum into a BeautifulSoup object
    url = r"https://www.mountainproject.com/forum/103989416/for-sale-for-free-want-to-buy?"+page_num
    page = requests.get(url)
    soup = BeautifulSoup(page.content, features="lxml")
    return soup

def get_data(soup, targets):
    #pulls out each table row (each post is its own row in a table)
    table_rows = soup.find_all("tr")
    #drops posts that are tagged with WTB
    table_rows = [row for row in table_rows if "wtb" not in str(row).lower()]
    #creates lists to be populated with table row data
    titles = [] 
    links = [] 
    target_rows = []
    #extracts only table entries that have a title containing one or more target words
    for row in table_rows:
        for target in targets:
            if target in str(row):
                #extracts the contents of the rows that contain keywords
                if row not in target_rows:
                    target_rows.append(row)
                #extracts title from row and drops html formatting
                #append non-duplicate titles to the titles list
                title = str(row.find("strong")).replace("<strong>", "").replace("</strong>","").lower()
                if title not in titles:
                    titles.append(title)    
                #extracts links from row and drops html formatting
                link = str(row.find("a")["href"])
                #append non-duplicate links to the links list
                if link not in links:
                    links.append(link)
    
    last_activity = []
    num_replies = []
    for row in target_rows:
        #append amount of time since the last activity to list last_activity
        last_activity.append(re.findall(".* ago", str(row))[0].strip())
        num_replies.append(re.findall(" {10,}[0-9]{1,3}", str(row))[0].strip())
    
    #extract the time of the last activity as a timedelta object and append to time_deltas
    time_deltas = []
    for row in last_activity:
        if row.split(" ")[1] == "mins" or row.split(" ")[1] == "min":
            time_deltas.append(timedelta(minutes = int(row.split(" ")[0])))
        elif row.split(" ")[1] == "hours" or row.split(" ")[1] == "hour":
            time_deltas.append(timedelta(hours = int(row.split(" ")[0])))
        elif row.split(" ")[0] == "moments":
            time_deltas.append(timedelta(minutes=0))
        else:
            time_deltas.append(timedelta(days = int(row.split(" ")[0])))
    #compute time of last update by subtracting each time delta from the current time
    time_last_updated = [datetime.now() - time_delta for time_delta in time_deltas]
    return (titles, links, last_activity, time_last_updated, num_replies)


def send_to_phone():
    #function paramaters
    soup = open_webpage("page=1") #opens given page number of forum; must be in form "page=n"
    targets = ["fs", "cams", "c4", "totem", "master", "friend", "dragon", "patagonia"] #keywords in titles of posts 
    #get data for DataFrame
    titles, links, last_activity, time_last_updated, num_replies = get_data(soup, targets)
    
    #adds variables listed in columns to pandas DataFrame
    posts = pd.DataFrame(list(zip(
                         titles, links, last_activity, time_last_updated, num_replies)), 
                         columns = ["titles", "links", "last_activity", "time_last_updated", "num_replies"]
                         ).sort_values(by="time_last_updated", ascending=False)
    #creates notification column
    posts["notification"] = False   
    
    #DataFrame containing all posts of interest from all the times the program has run
    masterlist = pd.read_csv("posts_masterlist.csv")
    #add all posts in posts to masterlist
    masterlist = masterlist.append(posts, sort=False).reindex(posts.columns, axis=1)
    
    #drop the posts that are already in masterlist
    masterlist = masterlist.drop_duplicates("links", keep="first")
    #change indices to unique numbers
    masterlist.index = range(masterlist.shape[0])
    
    #authorize for the pushbullet API
    pb = Pushbullet() #insert your api key here
    for index, row in masterlist.iterrows():
        #if notification has not yet been sent send notification for post
        #also mark each post for which the notification has been sent as sent
        if row.notification != True:
            masterlist.loc[index, "notification"] = True
            push = pb.push_link(row.titles, row.links)
    
    #update the masterlist csv file
    masterlist.to_csv("posts_masterlist.csv")
    
#run the program every frequency minutes duration times    
def repeat(duration, frequency):
    for i in range(duration):
        send_to_phone()
        time.sleep(frequency * 60)
        

        
        
  
    





        
    








