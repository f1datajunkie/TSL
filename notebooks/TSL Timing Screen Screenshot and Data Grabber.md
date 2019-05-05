---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.0'
      jupytext_version: 0.8.6
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

# TSL Timing Screen Screenshot and Data Grabber


This originally started out as a simple script to grab a screenshot of a TSL Timing screen. IT then got a little bit more complicated as I added in a routine that tried to email the screenshot to one or more recipients, and then way more complicated as I started to actually scrape data from the timing screen on the one hand, and ustomate the collection of scrapes, grabbing of screenshots, and mailing of all sorts of things on the other.

The plan now is to turn this into a proper development narrative to try to recreate, in idealised form, how the various puzzle pieces were identified, solved and pieced together...

...as well as tidying up the code, making a simple CLI for it, and packaging it so that it can be easily deployed to collect data whenever, as wheresoever, it's required.

*Note that the original recipe is easily generalised to grab arbitrary webpages.*

```python
%load_ext autoreload
%autoreload 2
```

```python
#Inspired by: https://www.kaggle.com/dierickx3/kaggle-web-scraping-via-headless-firefox-selenium
#from webdriverdownloader import GeckoDriverDownloader
#gdd = GeckoDriverDownloader()
#geckodriver, geckobin = gdd.download_and_install("v0.23.0")

#Alternatively, we can install as part of the container build process
```

```python
%matplotlib inline
```

## Set up a browser instance

We can create a headless browser (one that doesn't need to open in a window that we can see) that we can load pages into and grab screenshots from. As we are running an actual browser, if the web page is being updated via a websocket connection, our remotely launched browser will be being updated with the socket connection data.

So once we launch our browser onto a timing screen, we can just keep referencing the browser to get the latest view of the page...

```python
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

options = Options()
options.headless = True

#If we need to set the path to geck, we can...
#browser = webdriver.Firefox(executable_path=geckobin, options=options)

browser = webdriver.Firefox(options=options)
```

Set the URL of the page you want to grab the screenshot for:

```python
url = "https://livetiming.tsl-timing.com/191231"
url = 'https://livetiming.tsl-timing.com/191209'
url = 'https://livetiming.tsl-timing.com/191431'#brscc april 6
#url='https://livetiming.tsl-timing.com/191403' #btcc april 6
url='https://livetiming.tsl-timing.com/191521' #croft barc april 13
url='https://livetiming.tsl-timing.com/191851' #donington historic
```

Some web pages take time to load. For example, the TSL live timing screens are likely to show a spinny thing when a timing screen page is first loaded.

*The TSL timing screen works by loading a page container, then sets up a data connection via a web socket to retrieve the actual timing updates. If we are just grabbing a screenshot of the rendered timing screen, we need to make sure we wait long enough for the spinny thing to disappear and for the table to be rendered.*

```python
#desiredId = 'tablebody' #The HTML id of a tag we want to be visible before we grab the page screenshot
undesiredId = 'loading' #The HTML tag of an element we want to be invisible before we grab the page screenshot
```

Set the name of the image file you want to save the screenshot to:

```python
outfile = 'screenshot.png'
```

Now we can grab the screenshot:

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
```

```python
#Set a default screensize...
#There are other ways of setting up the browser so that we can grab the full browser view,
#even long pages that would typically require scrolling to see completely
browser.set_window_size(800, 400)
browser.get(url)

#EC.visibility_of_element_located
#EC.presence_of_element_located
#EC.invisibility_of_element_located

#Let's wait for the spinny thing to disappear...
element = WebDriverWait(browser, 10).until( EC.invisibility_of_element_located((By.ID, undesiredId)))

#Save the page
browser.save_screenshot( outfile )
print('screenshot saved to {}'.format(outfile))
```

Preview the captured page:

```python
from IPython.display import Image
Image(outfile)
```

```python
from selenium.common.exceptions import TimeoutException

#This will return something if it loads within the specified maxwait / timeout
def initBrowser(url, maxwait=10, maxtries=3):
    ''' Launch a new browser and '''
    browser = webdriver.Firefox(options=options)
    browser.get(url)
    
    try:
        element = WebDriverWait(browser, maxwait).until( EC.invisibility_of_element_located((By.ID, undesiredId)))
    except TimeoutException as e:
        browser.close()
        maxtries = maxtries-1
        if maxtries:
            #Try again with a longer wait, after a backoff
            time.sleep(maxwait)
            return initBrowser(url, maxwait*1.5, maxtries)
        
        return None

    return browser


#Note that we can also reload a page (ctrl-R) with:
#browser.refresh()
```

```python
browser=initBrowser(url)
browser.save_screenshot( outfile )
Image(outfile)
```

## Tabs

- Classification: current ranking
- Tracking: track map
- Weather:
- Statistics: fastest laps etc


We can also grab other tabs...

```python
#Classification, Weather, Statistics

tabId = "Classification"
element = browser.find_element_by_id(tabId)
element.click()
element = WebDriverWait(browser, 10).until( EC.visibility_of_element_located((By.ID, tabId)))

ofn = '{}_{}.png'.format(outfile.replace('.png',''),tabId)

#Save the page
browser.save_screenshot( ofn )
print('screenshot saved to {}'.format(ofn))
Image(ofn)
```

### Grab some metadata

The timing screen includes information about the race series and the session the timing screen relates to. We can pull that data out of the timing screen to act as metadata.

```python
#https://stackoverflow.com/a/12150013/454773
from selenium.common.exceptions import NoSuchElementException

def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True

def text_value_from_xpath(driver, xpath):
    try:
        el = driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return ''
    return el.text

#check_exists_by_xpath(browser, '//*[@id="currentflag"]')
```

```python
#Let's use the classification screen as our "base" screen
tabId='Classification'
element = browser.find_element_by_id(tabId)
element.click()
element = WebDriverWait(browser, 10).until( EC.visibility_of_element_located((By.ID, tabId)))

```

Get the series name:

```python
series_path='//*[@id="seriesName"]/span[2]'

series = text_value_from_xpath(browser, series_path)
series
```

And the session:

```python
session_path = '//*[@id="sessionName"]/span[2]'
session = text_value_from_xpath(browser, session_path )
session
```

We could use this information to give us meaningful filenames when we save timing screen images or data.

```python
#Red flag
#//*[@id="currentflag"]
flag_path='//*[@id="currentflag"]'
flag = text_value_from_xpath(browser, flag_path )
flag
```

```python
sessionTime_path ='//*[@id="sessionTime"]'
sessionTime = text_value_from_xpath(browser, sessionTime_path )
sessionTime
```

```python
import string
def tableNameCleaner(t):
    if t:
        t = t.replace(' - ','_').replace('-','_').replace(' ','_').translate(str.maketrans('','',string.punctuation.replace('_',''))).upper()
        t = t.replace('QUALIFYING','Q').replace('RACE','R').replace('CHAMPIONSHIP','')
    return t
    
def getInfo(browser):
    series_path='//*[@id="seriesName"]/span[2]'
    series = text_value_from_xpath(browser, series_path)
    
    session_path = '//*[@id="sessionName"]/span[2]'
    session = text_value_from_xpath(browser, session_path )

    return {'series':series,
            'session':session,
             'tablename': tableNameCleaner('{}_{}'.format(series,session)) }
```

```python
 getInfo(browser)
```

### Grabbing Images of the Timing Screen

We can create a simple function to use *selenium* to grab png screenshots of a particular tab on the timing screen.

```python
def setPageTab(browser, tabId='Classification', ofn=None, preview=True, link=True):
    ''' Simple function to view a particular tab within a TSL timing screen. '''
    
    #Check the page has loaded
    element = WebDriverWait(browser, 10).until( EC.invisibility_of_element_located((By.ID, undesiredId)))
    
    #ofn is output filename
    element = browser.find_element_by_id(tabId)
    element.click()
    element = WebDriverWait(browser, 10).until( EC.visibility_of_element_located((By.ID, tabId)))

    ofn = ofn if ofn is not None else '{}_{}.png'.format(outfile.replace('.png',''),tabId)

    if preview or link:
        #Save the page
        browser.save_screenshot( ofn )
        print('screenshot saved to {}'.format(ofn))
        
        if preview:
            display(Image(ofn))

        if link:
            return ofn
```

```python
#url = 'https://livetiming.tsl-timing.com/191209'
setPageTab(browser,'Classification', preview=False, link=True)
```

We could create a meaningful filename from the series and session metadata. For example:

```python
#get file name
fn = '{}_{}.png'.format(series.replace('/','_'), session.replace('/','_') )

setPageTab(browser, 'Classification', fn)
```

We can get also access to the actual HTML via the element's `innerHTML()` attribute:

`el.get_attribute('innerHTML')`

If we grab the `<table>` element, this actually returns the contents contained *within* the table element, so we would need to recreate the outer `<table>` tag before we try to scrape the table data into a *pandas* dataframe. If we grab a `<div>` element that contains the table, we can scrape it directly into a *pandas* dataframe.

```python
#classification data
xpath = '//*[@id="ResultsTableContainer"]'
el = browser.find_element_by_xpath(xpath)
```

```python
import pandas as pd

df = pd.read_html( el.get_attribute('innerHTML'))[0].dropna(axis=1,how='all')
df.rename(columns={'Time/Gap':'TimeGap',
                   'Unnamed: 1':'Penalties'}, inplace=True)
df.head()
```

```python
df.dtypes
```

We also need to get the flag status. This is on path `//*[@id="tablebody"]/tbody/tr[3]/td[2]/div[1]`

```python
browser=initBrowser(url)
```

```python
els = browser.find_elements_by_xpath('//*[@id="tablebody"]/tbody/tr[*]/td[2]/div[1]')
for el in els:
    print(el.get_attribute("class").split(' ')[-1])
```

The `posIcon` also captures whether the car is in the pit (`posIconInPit`). This may record a car going in to the pit on a lap so the laptime with the pit stop included may be recorded on the following lap.

Let's make a function for that:

```python
def getPosIcon(browser):
    els = browser.find_elements_by_xpath('//*[@id="tablebody"]/tbody/tr[*]/td[2]/div[1]')
    icons=[]
    for el in els:
        icons.append(el.get_attribute("class").split(' ')[-1])
    return pd.DataFrame({'icons':icons})

getPosIcon(browser)
```

```python
df['icons'] = getPosIcon(browser)['icons']
df
```

```python
#Create this as a temporary table for a particular session
#Then think about merging into to a full table overal sessions / events etc

#The Flag is not within the table but can be captured to give a crude indication of flag conditions
#I wonder if I should also be capturing time of day somewhere as a crude record of sample times?
classification_table = '''
CREATE TABLE IF NOT EXISTS  "{_table}" (
  "Pos" INTEGER,
  "Penalties" TEXT,
  "Icons" TEXT,
  "No" INTEGER,
  "Cl" TEXT,
  "PIC" INTEGER,
  "Name" TEXT,
  "Laps" INTEGER,
  "Gap" TEXT,
  "Diff" TEXT,
  "Best" TEXT,
  "BestInS" FLOAT,  
  "Last" TEXT,
  "LastInS" FLOAT,
  "PS" FLOAT,
  "S1" TEXT,
  "V1" FLOAT,
  "S2" TEXT,
  "V2" FLOAT,
  "S3" TEXT, 
  "VF" FLOAT,
  "Flag" TEXT,
  PRIMARY KEY (No, Laps) ON CONFLICT IGNORE
);
'''
#PK WITH LAST, OR TIMEGAP??? Or just go with Number/Lap PK the first time we get that combination
#dan then ignore any updates to it?
#Rather that upsert, just do an insert, so we only get new Number/Laps combinations?

fastest_laps_table = '''
CREATE TABLE IF NOT EXISTS  "{_table}" (
    "NO" INTEGER,
    "NAME" TEXT,
    "TIME" TEXT,
    `TIME OF DAY` TEXT,
    "LAP" INTEGER,
    `AVG. SPEED (MPH)` FLOAT,
    "VEHICLE" TEXT
);
'''

flags_table = '''
CREATE TABLE IF NOT EXISTS  "{_table}" (
    "COLOUR" TEXT,
    `TOTAL TIME` TEXT,
    `TOTAL LAPS` INTEGER,
    "COUNT" INTEGER
);
'''

leaderhistory_table = '''
CREATE TABLE IF NOT EXISTS  "{_table}" (
    "NO" INTEGER,
    "NAME" TEXT,
    `FROM LAP` TEXT,
    `LAPS LED` INTEGER,
    `DISTANCE (MILES)` FLOAT,
    "VEHICLE" TEXT
);
'''
```

```python
import sqlite3
from sqlite_utils import Database

dbname='may4test3.db'

#!rm $dbname
conn = sqlite3.connect(dbname, timeout=10)

_table = 'tsl_timing_classification'

#Setup database tables
c = conn.cursor()
c.executescript(classification_table.format(_table=_table))


DB = Database(conn)

```

If we grab the classification table with a period slightly less than that of the fastest sector time, and upsert on the table using the (car number, lap, gap) as a unique key, then we should make sure we capture all the laps and the sector times, though we will need to do a little bit of processing of the multiple rows captured for each driver for each lap. (As the timing screen is live, as the leader goes onto a new lap, every other driver goes at least 1 Lap behind; we have to recover from such things.)

The *(car number, lap, previous lap)* combination should also be unique. (I need to think, would that guarantee we capture section times?).

My original method used upserts to prevent collisions, but that's wrong, I think. SQLite lets us add a condition to the PK in a table definition that will ignore conflicts, so we can add a car number / lap combination to the tabe as soon as we see it, and then if we upload it again, perhaps with the `TimeGap` reset to `Lap 1` by the lead car starting a new lap, we can just ignore it.

```python
url = 'https://livetiming.tsl-timing.com/191851'
browser = webdriver.Firefox(options=options)
browser.get(url)

#We need a delay after this or we may break the following by trying to look in the page for an element
#before it's had time to properly load and render
element = WebDriverWait(browser, 10).until( EC.invisibility_of_element_located((By.ID, undesiredId)))
```

```python
#should perhap have a wait here to just make sure evrything is loaded...
#Or perhaps better, a guard at end of previous cell
#
setPageTab(browser, 'Classification')
```

```python
import time

xpath = '//*[@id="ResultsTableContainer"]'


#This should really be while not finished
while True:
    #Grab the timing screen
    el = browser.find_element_by_xpath(xpath)
    
    #Parse out the data
    df = pd.read_html( el.get_attribute('innerHTML'))[0].dropna(axis=1,how='all')
    #Tidy up the column names
    df.rename(columns={'Time/Gap':'Gap',
                       'Unnamed: 1':'Penalties'}, inplace=True)
    #Upsert the date
    #DB[_table].upsert_all(df.to_dict(orient='records'))
    #insert the date
    DB[_table].insert_all(df.to_dict(orient='records'))
    print('.',end='')
    time.sleep(15)
    
#TO DO - also record time stamp; and maybe in another table, flag status vs timestamp
#so then we can easily retrieve eg approximate safety car periods etc
```

I need to rethink the logic...

We need to grab the timing screen just after a car has lapped; at this point, the sector times will be the sector times from the previous lap.


Thinking this through: we need to sample at a rate less than the min sector time to grab all the sector time data. To capture the gap data, we need to sample between the last car on the lead lap and the leader (this makes sure we have a full column of times). Or we just forgo the Gap as noise? What's important is that we get the lap and sector times? Which is the first sampling of the row for a particular (vehicle number / lap) key pair.

When the leader laps, the other cars show `1 Lap` in the `Gap` column. When one of those car laps, we want to capture it. The unique key is the car number, and the lap number. When a car completes a lap, all the sector times are in place, lap counter increments and so does the last lap time. So we don't need an upsert. We need to add the new PK key and ignore any other updates.

To get sector times, we only need to sample with a period less than the minimum sector time. To grab the correct gap to leader time, the sample for a driver on a given lap has to be made while they are on the lead lap. The diff should always be correct?

So need to check the df to see if the PK is already taken, and if it is, don't add the row. Alternatively, we can define the SQLite database table to ignore any attempt to add a row for which the PK is already taken.

```python
dbname='testlive4.db'

#!rm $dbname
conn = sqlite3.connect(dbname, timeout=10)

q="SELECT * FROM tsl_timing_classification;"
pd.read_sql(q,conn)
```

The times are reported as strings, which would could cast to intervals (the pandas 

```python
#Preferred time format
def formatTime(t):
    return float("%.3f" % t)

# Accept times in the form of hh:mm:ss.ss or mm:ss.ss
# Return the equivalent number of seconds and milliseconds
def getTime(ts, ms=False):
    ts=str(ts)
    t=ts.strip()
    if t=='': return pd.to_datetime('')
    if ts=='P': return None
    if 'LAP'.lower() in ts.lower():
        ts=str(1000*int(ts.split(' ')[0]))
    t=ts.split(':')
    if len(t)==3:
        tm=60*int(t[0])+60*int(t[1])+float(t[2])
    elif len(t)==2:
        tm=60*int(t[0])+float(t[1])
    else:
        tm=float(pd.to_numeric(t[0], errors='coerce'))
    if ms:
        #We can't cast a NaN as an int
        return float(1000*formatTime(tm))
    return float(formatTime(tm))
```

```python
df['LastInS']=df['Last'].apply(getTime)
df['BestInS']=df['Best'].apply(getTime)
df.head()
```

We can then easily save the dataframe to a CSV file:

```python
df.to_csv('test1.csv')
```

#### Saving the Data to a Database
We can also save the data into a SQLite database.

There are several ways of doing this, of varying degrees of casulaness. The simplest way might be to create a separte table for each race (that is, each series and session combination) but that would explode the number of tables.

If we want to use fewer tables, then we need to know which series/session timing screens are alike (that is, have the same format / columns). It may be that all the sreens are the same, or it may be that practice, qualifying and race screens show different information. We would also need to check whether each series records the same columns in the timing screen if we are to have a single table for "race" data for example.

Also note that we would need to add some columns to the table if we are including data from mutliple series and/or sessions in the same table to identify which series/session any particular row in the table refers to.

```python
import sqlite3
conn = sqlite3.connect("test.db")
df.to_sql('test1', con=conn, index=False, if_exists='replace')
```

We can now query the data:

```python
sql = 'SELECT * FROM test1 LIMIT 3'
pd.read_sql_query(sql, conn)
```

Note that we might also want to think about defining the database columns more formally if we know the structure of the timing screen data we want to record.


## Viewing Other Tabs

We can also grab data from tabs other than the *Classification* tab:

```python
browser = initBrowser(url)
setPageTab(browser, 'Statistics')
```

```python
#get statistics table
#//*[@id="StatsTableContainer"]/div[3]/div[2]/table
xpath = '//*[@id="StatsTableContainer"]/div[3]/div[2]/table'
el = browser.find_element_by_xpath(xpath)
el.text
#'Competitors: 30\nPlanned Start: 15:10\nActual Start: 15:25:00.510\nFinish Time:\nTotal Laps 107\nTotal Distance Covered: 129.2501 mi.\nTrack Length: 1.2079 mi.'
```

```python
pd.read_html( '<table>{}</table>'.format(el.get_attribute('innerHTML')))[0].dropna(axis=1,how='all')
```

```python
#Flags table
xpath = '//*[@id="StatsTableContainer"]/div[3]/div[1]/table[1]'
el = browser.find_element_by_xpath(xpath)
el.text
#'COLOUR TOTAL TIME TOTAL LAPS COUNT\nGREEN 00:05:45 5 1\nRED 00:00:29 0 1\nSAFETY CAR 00:00:00 0 0\nFCY 00:00:00 0 0'
```

```python
pd.read_html( '<table>{}</table>'.format(el.get_attribute('innerHTML')))[0].dropna(axis=1,how='all')
```

```python
#fastest laps
fastlap_path ='//*[@id="fastestLapTable"]'
el = browser.find_element_by_xpath(fastlap_path)
el.text
#'NO CL NAME TIME TIME OF DAY LAP AVG. SPEED (MPH) VEHICLE\n15\nM\nOLIPHANT * 54.140 15:29:02.984 4 80.32 BMW 330i M Sport\n116\nM\nSUTTON 54.685 15:28:24.626 3 79.52 Subaru Levorg\n25\nM\nNEAL 54.983 15:28:18.112 3 79.08 Honda Civic Type R\n1\nM\nTURKINGTON 55.127 15:28:07.375 3 78.88 BMW 330i M Sport\n303\nI\nSIMPSON 55.228 15:27:58.303 2 78.73 Honda CIvic Type R\n80\nM\nINGRAM 55.449 15:27:17.128 2 78.42 Toyota Corolla\n77\nM\nJORDAN 56.278 15:27:14.039 2 77.27 BMW 330i M Sport\n15\nM\nOLIPHANT * 56.858 15:27:13.242 2 76.48 BMW 330i M Sport\n1\nM\nTURKINGTON 57.049 15:27:12.248 2 76.22 BMW 330i M Sport'
```

```python
pd.read_html( '<table>{}</table>'.format(el.get_attribute('innerHTML')))[0].dropna(axis=1,how='all')
```

```python
#leader history
leaderHistory_path = '//*[@id="leaderHistory"]/div/table'
el = browser.find_element_by_xpath(leaderHistory_path)
el.text
#NO NAME FROM LAP LAPS LED DISTANCE (MILES) VEHICLE\n19\nHENSHALL 6 1 1.64 Caterham 310R\n77\nSAWYER 4 2 3.28 Caterham 310R\n25\nMCCORMACK 2 2 3.28 Caterham 310R\n11\nPERRY 1 1 1.64 Caterham 310R
```

```python
pd.read_html( '<table>{}</table>'.format(el.get_attribute('innerHTML')))[0].dropna(axis=1,how='all')
```

Create a function to grab statistcs tab data.

```python
#TO DO
def statisticsData(browser):
    
    setPageTab(browser, 'Statistics')
    
    #flags
    xpath = '//*[@id="StatsTableContainer"]/div[3]/div[1]/table[1]'
    el = browser.find_element_by_xpath(xpath)
    df_flags = pd.read_html( '<table>{}</table>'.format(el.get_attribute('innerHTML')))[0].dropna(axis=1,how='all')
    
    #fastest laps
    fastlap_path ='//*[@id="fastestLapTable"]'
    el = browser.find_element_by_xpath(fastlap_path)
    df_fastest = pd.read_html( '<table>{}</table>'.format(el.get_attribute('innerHTML')))[0].dropna(axis=1,how='all')
    
    #leader history
    leaderHistory_path = '//*[@id="leaderHistory"]/div/table'
    el = browser.find_element_by_xpath(leaderHistory_path)
    df_leaderhistory = pd.read_html( '<table>{}</table>'.format(el.get_attribute('innerHTML')))[0].dropna(axis=1,how='all')

    return df_flags, df_fastest, df_leaderhistory

```

```python
statisticsData(browser)
```

```python
#get file name
fn = '{}_{}.png'.format(series, session )

setPageTab(browser, 'Classification', fn)
```

```python
#Doesn't work?
trackDisplayName_path ='//*[@id="weatherConditions"]/span[2]'
trackDisplayName = text_value_from_xpath(browser, trackDisplayName_path )
trackDisplayName
```

```python
#Doesn't work?
weatherConditions_xpath = '//*[@id="weatherConditions"]/span[4]'
weatherConditions = text_value_from_xpath(browser, weatherConditions_xpath )
weatherConditions
```

```python
#Doesn't work?
trackConditions_xpath = '//*[@id="weatherConditions"] '
trackConditions = text_value_from_xpath(browser, trackConditions_xpath )
trackConditions
```

## Automated Grab

The aim here is to grab a copy of the screen classification when the race has finished.

(How is finished flagged? Eg if the clock has reached zero do cars get to finish the lap they are on? At what point does "FINISHED" appear?)


*(If we want to run browsers over several timing screens, eg for different meetings on the same day, it may be worth looking to something like https://github.com/micahscopes/nbmultitask so we could launch several watchers, one per timing screen, in separate, non-blocking processes.)*

```python
#flag status is something like"

#FINISHED
#RUNNING
#RED FLAG
#Scheduled Start: 16.55
#Safety Car
```

Set up the database:

```python
def initDb(dbname='test.db'):
    
    #TO DO: change to py fn
    #!rm $dbname
    
    conn = sqlite3.connect(dbname, timeout=10)

    #Setup database tables
    c = conn.cursor()
    #c.executescript(classification_table)


    DB = Database(conn)
    #_table = 'tsl_timing_classification'
    #
    return c, DB
```

```python
import hashlib

#The _table_hash will persist in the function
def timingScreenToDB(browser, DB, _table='testTable', _table_hash={'hash':''}, resettable=True):#, period=15):

    #check we're on the right tab
    setPageTab(browser, 'Classification', preview=False)
    
    
    xpath = '//*[@id="ResultsTableContainer"]'

    #Grab the timing screen
    el = browser.find_element_by_xpath(xpath)

    #Parse out the data
    df = pd.read_html( el.get_attribute('innerHTML'))[0].dropna(axis=1,how='all')
                     
    #Get a hash of the table; if it's the same as last time, refresh the page just this once...
    _table_hash_new =  hashlib.md5(df.to_html().encode('utf-8')).hexdigest()
    if _table_hash['hash'] == _table_hash_new and resettable:
        print('hmmm... stuck page? Try a refresh...')
        browser.refresh()
        timingScreenToDB(browser, DB, _table, False)
    _table_hash['hash'] == _table_hash_new
                     
    #Tidy up the column names
    df.rename(columns={'Time/Gap':'Gap',
                       'Unnamed: 1':'Penalties'}, inplace=True)
    
    #Get the icon status
    df['icons'] = getPosIcon(browser)['icons']
    
    #Add time in seconds for best and last
    #Getting a key not found error from a fresh start for some reason, so guard against that
    if 'Last' in df:
        df['LastInS']=df['Last'].apply(getTime)
    if 'Best' in df:
        df['BestInS']=df['Best'].apply(getTime)
    
    #Get the flag status
    flag = text_value_from_xpath(browser, flag_path )
    df['Flag'] = flag
        
    #Upsert the date
    #DB[_table].upsert_all(df.to_dict(orient='records'))
    #insert the data - this assumes the insert conflict ignore definition on the table
    DB[_table].insert_all(df.to_dict(orient='records'))
    #print('.',end='')
    #time.sleep(period)

    #outfile='tmp.png'
    #browser.save_screenshot( outfile )
    #Can we get this to just update the same image?
    #display(Image(outfile))
    
    #TO DO - also record time stamp; and maybe in another table, flag status vs timestamp
    #so then we can easily retrieve eg approximate safety car periods etc
```

The timing screen goes into a blank state when waiting for a new race. We may need to refresh it every so often when waiting for a new race to start. Do this with: `browser.refresh()`

Note that if we do this we need to set a wait for the page to load before we try to work on it.

```python
#Immortalise statistics in DB

## TO DO - BROKEN - I think sqlite_utils is messing up on colnames again
# A workaround would to be have a column name cleaner and redefine the table definitions

def initStatsDBTables(c, _table):
    c.executescript(fastest_laps_table.format(_table=_table))
    c.executescript(flags_table.format(_table=_table))
    c.executescript(leaderhistory_table.format(_table=_table))


def statisticsScreenToDB(browser, DB, _table='test_stats'):
    df_flags, df_fastest, df_leaderhistory = statisticsData(browser)
    
    DB['{}_flags'.format(_table)].insert_all(df_flags.to_dict(orient='records'))
    DB['{}_fastest'.format(_table)].insert_all(df_fastest.to_dict(orient='records'))
    DB['{}__leader_history'.format(_table)].insert_all(df_leaderhistory.to_dict(orient='records'))

```

```python
browser=initBrowser(url)

df_flags, df_fastest, df_leaderhistory = statisticsData(browser)
df_flags, df_fastest, df_leaderhistory
```

```python
DB['{}_flags'.format(_table)].insert_all(df_flags.to_dict(orient='records'))
```

```python
statisticsScreenToDB(browser, DB, _table)
```

```python
#initStatsDBTables(c, _table)
```

```python
df_fastest.to_dict(orient='records')
```

```python
df_flags, df_fastest, df_leaderhistory = statisticsData(browser)
df_flags.to_dict(orient='records')
```

```python
statisticsScreenToDB(browser, DB)
```

```python
url_brscc = 'https://livetiming.tsl-timing.com/191431'
url_btcc='https://livetiming.tsl-timing.com/191403' #btcc april 6
```

```python
browser.get(url_btcc)
```

```python
url='https://livetiming.tsl-timing.com/191521'
#url='https://livetiming.tsl-timing.com/191531'

```

```python
getInfo(browser)
```

```python
_table= getInfo(browser)['tablename']
c.executescript(classification_table.format(_table=_table))
```

If there is a long wait to the next race, the timing screen reports a `Scheduled Start` time. We can compare the current time to the scheduled start time, and if there is a long wait, we could go to sleep for a bit...

So how can we work out how long to wait?

```python
#What's the time now?
from datetime import datetime
n = datetime.now()
n
```

```python
#What's the schedule start time?
from dateutil import parser
s = parser.parse("{} {} {} {}".format(n.year, n.month, n.day, '15:50'))
s
```

```python
#What's the difference?
(s-n).seconds
```

```python
n = datetime.now()
s = parser.parse("{} {} {} {}".format(n.year, n.month, n.day, '17:40'))
(s-n).days
```

```python
def waitTimeToStart(tts, delay=120):
    ''' Calculate a sensible sleep time given the cirrent time and the scheduled start time.
        The delay gives the time before the scheduled start time we're happy to sleep until.
    '''
    n = datetime.now()
    s = parser.parse("{} {} {} {}".format(n.year, n.month, n.day, tts))
    tts = (s-n)
    
    #If the time is after the scehduled start time, wait a minute...
    #Seems we don't get negative seconds?
    if tts.days < 0: 
        return 60
    #If the time is within the prescribed delay period, no need for an extra wait
    elif tts.seconds<delay:
        return tts.seconds
    else:
        return (s-n).seconds - delay
```

```python
def emailReport(info):
    '''Holding pattern - defined below...'''
    print('We could do emailing here....')
    display(Image(info['finalscreen']))
```

```python
c, DB = initDb('may4test5.db')
```

```python
import time

#Start to build up the logic

period=75
period_lap = 95 #This is the time we'll after we record the race as finished before declaring a result
#This means we declare a result at most period+period_lap after we first see FINISHED flag

finishedwait=60
refresh_before_scheduled_start = 120

send_email = True #Do we want to send email
sent_email = False #Have we sent an email for this race

#If we are in a race
browser = initBrowser(url)



showpreview=True
while True:
    
    prevSessionTime = None #heuristic to try to spot if we are stuck
    #If we are stuck, reload the browser
    shoved=False #part of the keep it running heuristic
    
    sent_email = False
    
    #Reload the browser after each race
    browser = initBrowser(url)
    info =  getInfo(browser)
    
    #Need to check we have a valid table name
    #If not, do a delay and then continue back to repeat the loop
    _table = getInfo(browser)['tablename']
    
    if not _table or _table=='':
        print('Nothing seems to be on the timing screen...Wait a couple of minutes...')
        wait(120)
        continue
        
    previewed = showpreview
    setPageTab(browser, 'Classification', preview=showpreview)
    
    #Start doing setup for a particular race here

    flag = text_value_from_xpath(browser, flag_path )
    if flag.upper()=='FINISHED':
        print('Still on screen from previous race')
        time.sleep(finishedwait)
        showpreview=False
        continue
    
    #If the scheduled start is some time away, wait until a few mins before the scheduled start
    #Or should we keep polling...
    #What happens over lunch? The previous table chekc should catch things there?
    
    #eg: Scheduled Start: 15.50 20:00
    if flag.startswith('Scheduled Start'):
        waitfor = waitTimeToStart(flag.replace('Scheduled Start','').split()[1],refresh_before_scheduled_start) 
        print('Race start {}; now {} so sleeping for {}s'.format(flag,datetime.now(),waitfor))
        time.sleep( waitfor )
        showpreview=False
        continue
        
    #Try to limit how often we display the screen
    #If we showed it on the way in, no need to show it now.
    #If we didn't show it on the way in, preview it here.
    showpreview=True
    if not previewed:
        setPageTab(browser, 'Classification', preview=showpreview)
    
    print("Creating table {} if it doesn't already exist".format(_table))
    c.executescript(classification_table.format(_table=_table))

    race_on = True if flag!='Finished' else False
    
    awaiting_result=True
    letsgoracing = True
    while race_on and awaiting_result:
        
        #If for some reason the process goes to sleep,
        # ensure we don't add data to the wrong table when we wake up...
        if _table != getInfo(browser)['tablename']:
            print('hmmm, did I nod off there?')
            break
            
        if letsgoracing:
            print('letsgoracing...')
            letsgoracing = False
            
        #Better to use some heuristics here eg based on time left in sessiontime
        #Only issue there is if a race is red flagged so is race clock/sessionTime?
        #So maybe try to grab close race start time, ish, and sessionTime at that point
        #and generate a heuristic about earliest time race is expected to finish?
        #For some reason, the flag doesn't seem to update in the browser properly?
        flag = text_value_from_xpath(browser, flag_path )
        
        timingScreenToDB(browser, DB, _table)
        print('.',end='')

        sessionTime = text_value_from_xpath(browser, sessionTime_path )
        print(flag, sessionTime, end='')
        
        
        #Hack for now
        statsdone=False    
        while flag.upper()=='FINISHED':
            #TO DO - Grab statistics tables and save to DB
            #We need to wait and do a final check - wait for time approx one lap
            #Get worst best lap time and use that? 
            time.sleep(period_lap)
            #Then need to get guaranteed final times and stats - but make sure screen is still there..
            #Need to guard that we do not do this if we have moved on to another race...
            #Note that this field may take some time to populate after a browser refresh?
            flag = text_value_from_xpath(browser, flag_path )

            if flag.upper()=='FINISHED':
                timingScreenToDB(browser, DB, _table)
                if not statsdone:
                    initStatsDBTables(c, _table)
                    statisticsScreenToDB(browser, DB, _table)
                    statsdone=True
                #keep refreshing
                browser = initBrowser(url)
                final_screen = setPageTab(browser,'Classification', preview=False, link=True)
                #TO DO - a lot of the following is dependent on things later in the notebook...
                if send_email and not sent_email:
                    #server = smtplib.SMTP_SSL("smtp.gmail.com", port, context=context)
                    #server.login(sender_email, sender_password)

                    #send_to = [] if  not 'send_to' in locals() else locals()['send_to']
                    #info =  getInfo(browser)
                    #send_from = sender_email
                    #subject = 'Autogenerated bits for {} - {}'.format(info['series'], info['session'])
                    #text = "Some automatically generated bits from {} - {}. Check the attachments...".format(info['series'], info['session'])
                    #outfiles = [final_screen, get_best_csv(_table),get_laps_csv(_table), get_boxplot(_table)]
                    #try:
                    #    print('mailing...')
                    #    send_mail(server, send_from, send_to, subject, text, files=outfiles)
                    #except:
                    #    print('mail send failed')
                    #html email needs work?
                    #send_mail_html(server, sender_email, receiver_email,
                    #               subject, text, htmltext, files=[final_screen])
                    emailinfo = {'finalscreen':final_screen}
                    emailReport(emailinfo)
                    sent_email = True
            print('Session should have completely finished...')
            awaiting_result = False
            #Also grab final classification table as a complete, separate thing
            #?need to create table?
            #timingScreenToDB(browser, DB, '{}_final_timing_screen'.format(_table))
            #setPageTab(browser, 'Statistics')
            #statisticsScreenToDB(browser, DB, '{}_final_statistics'.format(_table))

        #carry on waiting
        time.sleep(period)

        #Sometimes things seem to get stuck on the timing screen, so give it a shove
        sessionTime = text_value_from_xpath(browser, sessionTime_path )
        if prevSessionTime and sessionTime==prevSessionTime:
            if shoved:
                #Let's try and go back to the start...
                awaiting_result = False
            print('shove..')
            prevSessionTime = sessionTime
            #browser = initBrowser(url)
            browser.refresh()
            shoved = True

fn = '{}_{}.png'.format(series, session )


#Don't need to get the URL? Just dump the screenshot instead?
#Browser is already good and if meeting is busy we may not be able to get a new connection onto timing screen?
#setPageTab(browser, 'Classification', fn)

browser.save_screenshot( fn )
```

```python
def emailReport(info):
    server = smtplib.SMTP_SSL("smtp.gmail.com", port, context=context)
    server.login(sender_email, sender_password)

    send_to = [] if  not 'send_to' in locals() else locals()['send_to']

    subject = 'Autogenerated bits for {} - {}'.format(info['series'], info['session'])
    text = "Some automatically generated bits from {} - {}. Check the attachments...".format(info['series'], info['session'])
    outfiles = [final_screen, get_best_csv(_table),get_laps_csv(_table), get_boxplot(_table)]
    print('mailing...')
    
    send_mail(server, send_from, send_to, subject, text, files=outfiles)
    
    #print('failed...')
    #html email needs work?
    #send_mail_html(server, sender_email, receiver_email,
    #               subject, text, htmltext, files=[final_screen])

emailReport(info)
```

```python
send_from
```

```python
def get_best_csv(_table):
    sql = 'SELECT No, Name, Cl, MIN(Best) FROM {} WHERE Best IS NOT NULL GROUP BY No ORDER BY Cl, MIN(Best)'.format(_table)
    outdf = pd.read_sql_query(sql, conn)
    
    #TO DO - is this in the table anyway?
    outdf['BestInS']=outdf['MIN(Best)'].apply(getTime)
    
    fn='{}_best.csv'.format(_table)
    outdf.to_csv(fn,index=False)
    return fn

fn = get_best_csv(_table)
!head {fn}
```

```python
sql = 'SELECT * FROM {} LIMIT 2'.format(_table)
pd.read_sql_query(sql, conn)
```

```python
def get_laps_df(_table):
    sql = 'SELECT No, Name, Cl, Laps, Last FROM {} ORDER BY No'.format(_table)
    outdf = pd.read_sql_query(sql, conn)
    
    #TO DO - is this in the table anyway?
    outdf['LastInS']=outdf['Last'].apply(getTime)
    
    return outdf

def get_laps_csv(_table):
    outdf = get_laps_df(_table)
    fn = '{}_laps.csv'.format(_table)
    outdf.to_csv(fn,index=False)
    return fn

fn = get_laps_csv(_table)
!head {fn}
```

```python
outdf
```

```python
from IPython.display import clear_output

def get_boxplot(_table, fn=None):
    outdf = get_laps_df(_table)
    p = outdf[['No','LastInS']].boxplot(by='No')
        
    fig = p.get_figure()
    fn = '{}.png'.format(_table) if fn is None else fn

    fig.savefig(fn)
    return fn

#matplotlib will autodisplay the image
fn = get_boxplot(_table)

#Display from file
Image(fn)
```

```python
#!pip3 install rpy2
#%load_ext rpy2.ipython
#COuld we integrae R code in the notebook for plotting?
```

# Emailing the screenshot

Having grabbed the screenshot, we might now want to email it to somebody.

We can do that with the `smtplib` package if we have the details of an SMTP server we can connect to.

For example, if you have a GMail account:

```python
import smtplib, ssl, getpass
from IPython.display import clear_output


```

```python

sender_email = input("Type your Email address and press enter: ")
sender_password =  getpass.getpass()


receiver_email = input("Email address for test send: ")#"user@example.com"  # Enter receiver address
message = """\
Subject: Test

Test message from code..."""


smtp_server="smtp.gmail.com"
port = 465  # For SSL
# Create a secure SSL context
context = ssl.create_default_context()

with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, receiver_email, message)
    
#Clear the output so we don't share emails in saved notebook
clear_output()
```

```python
receiver_email = input("Email address for test send: ")#"user@example.com"  # Enter receiver address
with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, receiver_email, message)

#Clear the output so we don't share emails in saved notebook
clear_output()
```

```python
def getMailBlurb(browser, subject=None, text=None):
    subject = ''
    
    text="""Here's some autograbbed data from the end of the race...
    
    It's all automated.
    
    There may be attachments..
    """
```

```python
subject='Test email attachment'
text = """some text
Over several

lines"""

```

Let's go defensive and check we have at least one valid email to send to...

```python
#https://www.scottbrady91.com/Email-Verification/Python-Email-Verification-Script
import re

def checkEmails(addressesToVerify):
    ''' Tests one or more email addresses. Returns list of emails that parse. '''
    addressesToVerify = addressesToVerify if isinstance(addressesToVerify, list) else [addressesToVerify]
    
    regex = '^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$'

    validEmailAddresses = []
    for addressToVerify in addressesToVerify:
        if re.match( regex, addressToVerify):
            validEmailAddresses.append(re.match( regex, addressToVerify).group())

    #Return uniques
    return list(set(validEmailAddresses))


#checkEmails(['a.bkexample.com','a@bkexample.com','a@bkexample.com'])
#We could go further and check it's a valid email
#eg https://www.scottbrady91.com/Email-Verification/Python-Email-Verification-Script
#or other validation packages
```

```python
#https://stackoverflow.com/a/3363254/454773
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

def send_mail(server, send_from, send_to, subject='Test subject email', text='Test message text', files=None):
    if not send_from:
        print('No sender?')
        return
    
    send_to = checkEmails(send_to)
        
    assert isinstance(send_to, list)
    #assert isinstance(files, list)

    msg = MIMEMultipart()
    #The from can be different to the sender, which was used to login to mailgun
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fo:
            part = MIMEApplication(
                fo.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        print('attach part {}'.format(part['Content-Disposition']))
        msg.attach(part)



    #smtp = smtplib.SMTP(server)
    smtp = server
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()


    
#server = smtplib.SMTP_SSL("smtp.gmail.com", port, context=context)
#server.login(sender_email, sender_password)
#send_mail(server, sender_email, [receiver_email], subject, text, files=[outfile])
```

Sending with image inline as HTML email:

```python
cid = 0 #A unique id count for the image

#We'd probably need to rethink this for multiple images...
htmltext=''''<html><body><h1>Timing screen</h1>\n<div><img src="cid:{cid}"></div>\n</body></html>'''.format(cid=cid)
```

```python
import uuid
from email.mime.base import MIMEBase
from email import encoders

#ish via https://www.code-learner.com/python-send-html-image-and-attachment-email-example/
def add_image(msg, img, iid=0):
    uniqueId = '{}-{}-{}'.format(img.split('/')[-1], datetime.now().strftime('%Y%m%d%H%M%S'), uuid.uuid4())
    
    with open(outfile, 'rb') as f:
        # set attachment mime and file name, the image type is png
        mime = MIMEBase('image', 'png', filename=img)
        # add required header data:
        mime.add_header('Content-Disposition', 'attachment', filename=img)
        mime.add_header('X-Attachment-Id', str(iid))
        mime.add_header('Content-ID', '<{}>'.format(iid))
        # read attachment file content into the MIMEBase object
        mime.set_payload(f.read())
        # encode with base64
        encoders.encode_base64(mime)
        # add MIMEBase object to MIMEMultipart object
        msg.attach(mime)
    
def send_mail_html(server, send_from, send_to, subject, text, htmltext, files=None):
    
    if not send_from:
        print('No sender?')
        return
    
    send_to = checkEmails(send_to)
    
    if not send_to:
        print('No valid email addresses to send to.')
        return
    
    assert isinstance(send_to, list)
    assert isinstance(files, list)

    msg = MIMEMultipart('alternative')
    #the from can be different to the sender, which was used to login to mailgun
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    fid=0
    for f in files or []:
        add_image(msg, f, fid)
        fid += 1
        
    #It would make sense to add the images somehow into the htmltext
    #Maybe htmltext needs templating?
    msg.attach(MIMEText(htmltext, 'html', 'utf-8'))


    #smtp = smtplib.SMTP(server)
    smtp = server
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()
    

```

```python
#mailgun setup
```

```python
#This will guard that we have a receiver_email variable
receiver_email = [] if  not 'receiver_email' in locals() else locals()['receiver_email']

server = smtplib.SMTP_SSL("smtp.gmail.com", port, context=context)
server.login(sender_email, sender_password)
send_mail_html(server, sender_email, receiver_email, subject, text, htmltext, files=[outfile])
```

```python
#Not ssl?

#use tls
server = smtplib.SMTP(smtp_server, port)
# identify ourselves to smtp gmail client
server.ehlo()
# secure our email with tls encryption
server.starttls()
# re-identify ourselves as an encrypted connection
server.ehlo()

server.login(sender_email, sender_password)
send_mail(server, sender_email, receiver_email, subject='new test')

#server.quit()



```

## TO DO

On the emailer:

- tidy it up so there's a reasonable way of adding multiple images to HTML email and getting the IDs right...

On the screengrabber:

- keep checking the page, parsing it to look for when a session is complete, then send an email of the final classification etc.

*I'm not sure if this would require reloading the page or whether the socket connection to the live timing server works and selenium can just keep rechecking for when a particular id takes a `FINISHED` value?*
