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

# TSL - PDF Grabber

A notebook for finding and downloading TSL timing sheet PDFs.


```python
import datetime

#Use this year as default
YEAR = datetime.datetime.now().year

year = year

domain = 'http://www.tsl-timing.com'


results_url='http://www.tsl-timing.com/Results'

series = 'toca'
series_url='http://www.tsl-timing.com/Results/{}/{}'.format(series, year)

event_id = 191403

event_url='http://www.tsl-timing.com/event/{}'.format(event_id)
```

```python
download_dir_base = 'tsl_results_data'
```

```python
import requests
from bs4 import BeautifulSoup
import os
```

## Get All Results Info

Get a list of links to all clubs and series.

```python
resultspage=requests.get(results_url)
resultssoup=BeautifulSoup(resultspage.content)
```

```python
resultsseries=resultssoup.find('div',{'class':'clubListContainer'}).findAll('a')
resultsseries[0]
```

```python
import pandas as pd
```

```python
def get_TSL_series(results_url='http://www.tsl-timing.com/Results'):
    
    resultspage=requests.get(results_url)
    resultssoup=BeautifulSoup(resultspage.content)
    
    resultsseries=resultssoup.find('div',{'class':'clubListContainer'}).findAll('a')
    
    _data = []
    for seriesresult in resultsseries:
        _series_url = seriesresult['href']
        _series = _series_url.strip('/').split('/')[-1]
        _series_logo_path = seriesresult.find('img')['src']
        _series_event = seriesresult.find('div',{'class':'clubListTitle'}).text
        #print(_series_url,_series_logo_path, _series, _series_event )
        _data.append({'_series_url':_series_url,
                      '_series_logo_path':_series_logo_path,
                      '_series':_series,
                      '_series_event':_series_event})
        
    return pd.DataFrame( _data )
    
get_TSL_series()
```

## Get Series Pages

Get a list of links for each event in a series.

```python
def get_TSL_series_events(series='toca', year = YEAR ):
    
    series_url='http://www.tsl-timing.com/Results/{}/{}'.format(series, year)
    
    seriespage=requests.get(series_url)
    seriessoup=BeautifulSoup(seriespage.content)

    seriesevents=seriessoup.find('div',{'id':'races'}).findAll('a')

    _data = []
    
    for seriesevent in seriesevents:
        _event_url = seriesevent['href']
        _event_txt = seriesevent.find('div',{'class':'clubEventText'}).text

        _event_txt_parts = _event_txt.strip('\n').split('\n')
        _event_date = _event_txt_parts[0]
        _event_name = _event_txt_parts[1]

        #print(_event_txt_parts)
        _data.append( {'_event_url':_event_url,
                       '_event_date':_event_date,
                       '_event_name':_event_name } )
        
    return pd.DataFrame( _data )

get_TSL_series_events('toca')
```

### Get Event PDFs

Download PDFs relating to a particular event.

```python
eventpage=requests.get(event_url)
eventsoup=BeautifulSoup(eventpage.content)
```

```python
#check that event data is available
data_available = False if eventsoup.find("h3", string="Event data available soon") else True
```

```python
event_map_url = eventsoup.find('img',{'class':'eventMapImage'})['src']
event_map_url
```

```python
events=eventsoup.findAll('div',{'class':'championshipDiv'})
```

```python
p = '{}/{}/{}'.format(download_dir_base,series,year)
```

```python
if not os.path.exists(p):
    os.makedirs(p)

download=True

for event in events:
    championship_name = event.find('h3').text
    championship_url = event.find('a')['href']
    if download:
        print('Downloading: {} [{}]'.format(championship_name, championship_url))
        if championship_url.endswith('.pdf'):
            cmd = 'curl -o "{fp}" {url}'.format(url='{}{}'.format(domain,championship_url),fp='{}/{}.pdf'.format(p,championship_name))
            os.system(cmd)
        print('Files downloaded to: {}'.format(p))
```

Put all that together...

```python


def get_TSL_event_data(event_id = 191403, download = False, dirpath='results'):
    
    event_url='http://www.tsl-timing.com/event/{}'.format(event_id)
    
    eventpage=requests.get(event_url)
    eventsoup=BeautifulSoup(eventpage.content)
    
    data_available = False if eventsoup.find("h3", string="Event data available soon") else True
    
    _data=[]
    
    if data_available:
        events=eventsoup.findAll('div',{'class':'championshipDiv'})
        
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        for event in events:
            championship_name = event.find('h3').text
            championship_url = event.find('a')['href']
            championship_stub = championship_url.split('/')[-1].split('.')[0].replace(str(event_id),'')
            _data.append({'championship_name':championship_name,
                          'championship_url':championship_url,
                          'championship_stub': championship_stub})
            
            if download:
                print('Downloading: {} [{}]'.format(championship_name, championship_url))
                if championship_url.endswith('.pdf'):
                    cmd = 'curl -o "{fp}" {url}'.format(url='{}{}'.format(domain,championship_url),
                                                        fp='{}/{}.pdf'.format(dirpath,championship_name))
                    os.system(cmd)
        
        if download:
            print('Files downloaded to: {}'.format(dirpath))
        
    return pd.DataFrame( _data )

#p = '{}/{}/{}'.format(download_dir_base,series,year)
#get_TSL_event_data(dirpath = p)
get_TSL_event_data()

#Looks like we can pull out further srubs from end of PDF filename?
```

```python
!ls ./toca/2019
```

```python
#https://www.tsl-timing.com/event/191363
get_TSL_event_data(191363, True)
```

```python
!ls results
```

## Alternative PDF Grabber

The PDF grabber will download copies of all timing sheet booklets for the current season.

Explore alternative variant using `requests-html`.

```python
#!pip3 install requests-html
```

```python
listing_url='http://www.tsl-timing.com/Results/toca/'

#scrape races tab
#go to event page
#for each series:
## grab name
## select appropriate series folder name
## create folder if not exist
## grab "View PDF Book" URL
## download booklet to appropriate series folder with event name as part of URL
```

```python
import requests
from bs4 import BeautifulSoup

html = requests.get(listing_url).text

soup = BeautifulSoup(html)

div = soup.find('div', attrs={'id' : 'races'})

stub='http://www.tsl-timing.com{}'


from requests_html import HTMLSession
session = HTMLSession()


!mkdir -p 2019

for a in div.findAll('a'):
    event_url = stub.format(a['href'])
    r = session.get(event_url)

    xp = r.html.xpath('//*[@id="contentContainer"]/section/h3')
    if xp and xp[0].text=='Event data available soon':
        break
    
    #the pts PDFs are champtionship points files
    links = [l for l in r.html.links if l.endswith('.pdf') and 'pts' not in l]
    #Grab PDFs
    for l in links:
        pdf_url=stub.format(l)
        fn = l.split('/')[-1]
        #!echo $pdf_url
        !curl -o 2019/{fn} {pdf_url}
```

```python
!ls 2019
```

The filenames are coded according to datestamp and a letter code identifying the series.

```python
# See the R notebook - tabula scraper
```

```python

```

```python

```

```python

```

```python

```
