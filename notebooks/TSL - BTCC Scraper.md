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

# TSL - BTCC Timing Sheet Scraper

A notebook for scraping TSL timing sheet data for BTCC races and the associated support races.

A separate scraper is used for each type of timing sheet.

TO DO:

- automate the detection and selection of scrapers from the timing sheet document type;
- save *pandas* dataframe versions of the data as (unindexed) CSV files;
- automate the generation of file names and save dataframes from the document type;
- automate the scrapes to take a timing results booklet PDF and save one or more tables using CSV format for each document it contains.


## PDF Grabber

Grab PDFs from TSL site.

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
            
            _data.append({'championship_name':championship_name,
                          'championship_url':championship_url})
            
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

```python

```

```python
#BELOW IS OLD AND PROBABLY DEPRECATED
```

## PDF Scrapers

```python
import os
fn='161303msf'
fn='ginettaJnrSnetterton2015'
fn='161303trg'
fn='BTCC/2016/TOCA%2F2016%2F162403trg'
fn='/Users/ajh59/Downloads/171503trg'
cmd = 'pdftohtml -xml -nodrm -zoom 1.5 -enc UTF-8 -noframes %s "%s" "%s"' % (
        '',fn+'.pdf', os.path.splitext('BTCC/2017/'+fn.split('/')[-1]+'.xml')[0])
# can't turn off output, so throw away even stderr yeuch
cmd + " >/dev/null 2>&1"
os.system(cmd)
```

```python
fn.split('/')[:-1]
```

```python
import lxml.etree

xmldata = open('BTCC/2017/{}.xml'.format(fn.split('/')[-1]),'r').read()
root = lxml.etree.fromstring(xmldata)
pages = list(root)
```

```python
import pandas as pd
def flatten(el):           
    result = [ (el.text or "") ]
    for sel in el:
        result.append(flatten(sel))
        result.append(sel.tail or "")
    return "".join(result)

def ish(val1,val2,tolerance=3):
    if abs(val1-val2)<=tolerance:
        return True
    return False
```

```python
def rowstarter(page):
    rownum=0
    for startrow in page:
        if flatten(startrow).strip()!='':
            break
        else: rownum=rownum+1
    return rownum

def pageinfo(page):
    rowstart=rowstarter(page)
    event=flatten(page[rowstart]).strip()
    doctype=flatten(page[rowstart+1]).strip()
    return rowstart,event,doctype
```

```python
#First page is a cover page
#Second page is a circuit map

#Last page of each session are weather conditions
i=0
for page in pages:
    print(i,pageinfo(page))
    i=i+1
```

```python

```

```python

```

```python
import datetime
#http://tgs.github.io/nptime/
from nptime import nptime

def nptimify(t):
    tt=t.split(':')
    if len(tt)==3:
        h=int(tt[0])
        m=int(tt[1])
        if len(tt[2].split('.'))==2:
            s=int(tt[2].split('.')[0])
            ms=int(tt[2].split('.')[1])
        else:
            s=int(t.split(':')[2])
            ms=0
    elif len(tt)==2:
        h=int(tt[0])
        m=int(tt[1])
        if len(tt[2].split('.'))==2:
            s=int(tt[2].split('.')[0])
            ms=int(tt[2].split('.')[1])
        else:
            s=int(t.split(':')[2])
            ms=0
    return nptime(h, m, s, ms)

def npreltimify(t,earliest="0:0:0"):
    return nptimify(t) - nptimify(earliest)

def nprebase(delta,earliest="0:0:0"):
    return delta + nptimify(earliest)

#def nprebaseElapsed()

#Preferred time format
def formatTime(t):
    return float("%.3f" % t)
# Accept times in the form of hh:mm:ss.ss or mm:ss.ss
# Return the equivalent number of seconds
def getTime(ts):
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
        tm=float(t[0])
    return float(formatTime(tm))
```

## Lap Chart Scraper

```python
import pandas as pd
```

```python
def pageview(pages,page):
    for el in pages[page]:
        print( el.attrib['left'], el.attrib['top'],flatten(el))
```

```python
pageview(pages,65) #5
```

```python
def columnSpotter(pages,counts=None,raw=None,omittop=0,omitbottom=9999):
    if counts is None: counts={}
    if raw is None: raw=[]
    for page in pages:
        for el in page:
            if 'top' not in el.attrib: continue
            top=int(el.attrib['top'])
            if top<omittop or top>omitbottom: continue 
            left=el.attrib['left']
            raw.append(int(left))
            if left in counts:
                counts[left]=counts[left]+1
            else:
                counts[left]=1
    return counts,raw
```

```python
%matplotlib inline
import matplotlib.pyplot as plt
def columnCharter(cc):
    ccd=pd.DataFrame.from_dict(cc,orient='index').reset_index()
    ccd.columns=['left','count']
    ccd['left']=ccd['left'].astype(int)
    ccd.sort('left', inplace=True)
    #ccd.plot('left','count',kind='bar')
    plt.bar(ccd['left'], ccd['count'])
    return

#counts,raw=columnSpotter(pages[28:30])
columnCharter(columnSpotter(pages[4:13],omittop=220,omitbottom=1000)[0])
```

```python
def lapScraper(pages, pagenums):
    laps={}
    for p in pagenums:
        page=pages[p]
        print('---------new page----------')
        event=flatten(page[0]).strip()
        document=flatten(page[1]).strip()
        print(event,document)
        rowval=999
        row=[]
        header=0
        newcol=True
        newrow=False
        for el in page[2:-7]:
            txt=flatten(el).strip()
            #print( el.attrib['left'], el.attrib['top'],txt)
            if 'top' not in el.attrib:continue
            top=int(el.attrib['top'])
            left=int(el.attrib['left'])
            if header>0:
                if header==4:
                    lap=txt
                    laps[lap]=[]
                if header==1:
                    newrow=True
                header=header-1  
            elif newrow or ish(rowval,top):
                newrow=False
                if txt!='D':
                    row.append(txt)
            elif rowval<top:
                laps[lap].append(row)
                newrow=True
                row=[txt]
            elif rowval>top:
                header=3
                if row!=[] and lap in laps:
                    laps[lap].append(row)
                    row=[]
                lap=txt
                laps[lap]=[]
            rowval=top
        laps[lap].append(row)
    return event, document,laps
```

```python
range(65,69)
```

```python
l_e,l_d,laps=lapScraper(pages, range(65,69))#4,13
laps
```

```python
#We really should process the data properly as we scrape it
#As it is, hack it...
def lapChartHacker(laps):
    tidylaps={}
    for lap in laps:
        tidylaps[lap]=[]
        for row in laps[lap]:
            #print(row,len(row))
            if len(row)==2:
                tidylaps[lap].append({'num':row[0],
                                      'rawbehind':0, 'behind':0,
                                      'rawtime':row[1], 'laptime':getTime(row[1]),
                                      'pit':False})
            elif len(row)==4:
                tidylaps[lap].append({'num':row[0],
                                      'rawbehind':row[1],'behind':getTime(row[1]),
                                      'rawtime':row[3], 'laptime':getTime(row[3]),
                                      'pit':True})
            else:
                tidylaps[lap].append({'num':row[0],
                                      'rawbehind':row[1],'behind':getTime(row[1]),
                                      'rawtime':row[2], 'laptime':getTime(row[2]),
                                      'pit':False})
    return tidylaps
```

```python
ll=lapChartHacker(laps)
#ll
```

```python
def lapOutputter(ll):
    tmp=[]
    for lap in ll:
        for res in ll[lap]:
            res['lap']=int(lap.replace('LAP ',''))
            tmp.append(res)
    #tmp
    df=pd.DataFrame.from_dict(tmp)
    return df
```

```python
df_laps=lapOutputter(ll)
df_laps.sort_values(by=['num','lap'])
```

## Grid Scraper

```python
pageview(pages,51)
```

```python
def gridScraper(pages,pagenum):
    print('---------new grid scrape----------')
    page=pages[pagenum]

    rownum=rowstarter(page)
    
    event=flatten(page[rownum]).strip()
    doctype=flatten(page[rownum+1]).strip()
    print(event,doctype)
    if not "GRID" in doctype: return None
    
    rowval=999
    row=[]
    header=0
    newcol=True
    newrow=False
    grid=[]
    gridpos=[]
    gridrow=None
    rowstart=rownum+3
    for el in page[rowstart:]:
        txt=flatten(el).strip()
        #print(txt)
        #print( el.attrib['left'], el.attrib['top'],txt)
        top=int(el.attrib['top'])
        left=int(el.attrib['left'])
        
        if txt.startswith('ROW'):
            pass
        elif len(gridpos)==2 and '.' not in txt : #no time
            gridpos.append('')
            gridpos.append(txt)
        else:
            gridpos.append(txt)
        if len(gridpos)==4:
            grid.append(gridpos)
            #print(gridpos)
            gridpos=[]
        if txt=='Pole': break
    grid.reverse()
    return event,doctype,grid
        

```

```python
g_e,g_d,g=gridScraper(pages,51)
g
```

```python
df_grid=pd.DataFrame(g,columns=['pos','driverName','rawtime','num'])
df_grid.head()
```

```python
df_grid['grid_laptime']=df_grid['rawtime'].apply(getTime)
df_grid['pos']=df_grid['pos'].astype(int)
df_grid=df_grid.rename(columns={'pos':'grid','rawtime':'grid_rawtime'})
df_grid=df_grid.sort_values(['grid','grid_laptime'])
df_grid.reset_index(drop=True,inplace=True)
df_grid
```

## Annotated Table

```python
df_laps=df_laps.merge(df_grid[['num','driverName']])
df_laps.head()
```

```python
if g_e!=l_e: print('Event mismatch?')
elif g_d.split('-')[0].strip()!=l_d.split('-')[0].strip(): print('Round mismatch')
else:
    fn='btcc_{}.csv'.format(l_d.replace(' ',''))
    print('Saving *{} - {}* as `{}`'.format(l_e,l_d,fn))
    df_laps.to_csv(fn,index=False)
    
    fn='btcc_{}.csv'.format('-'.join([g_d.split('-')[0],g_d.split('-')[1].split()[0]]).replace(' ',''))
    print('Saving *{} - {}* as `{}`'.format(g_e,g_d,fn))
    df_grid.to_csv(fn,index=False)
```

```python

```

## Classification Scraper

```python
pageview(pages,72)
```

```python
columnCharter(columnSpotter(pages[72:73],omittop=220,omitbottom=1000)[0])
```

```python
#via https://gist.github.com/drewda/1299198
def getJenksBreaks( dataList, numClass ):
    dataList.sort()
    mat1 = []
    for i in range(0,len(dataList)+1):
        temp = []
        for j in range(0,numClass+1):
            temp.append(0)
        mat1.append(temp)
    
    mat2 = []
    for i in range(0,len(dataList)+1):
        temp = []
        for j in range(0,numClass+1):
            temp.append(0)
        mat2.append(temp)
    for i in range(1,numClass+1):
        mat1[1][i] = 1
        mat2[1][i] = 0
        for j in range(2,len(dataList)+1):
            mat2[j][i] = float('inf')
    v = 0.0
    for l in range(2,len(dataList)+1):
        s1 = 0.0
        s2 = 0.0
        w = 0.0
        for m in range(1,l+1):
            i3 = l - m + 1
            val = float(dataList[i3-1])
            s2 += val * val
            s1 += val
            w += 1
            v = s2 - (s1 * s1) / w
            i4 = i3 - 1
            if i4 != 0:
                for j in range(2,numClass+1):
                    if mat2[l][j] >= (v + mat2[i4][j - 1]):
                        mat1[l][j] = i3
                        mat2[l][j] = v + mat2[i4][j - 1]
        mat1[l][1] = 1
        mat2[l][1] = v

    k = len(dataList)
    kclass = []
    for i in range(0,numClass+1):
        kclass.append(0)
    kclass[numClass] = float(dataList[len(dataList) - 1])
    countNum = numClass
    while countNum >= 2:#print "rank = " + str(mat1[k][countNum])
        id = int((mat1[k][countNum]) - 2)
        #print "val = " + str(dataList[id])
        kclass[countNum - 1] = dataList[id]
        k = int((mat1[k][countNum] - 1))
        countNum -= 1
    return kclass
  
def getGVF( dataList, numClass ):
    """
    The Goodness of Variance Fit (GVF) is found by taking the 
    difference between the squared deviations
    from the array mean (SDAM) and the squared deviations from the 
    class means (SDCM), and dividing by the SDAM
    """
    breaks = getJenksBreaks(dataList, numClass)
    dataList.sort()
    listMean = sum(dataList)/len(dataList)
    print listMean
    SDAM = 0.0
    for i in range(0,len(dataList)):
        sqDev = (dataList[i] - listMean)**2
        SDAM += sqDev
    SDCM = 0.0
    for i in range(0,numClass):
        if breaks[i] == 0:
            classStart = 0
        else:
            classStart = dataList.index(breaks[i])
            classStart += 1
        
        classEnd = dataList.index(breaks[i+1])
        classList = dataList[classStart:classEnd+1]
        classMean = sum(classList)/len(classList)
        print classMean
        preSDCM = 0.0
        for j in range(0,len(classList)):
            sqDev2 = (classList[j] - classMean)**2
            preSDCM += sqDev2
        SDCM += preSDCM
    return (SDAM - SDCM)/SDAM
  
# written by Drew
# used after running getJenksBreaks()
def classify(value, breaks):
    for i in range(1, len(breaks)):
        if value < breaks[i]:
              return i
    return len(breaks) - 1
```

```python
raw
```

```python
columnCharter(columnSpotter(pages[72:73],omittop=220,omitbottom=1000)[0])
```

```python
raw=columnSpotter(pages[72:73],omittop=220,omitbottom=1000)[1]
jb=getJenksBreaks( raw, 13 )
jb
```

```python
def getColBand_classification(left):
    band=None
    if left<45:
        band='pos'
    elif left< 75:
        band='no'
    elif left< 100:
        band='cl'
    elif left< 150:
        band='pic'
    elif left< 200:
        band='driver'
    elif left<  410:
        band='car'        
    elif left< 570:
        band='laps'
    elif left< 605 :
        band='time' 
    elif left< 670:
        band='gap'
    elif left< 720:
        band='diff'
    elif left< 760:
        band='mph' 
    elif left< 800 :
        band='best'
    else:
        band='on' 
    return band

def getColBand_classification(left):
    band=None
    if left<45:
        band='pos'
    elif left< 75:
        band='no'
    elif left< 99:
        band='cl'
    elif left< 145:
        band='pic'
    elif left< 158:
        band='driver'
    elif left<  406:
        band='car'        
    elif left< 569:
        band='laps'
    elif left< 603 :
        band='time' 
    elif left< 668:
        band='gap'
    elif left< 719:
        band='diff'
    elif left< 758:
        band='mph' 
    elif left< 798 :
        band='best'
    else:
        band='on' 
    return band

def classificationScraper(pages,pagenum):
    print('---------new classification scrape----------')
    
    page=pages[pagenum]

    rownum=rowstarter(page)
    
    event=page[rownum]
    doctype=page[rownum+1]
    rowstart=rownum+2
    if not "CLASSIFICATION" in flatten(doctype).strip(): return None
    
    headertop=int(page[rowstart].attrib['top'])
    
    #Get headers
    headers={}
    for el in page[rowstart:]:
        top=int(el.attrib['top'])
        if ish(headertop,top) is not True: break
        txt=flatten(el).strip()
        headers[txt]={'left':int(el.attrib['left'])}
        rowstart=rowstart+1
    
    rowdata={}
    rows=[]
    #drows=[]
    #drowdata={}
    curr_rowtop=int(page[rowstart].attrib['top'])
    for el in page[rowstart:]:
        rowtop=int(el.attrib['top'])
        currleft=int(el.attrib['left'])
        txt=flatten(el).strip()

        if 'NOT CLASSIFIED' in txt: continue
        if 'FASTEST LAP' in txt: break
            
        if ish(rowtop,curr_rowtop,10) is not True:
            #new row
            #print('new row')
            curr_rowtop=rowtop
            rows.append(rowdata)
            rowdata={}
            
            #drows.append(drowdata)
            #drowdata={}
            
        #rowdata.append(txt)
        rowdata[getColBand_classification(currleft)]=txt
        
        #for key in headers:
        #    if ish(headers[key]['left'],int(el.attrib['left'])):
        #        drowdata[key]=txt
        #        break
    
    return headers,rows#,drows
```

```python
cc,dd=classificationScraper(pages,72)
cc, dd
```

```python
pd.DataFrame(dd)[['pos','no','cl','pic','driver','car','laps','time','gap','diff','mph','best','on']]
```

## Best Speeds Scraper



```python
def getHeaders(page,rowstart):
    headertop=int(page[rowstart].attrib['top'])
    
    #Get headers
    headers={}
    for el in page[rowstart:]:
        top=int(el.attrib['top'])
        print(top)
        if ish(headertop,top) is not True: break
        txt=flatten(el).strip()
        print(txt)
        headers[txt]={'left':int(el.attrib['left'])}
        rowstart=rowstart+1
    return headers,rowstart
```

```python
def bestSpeedsScraper(pages,pagenum):
    print('---------new best speeds scrape----------')
    
    page=pages[pagenum]
    rowstart,event,doctype = pageinfo(page)
    #headers,rowstart=getHeaders(page,rowstart)
    
    #Get as far as FINISH LINE
    for el in page[rowstart:]:
        txt=flatten(el).strip()
        rowstart=rowstart+1
        if txt=='1':
            break
    for el in page[rowstart:]:
        if int(el.attrib['left'])>50:
            break
        rowstart=rowstart+1
    
    bests={"inter1":[],"inter2":[],"finish":[]}
    rowdata=[]
    currleft=int(page[rowstart].attrib['left'])
    currtop=int(page[rowstart].attrib['top'])
    trapnum=0
    traps=["inter1","inter2","finish"]
    print('currtop',currtop)
    for el in page[rowstart:]:
        left=int(el.attrib['left'])
        top=int(el.attrib['top'])
        if top>currtop+100:break
        if left<currleft:
            print('top',top,currtop,left,trapnum,rowdata)
            bests[traps[trapnum]].append(rowdata)
            rowdata=[]
        elif (currtop-top)>10:
            bests[traps[trapnum]].append(rowdata)
            trapnum=trapnum+1
            rowdata=[]
        currleft=left
        currtop=top
        txt=flatten(el).strip()
        rowdata.append(txt)
        #if ish(headertop,top) is not True: break
        #print(txt)
        
    return bests #event, doctype,headers
    
```

```python
bs=bestSpeedsScraper(pages,26)
bs
```

```python
pd.DataFrame(bs['inter1'],columns=['num','name','mph'])
```

```python
pd.DataFrame(bs['inter2'],columns=['num','name','mph'])
```

```python
pd.DataFrame(bs['finish'],columns=['num','name','mph'])
```

## Best Sectors Scraper

```python
#http://stackoverflow.com/a/5389547/454773
from itertools import izip

def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)

```

```python
def bestSectorsScraper(pages,pagenum):
    print('---------new best speeds scrape----------')
    
    page=pages[pagenum]
    rowstart,event,doctype = pageinfo(page)
    #headers,rowstart=getHeaders(page,rowstart)
    
    #Get as far as FINISH LINE
    for el in page[rowstart:]:
        txt=flatten(el).strip()
        rowstart=rowstart+1
        if txt=='1':
            break
    for el in page[rowstart:]:
        if int(el.attrib['left'])>50:
            break
        rowstart=rowstart+1
    
    bests={"sector1":[],"sector2":[],"sector3":[],"ideal":[]}
    rowdata=[]
    currleft=int(page[rowstart].attrib['left'])
    currtop=int(page[rowstart].attrib['top'])
    trapnum=0
    traps=["sector1","sector2","sector3","ideal"]
    skipper=False
    for el in page[rowstart:]:
        left=int(el.attrib['left'])
        top=int(el.attrib['top'])
        if top>currtop+100:break
        if left<currleft:
            #print('top',top,currtop,left,trapnum,rowdata)
            if rowdata!=[]: bests[traps[trapnum]].append(rowdata)
            rowdata=[]
        elif (currtop-top)>10:
            if rowdata!=[]: bests[traps[trapnum]].append(rowdata)
            trapnum=trapnum+1
            rowdata=[]
        currleft=left
        currtop=top
        txt=flatten(el).strip()
        #Cop out for now
        if skipper or "PERFECT LAP" in txt:
            skipper=not(skipper)
            continue
        #print(txt)
        if len(rowdata)>0:
            rowdata.append(txt)
        else:
            rowdata.append(txt)
            #print(txt)
            if traps[trapnum]!='ideal':
                m=re.match(r"(?P<num>\d+) +(?P<name>.*)$", txt)
                rowdata.append(m.group('num'))
                rowdata.append(m.group('name'))
        #if ish(headertop,top) is not True: break
        #print(txt)
        
    #getting end effect on last perfect lap?
    #fudge it here...
    bests[traps[trapnum]].append(rowdata)
    bests2={'ideal':[]}
    for key in ['sector1','sector2','sector3']: bests2[key]=bests[key]
    for (a,b) in pairwise(bests['ideal']):
        m=re.match(r"(?P<num>\d+) +(?P<name>.*)$", a[0])
        bests2['ideal'].append(a+[m.group('num'),m.group('name')]+b)
    return bests2 #event, doctype,headers
    
```

```python
bb=bestSectorsScraper(pages,27)
bb
```

```python
ideal=pd.DataFrame(bb['ideal'],columns=['raw','ideal','num','name','pos','best','diff'])
```

```python
s1=pd.DataFrame(bb['sector1'],columns=['raw','num','name','s1time'])
```

```python
s2=pd.DataFrame(bb['sector1'],columns=['raw','num','name','s2time'])
```

```python
s3=pd.DataFrame(bb['sector1'],columns=['raw','num','name','s3time'])
```

```python
s=pd.merge(s1,s2,on=['raw','num','name'])
s=pd.merge(s,s3,on=['raw','num','name'])
s=pd.merge(s,ideal,on=['raw','num','name'])
s
```

## Sector Analysis

```python
pageview(pages,93)
```

```python
import re

def getColBand_sectoranalysis(left):
    band=None
    if left< 60:
        band='lap'
    elif left< 120:
        band='s1time'
    elif left< 190:
        band='s1speed'
    elif left< 275:
        band='s2time'
    elif left< 340 :
        band='s2speed'        
    elif left< 415:
        band='s3time'
    elif left< 510 :
        band='s3speed' 
    elif left< 550:
        band='laptime'
    elif left< 600:
        band='flag'
    elif left< 690:
        band='mph' 
    elif left< 725:
        band='diff'
    else:
        band='timeofday' 
    return band

def bestSectorsScraper(pages,pagenums):
    sectorAnalysis=[]
    recent=[None,None,None]
    record={'dname':None,'dclass':None,'dnum':None,'tname':None,'lapdata':[],
            'meta':{}}
    meta={}
    lapmarker = re.compile(r"\d+ +-")
    
    #The lapping flag says whether or not we are logging lap data
    lapping=False
    
    laptmp={}
    print('---------new sector analysis scrape----------')
    
    for p in pagenums:
        print("---new page---")
        page=pages[p]
        rowstart,event,doctype = pageinfo(page)
        #Get as far as first analysis table
        oldtop=int(page[rowstart].attrib['top'])

        for el in page[rowstart:]:
            txt=flatten(el).strip()
            #print('..',txt)
            rowstart=rowstart+1
            if "Difference To Personal Best Lap" in txt:
                break
        #print('-----',rowstart,laptmp)
        for el in page[rowstart:]:
            currleft=int(el.attrib['left'])
            currtop=int(el.attrib['top'])
            
            newline=ish(oldtop,currtop)
            if newline is not True: lapping = False
            txt=flatten(el).strip()
            if txt.startswith("Results can"): break
            #print('||',txt)
            #lapmarkers
            if txt=='LAP':
                if record['meta']!={}:
                    record['lapdata'].append(laptmp)
                    sectorAnalysis.append(record)
                record={'tname':None,'meta':{}}
                record['dname']=recent[1]
                record['dclass']=recent[2]
                record['dnum']=recent[0]
                record['lapdata']=[]
                laptmp={}
                lapping=False
                #print(dname,dclass,dnum,meta)
            elif txt=="MPH":
                record['tname']=recent[2]
            if " : " in txt:
                md=txt.split(' : ')
                record['meta'][md[0].strip()]=md[1].strip()
                
            if lapmarker.match(txt):
                #newlap
                lapping=True
                if laptmp!={}:
                    record['lapdata'].append(laptmp)
                    laptmp={}

            #Lap data needs to be captured in a much more structured way
            #Define column bands and associate each stamp with a column
            #laptmp[getColBand(left)]=txt
            if lapping:
                #laptmp.append(txt)
                laptmp[getColBand_sectoranalysis(currleft)]=txt
            #print(currleft,currtop,txt)
            
            oldtop=currtop
            #Simple crude FIFO queue
            dummy=recent.pop(0)
            recent.append(txt)
    #End effects
    record['lapdata'].append(laptmp)
    sectorAnalysis.append(record)
    return sectorAnalysis
```

```python
bss=bestSectorsScraper(pages,range(93,94))
bss
```

```python
sl=[]
for r in bss:
    for l in r['lapdata']:
        ld={'num':r['dnum']}
        ld.update(l)
        sl.append(ld)
pd.DataFrame(sl)
```

## Position Chart

TO DO

```python

```
