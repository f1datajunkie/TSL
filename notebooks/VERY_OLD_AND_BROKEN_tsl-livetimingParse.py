import os,csv,sys

from pygooglechart import SimpleLineChart
from pygooglechart import Axis

from BeautifulSoup import BeautifulSoup

#------maybe dupe code
#Preferred time format
def formatTime(t):
	return float("%.3f" % t)
# Accept times in the form of hh:mm:ss.ss or mm:ss.ss
# Return the equivalent number of seconds
def getTime(ts):
	t=ts.strip()
	t=ts.split(':')
	if len(t)==3:
		tm=60*int(t[0])+60*int(t[1])+float(t[2])
	elif len(t)==2:
		tm=60*int(t[0])+float(t[1])
	else:
		tm=float(t[0])
	return formatTime(tm)
#-----
def sortedDictValues(adict):
    keys = adict.keys()
    keys.sort()
    return map(adict.get, keys)
    
    
chart = SimpleLineChart(200, 125, y_range=[0, 20])

linetimes=[]
outdat=[]

laplogger={}

firstpass=True

drivers=[]
race='btcc' #renaultCLio,formulaRenault,ginettaJnr,porsche,btcc
dir='2011testbtccoulton/'+race

lapPos=[]
#record: num,name,

lapDat={'laps':{},'times':{},'pos':{},'gap':{}, 'timesInS':{},'elapsedTimes':{}}
driverData={}
count=0
maxlaps=0
finished=0
leaderElapsedTime=[]
for fn in os.listdir(dir):
 #fn='porsche-4.txt'
 if not fn.startswith('.'):
  fn=dir+'/'+fn

  f=open(fn)
  html=f.read()
  f.close()
  soup=BeautifulSoup(html)
  
  linedat={}
  
  status = soup.find('span',id="lblSessionStatus")
  print fn,status.contents[0]
  if status.contents[0]=="Waiting for Session Start":
  	continue
  if finished>3:
  	break
  if status.contents[0]=="Finished":
  	finished=finished+1
  table = soup.find('table', id="gridTimes")
  print "add data"
  rows=table.findChildren(['tr'])
  for row in rows:
    cells = row.findChildren('td')
    vals=row.findChildren('font')
    op=[]
    if len(cells)==9:
      for cell in cells:
        if cell.font:
          cell=cell.font.string
        else:
          cell=cell.string
        op.append(cell)
      pos,num,name,laps,timegap,diff,speed,bestlap,lastlap=op
      if timegap=="&nbsp;":
      	timegap=0
      if lastlap=="&nbsp;":
      	lastlap=0
      timeInS=getTime(str(lastlap))
      pos=int(pos)
      laps=int(laps)
      linedat[num]=op
      drivers.append(num)
      if laps>0:
        if laps>maxlaps:maxlaps=laps
        if num not in lapDat['laps']:
          driverData[num]=[{'name':name,'lap':laps,'time':lastlap,'pos':pos,'gap':timegap,"timeInS":timeInS,"elapsedTime":timeInS}]
          lapDat['laps'][num]=[laps]
          lapDat['times'][num]=[lastlap]
          lapDat['pos'][num]=[pos]
          lapDat['gap'][num]=[timegap]
          lapDat['timesInS'][num]=[timeInS]
          lapDat['elapsedTimes'][num]=[timeInS]
          if pos==1: leaderElapsedTime.append(timeInS)
        elif laps not in  lapDat['laps'][num]:
          elapsedTime=formatTime(lapDat['elapsedTimes'][num][-1]+getTime(lastlap))
          driverData[num].append({'name':name,'lap':laps,'time':lastlap,'pos':pos,'gap':timegap,"timeInS":getTime(lastlap),"elapsedTime":elapsedTime})
          lapDat['laps'][num].append(laps)
          lapDat['times'][num].append(lastlap)
          lapDat['pos'][num].append(pos)
          lapDat['gap'][num].append(timegap)
          lapDat['timesInS'][num].append(timeInS)
          lapDat['elapsedTimes'][num].append(elapsedTime)
          if pos==1: leaderElapsedTime.append(elapsedTime)
      #print pos,num,name,laps,timegap,diff,speed,bestlap,lastlap
  linetimes.append(linedat)

print 'driverData',driverData
writer = csv.writer(open(dir+"/../"+race+".gdf", "wb"))
writer.writerow(['nodedef>name VARCHAR','label VARCHAR','num VARCHAR','lap INT','pos INT',"laptime DOUBLE","elapsedTime DOUBLE"])
for num in driverData:
  writer.writerow([num+'_0',driverData[num][0]['name'],num,'-1',str(driverData[num][0]['pos']),'0','0'])
  for dd in driverData[num]:
    writer.writerow([num+'_'+str(dd['lap']),dd['name'],num,str(dd['lap']),str(dd['pos']),str(dd['timeInS']),str(dd['elapsedTime'])])
writer.writerow(['edgedef>oldlap VARCHAR','newlap VARCHAR'])
for num in driverData:
  for dd in driverData[num]:
    if dd['lap']<maxlaps and len(driverData[num])>dd['lap']:
      writer.writerow([num+'_'+str(dd['lap']),num+'_'+str(dd['lap']+1)])

writer = csv.writer(open(dir+"/../"+race+".csv", "wb"))
writer.writerow(['name','num','lap','pos','laptime',"elapsedTime","timeToLeader"])
for num in driverData:
  for dd in driverData[num]:
    writer.writerow([dd['name'],num,str(dd['lap']),str(dd['pos']),str(dd['timeInS']),str(dd['elapsedTime']),str(formatTime(leaderElapsedTime[dd['lap']-1]-dd['elapsedTime']))])
