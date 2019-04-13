---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.0'
      jupytext_version: 0.8.6
  kernelspec:
    display_name: R
    language: R
    name: ir
---

# TSL PDF Scraper

Scraper for extractng results and timing data from TSL results documents.


Part of a set of tools that will:

- automate the detection and selection of scrapers from the timing sheet document type;
- save *pandas* dataframe versions of the data as (unindexed) CSV files;
- automate the generation of file names and save dataframes from the document type;
- automate the scrapes to take a timing results booklet PDF and save one or more tables using CSV format for each document it contains.


This initial scraper is based primarily on Britcar timing sheets, although examples are also given around some BTCC timing sheets.

Hopefully, the timing sheets are consistent. If not, this scraper will be nothing more than a bespoke curiousity, although it may provide colues to a more robust scraper.

If nothing else, this should work as a walkthrough of how to scrape tables from a variety of PDF documents.

Where possible, data will be scraped into database tables that use a similar structure to the tables used in the `ergast` motor racing database.

The Python Tabula wrapper doesn't appear to work for me... so this notebook will use the *R* `tabulizr` package.


## TSL Timing Sheets

TSL publish (and archive) a range of timing sheet documents for the race series they provide timing services for.

A range of sheets are bundled in a "PDF book" for each race series. The scraper described here is designed to scrape data from the sheets contained within a PDF book into a simple SQLite database.

The range of timing sheets published by TSL for an event may include some or all of the following sheets for practice, qualifying and race:

- CLASSIFICATION
- 2ND FASTEST CLASSIFICATION
- SECTOR ANALYSIS
- BEST SPEEDS
- BEST SECTORS
- WEATHER CONDITIONS
- STATISTICS
- GRID
- LAP CHART
- POSITION CHART


## Making a Start

The `tabulizer` package provides an R wrapper around the [tabulapdf/tabula-java](https://github.com/tabulapdf/tabula-java) service that underpins the browser based [*Tabula*](https://tabula.technology/) PDF table scraping application.

```R
#install.packages("tabulizer")
```

```R
#sudo R CMD javareconf
library("tabulizer")
```

```R
PDF <- "2019/191403cli.pdf"
```

```R
get_page_dims(PDF, pages=1)
```

```R
#locate_areas("2019/191403cli.pdf", pages=1)
```

## Extract Page Info

We can extract document metadata from the PDFs using the `extract_metadata()` function:

```R
extract_metadata(PDF)
```

We can also extract text from a page using the `extract_text()` function:

```R
t <- extract_text(PDF, page=1)

#Split the separate lines into a list
strsplit( t , '\n')[[1]]
```

```R
series <- strsplit( t , '\n')[[1]][1]
series
```

Let's try another one...

```R
extract_text('results/Dunlop Endurance Championship.pdf', page=1)
```

Okay, so maybe we need to do a bit more cleaning...

Let's work on the assumption that the first none copyright related notice is the series...

```R
#install.packages("rlist")

library(rlist)
library(magrittr)

#library(stringi)

library(stringr)

#Clean whitespace
#THe list.map function applies the split to each item in the list
items <- list.map( strsplit( extract_text('results/Dunlop Endurance Championship.pdf', page=1)[[1]], '\n') , trimws(.) )

#Remove empty list items
items <- list.map( items , stri_remove_empty(.) )[[1]]

#Remove the TSL boilerplate items
items[! items %in% c('Results Provided by Timing Solutions Ltd', 'www.tsl-timing.com')]

```

```R
get_TSL_series <- function(PDF){
    t <- extract_text(PDF, page=1)
    
    items <- list.map( strsplit( t[[1]], '\n') , trimws(.) )

    items <- list.map( items , stri_remove_empty(.) )[[1]]

    items <- items[! items %in% c('Results Provided by Timing Solutions Ltd', 'www.tsl-timing.com')]

    items[1]
}

get_TSL_series(PDF)

```

Let's start to think about how we might manage the data. Use data frames for now, but with a view to casting dataframes as SQLite tables.

```R
series_df <- data.frame(series, PDF )
series_df
```

```R
library(DBI)

db <- dbConnect(RSQLite::SQLite(), "testdb.sqlite")
```

```R
#dbRemoveTable(db, "series")
dbWriteTable(db, "series", series_df) #append=
dbGetQuery(db, 'SELECT * FROM series LIMIT 5')
```

We can use the `area=` parameter to specify `(top, left, bottom, right)` area co-ordinates within which `tabulizer` should look for the table information.


For example, the page footer may contain useful information, such as the session time, weather and track condition.

```R
#Page footer
t = extract_text("2019/191403cli.pdf", pages = 9, area = list(c(760, 0, 1000, 600)))
cat(t)
```

How about the page header?

```R
#Page header
t = extract_text(PDF, pages = 13, area = list(c(0, 0, 120, 600)))
cat(t)
```

Where the header is split over two lines, we can can split the string to access the separate components:

```R
paste(strsplit(t, '\n')[[1]][1], '*and*', strsplit(t, '\n')[[1]][2])
```

```R
#What happens with the empy second item?
t = extract_text(PDF, pages = 2, area = list(c(0, 0, 120, 600)))
paste(strsplit(t, '\n')[[1]][1], '*and*', strsplit(t, '\n')[[1]][2])
```

We can then grab the headings for each page. 

```R
for (page in 1:extract_metadata(PDF)$pages){
    cat( paste('Page', page, '-',
               extract_text(PDF, pages = page, area = list(c(0, 0, 120, 600))), '\n' ))
}
```

We can also get information about how many pages into a group of pages a given page is from the footer:

```R
getPageMofN <- function(PDF, pages=NULL){
    pages = str_match(extract_text(PDF, pages = pages, area = list(c(810, 0, 1000, 600))),
                  '.*Page ([0-9]+ of [0-9]*) *')[,2]

    ifelse(is.na(pages), "1 of 1", pages)
    }

getPageMofN(PDF)
```

Let's see if we can make a lookup table / dataframe for the sessions:

```R
get_TSL_PDF_pages <- function(PDF){

    #series <- get_TSL_series(PDF)
    
    details<-data.frame()
    for (page in 1:extract_metadata(PDF)$pages){

        #Extract info from the top of the page
        t <- extract_text(PDF, pages = page, area = list(c(0, 0, 120, 600)))

        #Parse info
        series <- trimws(strsplit(t, '\n')[[1]][1])
        sessiondetail <- strsplit(t, '\n')[[1]][2]
        sessiondetails <- rev(strsplit(sessiondetail, '-')[[1]])
        report <- trimws(sessiondetails[1])
        event <- trimws(sessiondetails[2])
        if (length(sessiondetails)==3){
            session <- trimws(sessiondetails[3])
        } else {session <- 'RACE'}

        #Create dataframe
        details <- rbind(details, data.frame(series, page, event, session, report))
    }

    #Tidy dataframe
    details <- na.omit(details)

    details
    
    #TO DO - info from page footer; data available there may be dependent on report type.
}

details <- get_TSL_PDF_pages(PDF)

details[1:5,]
```

For the actual race table, we should also capture the event and the session start time. We might also want to capture the weather.

The event is the circuit, the date, and the event name.

```R
details <- get_TSL_PDF_pages('results/Dunlop Endurance Championship.pdf')
details[1:5,]
```

```R
#dbRemoveTable(db, "pdf_pages")
dbWriteTable(db, "pdf_pages", details, append=T)
dbGetQuery(db, 'SELECT * FROM pdf_pages LIMIT 5')
```

So now we should be able to run a query over the PDF data to find the pages associated with a particular event session. 

```R
q='
SELECT * FROM pdf_pages 
WHERE series="Dunlop Endurance Championship" 
    AND event="RACE 1" 
    AND session="RACE" 
    AND report="LAP ANALYSIS";
'

dbGetQuery(db, q)

```

We can try to be more structured in out creation of data tables by creatig them in a more normalised form. We can make use of functions in Simon Willison's `csvs_to_sqlite` command line tool to normalise the data for us if we save the datafiles to CSV first. (We could call the functions from the native Python package by using reticulate, but let's play safe for now!)

```R
system2('csvs-to-sqlite',stdout=T, stderr=T)
```

```R
details
```

## Extract Table Data

We can automatically extract data from tables, although we may want to check that:

- data may need parsing within cell;
- some rows aren't missed by the extractor.

Some pages in the PDF report data as a list rather than a table, eg some of the statistics reports. These pages will need retrieving as text and then undergo some parsing, or will need to be scraped by a more structured scraper.

```R
extract_tables(PDF, pages = 2)
```

```R
t = extract_tables("2019/191403cli.pdf", pages = 3, area = list(c(0, 0, 595, 842)))
t
```

The `tabulizer` table extractor returns the data as a list:

```R
typeof(t)
```

So let's instead put that into a more useful dataframe format.

```R
#Cast the list to a dataframe
df = as.data.frame(t)

#The first row, in this case, represents the column names
colnames(df) <- as.character(unlist(df[1,]))

#Remove the first row that contained the column names
df <- df[-1,]

#Preview the dataframe
df
```

```R
extract_table_as_df = function(f, pages=NULL, area=NULL, header=TRUE){
    t = extract_tables(f, pages = pages, area=area)
    df = as.data.frame(t)
    
    if ( header ){
        #The first row, in this case, represents the column names
        colnames(df) <- as.character(unlist(df[1,]))

        #Remove the first row that contained the column names
        df <- df[-1,]
    }
    
    df
}
```

```R
extract_table_as_df(PDF, pages=3)
```

Alternatively, use the in-built converter, which will always attempt to create a header from the first data row:

```R
extract_tables(PDF, pages=3, output="data.frame")
```

There is also an `output = "csv"` option to write data out to a CSV file.


By the by, we can use the `reticulate` package to allow us to wrangle the dataframe as a Python *pandas* dataframe rather than an R `data.frame`.

```R
#We can see how this looks as a pandas dataframe
library(reticulate)
#pd <- import("pandas",as = "pd",convert = FALSE)
r_to_py(df, convert=T)

#I can't really remember how to work with py in R under reticulate!
```

## Tidying Up Tables

Some of the table extract quite cleanly:

```R
extract_tables(PDF, pages = 4)
```

Others may need cleaning, at least if we go with the guessed at settings.

For example, the following table extraction does not separate out some of the sector times into separate columns:

```R
t_n <- extract_tables(PDF, pages = 5:10)
t_n
```

### Using Explicit, Rather than Guessed At, Co-ordinate Values to Separate Columns

We can pass in co-ordinatates to force particular column splits, telling `tabulizer` not to guess at the table columns and instead passing in explicit column co-ordinates. 

Note that this may require some juggling... For example, we may want to do a couple of passes:

- one to identify the name of the driver and row number markers for them;
- one to identify the timing columns.

We might also need to tune the column settings for different reports (e.g. for tracks where there are differnt numbers of sectors, or columns recorded).


Ona  Mac, co-ordinates for areas can be found via the `Preview` application: `Tools -> Show Inspector` then the fourth, ruler tab. When you make a rectangular selection in the PDF document, the co-ordinates of the top left corner will be displayed as well as the width and height of the selection.

```R
extract_tables(PDF, pages = 5, guess=FALSE, 
               columns=list(c(50, 120, 160, 200, 300, 390, 410, 450, 500, 600)), output='data.frame')
```

Where the data is contained over mutliple lists, we need to make a single list from them.

```R
full <- do.call(rbind, t_n)
full
```

Let's patch the function that converts the extracted list to a dataframe to accommodate that. We can add a handler for the `columns` and `guess` arguments at the same time.

```R
extract_table_as_df = function(f, pages=NULL, area=NULL, columns=NULL, guess=NULL, header=TRUE){
    t = extract_tables(f, pages = pages, area=area, columns=columns, guess=guess)
    
    #Combine multiple tables
    t <- do.call(rbind, t)
    
    df = as.data.frame(t)
    
    if ( header ){
        #The first row, in this case, represents the column names
        colnames(df) <- as.character(unlist(df[1,]))

        #Remove the first row that contained the column names
        df <- df[-1,]
    }
    
    df
}
```

It might also be worth adding to that function something that let's us specify which row a header should be taken from.

```R
#Check it still works for a single page
extract_table_as_df(PDF, pages = 3)
```

```R
extract_table_as_df(PDF, pages = 5, header=F)
```

The following example seems to suggest we're not extracting supposedly the same sort of table from across multiple tables in the same way. One way around this is to define some column settings defined for particular page types.

```R
extract_table_as_df(PDF, pages = 5:10, header=F)
```

### Defining Settings for Particular Pages

Let's explore how to define settings for particular pages.


#### Lap Chart

The lap chart gives times recorded on each lead lap, with the report  split across five sets of grouped columns over one or more pages.

Each grouped set of columns includes:

- vehicle number (`NO`);
- the time difference to the vehicle ahead (`BEHIND`);
- the lap time as a string in the format *DD:HH:MM:S.MS* (`LAP TIME`).

Data for a given lap is recorded over one or more columns. Metadata for each lap is given at the top of the first column associated with the lap. For example: `LAP 1 @ 16:55:57.584`. This metadata gives:

- the lap number;
- the clock time recorded at the end of the lap as completed by the race leader.

So for example:

`LAP 4 @ 16:59:13.069` records the leader's laptime as `1:04.309`. Lap 3 was recorded as `LAP 3 @ 16:58:08.760`.

The clock time for the end of lap 4 = completion time of lap 3 plus leader lap time for lap 4:

> `16:59:13.069 = 16:58:08.760 + 1:04.309`



```R
extract_table_as_df('results/Dunlop Endurance Championship.pdf', pages = 63, header=F)
```

Unfortunately, we can only specify either `columns` *or* `area` but not both.

```R
library(tidyr)
```

```R
lapinfo <- as.data.frame( t( extract_table_as_df('results/Dunlop Endurance Championship.pdf', pages = 63, guess=F, header=F,
                    columns=list(c(125, 237, 350, 464, 600)))[3,] ) )
colnames(lapinfo) <- c('raw')

#tidyr
lapinfo <- lapinfo %>% extract(raw, into=c('lapname', 'lap', 'time'),
                 '(LAP ([0-9]+)) @ (.*)', convert=TRUE)
rownames(lapinfo)<- 1:nrow(lapinfo)

lapinfo

```

Let's now try to separate out all the timing columns:

```R
df <- extract_tables('results/Dunlop Endurance Championship.pdf', pages = 63, header=F, guess=F, output='data.frame',
                    columns= list(c(45,80,114,130,156,192,228,242,269,306,341,358,383,420,454,469,494,529, 568, 600)))
#For now, just grab the first (only) page scraped dataframe
df <- df[[1]]
df
```

*(My table extractor seems to drop empty columns, for example, if there is no pit event.)*


We now need to tidy this up:

- drop the rows at the head: key this on the first row where the first column value starts with `NO`;
- drop the footer: key this based on the first row after the first data row to that is blank.

```R
startrow <- which(startsWith(df[,1],'NO'))+1
startrow
```

```R
#Blank row:
blanks <- which(df[,1]=='')
endrow <- min(blanks[blanks>startrow]) -1
endrow
```

```R
library(dplyr)

df <- df %>% slice(startrow:endrow)
df
```

Issues with this:

- need to fill `NA` column with blanks;
- need to split grouped columns into a long `laps` dataframe;
- some sort of name convention for columns.

```R
#Replace NA with blank string
df[is.na(df)] <- ''
df[1:5,]
```

```R
cols = c('NO','BEHIND','LAPTIME','PIT')
names(df) <- make.unique(rep(cols,5))
df[1:5,]
```

```R
#https://stackoverflow.com/questions/12466493/reshaping-multiple-sets-of-measurement-columns-wide-format-into-single-columns
reshape(df, direction="long", new.row.names =1:10000,
        varying=list(c(1,5,9,13,17), c(2,6,10,14,18),c(3,7,11,15,19),c(4,8,12,16,20)),
        timevar='Count')
```

Of course, it's never that simple... page 69, for example, where we get an overflow...

```R
lap_chart <- extract_tables('results/Dunlop Endurance Championship.pdf', pages = 69, header=F, guess=F, output='data.frame',
              columns= list(c(45,80,114,130,156,192,228,242,269,306,341,358,383,420,454,469,494,529, 568, 600)))[[1]][1:10,]
lap_chart

```

In some cases, the recorded laps may overflow from one column to the next;

```R
as.data.frame( t( extract_table_as_df('results/Dunlop Endurance Championship.pdf', pages = 69, guess=F, header=F,
                    columns=list(c(125, 237, 350, 464, 600)))[3,] ) )

```

We can get around this by linearising the page from several grouped sets columns into a single, grouped selt of columns. We can then clean rows within the single group and append cleaned data from all pages into a single dataframe. From this single dataframe, we can then split the data into the data corresponding to each lap.

```R
lap_chart_cols = c('NO', 'BEHIND', 'LAP TIME', 'PIT')
names(lap_chart) <- make.unique(rep(lap_chart_cols,5))

reshape(lap_chart, direction="long", new.row.names =1:10000,
        varying=list(c(1,5,9,13,17), c(2,6,10,14,18),c(3,7,11,15,19),c(4,8,12,16,20)),
        timevar='Count')[1:10,]
```

```R
lap_chart_cols = c('NO', 'BEHIND', 'LAP TIME', 'PIT')
names(lap_chart) <- make.unique(rep(lap_chart_cols,5))
lap_chart 
```

We can identify the lap rows by reshaping at the column group level:

```R
lap_chart_group <- extract_table_as_df('results/Dunlop Endurance Championship.pdf', pages = 68, guess=F, header=F,
                    columns=list(c(125, 237, 350, 464, 600))) 
names(lap_chart_group) <- make.unique(rep('LAP',5))

lap_chart_group_long <- reshape(lap_chart_group, direction="long", new.row.names =1:10000,
        varying=list(c(1,2,3,4,5)),
        timevar='Count')

lap_rows <- which(grepl("^LAP ", lap_chart_group_long$LAP))
lap_chart_group_long[lap_rows,]
```

**TO DO: Need to see what happens when eg there are less than five lap goups on a page: how are empty col groups treated?**


The next step is to aggregate data from multipe pages into one dataframe.

The lap number will be the lap increment multipled by the page number.

We could also grab the `Page M from N` footer information as the basis for which pages in the PDF to aggregate.

```R
dfs <- extract_tables('results/Dunlop Endurance Championship.pdf', pages = 63:64, header=F, guess=F, output='data.frame',
                    columns= list(c(45,80,114,130,156,192,228,242,269,306,341,358,383,420,454,469,494,529, 568, 600)))

```

I can't think how to do this vector style right now... Here's a literal way:

```R
pageCount <- 1

full_df = data.frame()

for(df in dfs){
    
    startrow <- which(startsWith(df[,1],'NO'))+1
    
    blanks <- which(df[,1]=='')
    endrow <- min(blanks[blanks>startrow]) -1
    
    df <- df %>% slice(startrow:endrow)
    
    cols = c('NO','BEHIND','LAPTIME','PIT')
    names(df) <- make.unique(rep(cols,5))
    
    df <- reshape(df,  direction="long", new.row.names =1:10000,
        varying=list(c(1,5,9,13,17), c(2,6,10,14,18),c(3,7,11,15,19),c(4,8,12,16,20)),
        timevar='Count')
    
    #We can drop the id column
    
    df$Lap <- df$Count * pageCount
    
    full_df = rbind(full_df, df)
    
    
    pageCount <- pageCount + 1
}

full_df
```

Let's get a sneaky preview of how the laptimes are distributed. We'll group on `NO`, but first we need to parse the laptime into a numeric. The `lubridate::hms()` function converts to the time string for us.

```R
#install.packages("lubridate")
library(lubridate)

full_df$laptimeInS = period_to_seconds(hms(full_df$LAPTIME))
```

```R
library(ggplot2)

p <- ggplot(full_df, aes(NO, laptimeInS))
p + geom_boxplot() + coord_flip()
```

To plot the classes, we need to know the classes. We can get this from the classification.

```R
class_df = extract_tables('results/Dunlop Endurance Championship.pdf', pages = 62, header=F, guess=F, output='data.frame',
                    columns= list(c(35,56,84,101,269,364,389,432,465,498,525,560, 600)))[[1]]
class_df
```

Note the exceptions... in a class, there may be `INV` (invited) cars.

Some rows may also overflow to second rows, especially in eg the `NOT CLASSIFIED` or `FASTEST LAP` sections.

So we need to cope with that...

The team and driver details may be merged into each other. We should be able to recover that from other sheets, but it's a real pain here unless we use a heuristic of splitting on camelcase.

```R
#https://stackoverflow.com/a/43706490/454773
paste(strsplit('JMH AutomotiveJohn SEALE / Marcus CLUTTON', "(?<=[a-z])(?=[A-Z])", perl = TRUE)[[1]], collapse=' :: ')
```

There are, however, likely to be exceptions, for example if the latter part of a team name is in uppercase:-(

```R
paste(strsplit('Team BRITMartyn COMPTON / Warren MCKINLAY', "(?<=[a-z])(?=[A-Z])", perl = TRUE)[[1]], collapse=' :: ')
```

If we can get the team names from elsewhere, in the same format, we could just replace them out of this column.


How about getting the column names from a specified row?

```R
#colnames(df) <- as.character(unlist(df[1,]))
headerrow=3
print( as.character(unlist(class_df[headerrow,])) )

class_df[-(1:headerrow),][1:5,]
 
```

Let's apply that:

```R
names(class_df) <- as.character(unlist(class_df[headerrow,]))
class_df <- class_df[-(1:headerrow),]

class_df[1:5,]
```

Let's also clean the class column of invited cars:

```R
class_df$CLASS = gsub(' INV', '', class_df$CL)
class_df$INV = endsWith(class_df$CL, ' INV')
class_df[10:15,]
```

Next up, how can we split the data from the classification PDF into the classified, not classified, and fastest time datasets?

```R
allInOne <- class_df %>% unite('allInOne',colnames(class_df), sep='')
#Remove all spaces - we don't know where a reserved word or phrase may be split
allInOne$allInOne <- gsub("\\s", "", allInOne$allInOne) 
allInOne
```

We can now lookup rows that separate different sections of the classification report.

```R
unclassified_row <- which(grepl("NOTCLASSIFIED", allInOne$allInOne))
unclassified_row
```

```R
fastestLap_row <- which(grepl("FASTESTLAP", allInOne$allInOne))
fastestLap_row
```

We can now filter the classification to give just the classified cars:

```R
class_df[1:(unclassified_row-1),]
```

And the unclassified cars:

```R
unclassified_df <- class_df[(unclassified_row+1):(fastestLap_row-1),]
unclassified_df
```

Maybe simplest to just drop the non-timing data rows and grab driver metadat by JOINing somewhere on `NO`?

```R
unclassified_df[unclassified_df[,]]
```

```R
unclassified_df[unclassified_df['POS']!='',]
```

#### Lap Analysis Pages

The `LAP ANALYSIS` pages record the laptimes for each vehicle, by vehicle. The data is arranged in two columns. Within a column, a vehicle is identified, their laptimes given, and the next vehicle identified. Times for a given vehicle may overflow from one column to the next, or from the second column on the page into the first column of the next.

```R
extract_tables('results/Dunlop Endurance Championship.pdf', pages = 41, 
                          header=F, guess=F, output='data.frame')[[1]][1:10,]
```

To scrape this table, we need to:

- identify the vehicle;
- identify the laptimes recorded for the vehicle.

The data provided for each lap is:

- lap number;
- lap time;
- laptime difference to personal best lap;
- speed (average speed for the lap);
- time of day.

The vehicle's three bast lap times are annotated, as are pit laps (that is, inlaps). The outlap will be significantly longer and includes the pit stop and pit lane loss times. Inlap times may be less than the fastest lap time if the time is set near the start of the pit lane.

```R
extract_tables('results/Dunlop Endurance Championship.pdf', pages = 41, header=F, guess=F, output='data.frame',
                    columns= list(c(52,98,115,168,210,300,352,396,419,467,508, 600)))[[1]]
```

First, let's split everything into two columns and try to pull out driver names and the rows they are associated with.

The driver rows start with a `P` for the position.

```R
lap_analysis_vehicle = extract_tables('results/Dunlop Endurance Championship.pdf', pages = 41, header=F, guess=F, output='data.frame',
                    columns= list(c(300, 600)))[[1]]

lap_analysis_vehicle = reshape(lap_analysis_vehicle, direction="long", new.row.names =1:10000,
    varying=list(c(1,2)), timevar='Col') 


vehicle_rows = which(grepl('P[0-9]+',trimws(lap_analysis_vehicle[,'V1'])))
lap_analysis_vehicle[vehicle_rows,'V1']

```

```R
teams <- data.frame(lap_analysis_vehicle[vehicle_rows,'V1']) %>% extract(1, c('POS','NO','TEAM'), 
                                                                regex = "(P[0-9]+) ([0-9]+) (.*)")

teams
```

```R
#Generate the pairwise ranges
#https://stackoverflow.com/a/41206700/454773
lap_ranges <- rbind(vehicle_rows[-length(vehicle_rows)], vehicle_rows[-1])
lap_ranges <- split(lap_ranges, col(lap_ranges))
```

Now let's split the data into two groups of 6 columns, and try to split the data out by driver.

We have the rows that mark each drive, so use that as the first approximate pass.

This first attempt is just on a single page.

```R
lap_analysis = extract_tables('results/Dunlop Endurance Championship.pdf', pages = 41,
                              header=F, guess=F, output='data.frame',
                              columns= list(c(52,98,115,168,210,300,352,396,419,467,508, 600)))[[1]]

lap_analysis_cols = c('LAP','LAP TIME','ANN','DIFF','MPH','TIME OF DAY')
names(lap_analysis) <- make.unique(rep(lap_analysis_cols,2))

lap_analysis <- reshape(lap_analysis, direction="long", new.row.names =1:10000,
    varying=list(c(1,7), c(2,8),c(3,9),c(4,10),c(5,11),c(6,12)), timevar='Col')

full_lap_analysis <- data.frame()
#Need to autsplit into groups
for (lap_range in lap_ranges){
    full_lap_analysis <- rbind(full_lap_analysis, lap_analysis[lap_range[1]:(lap_range[2]-1),] )

    }

#Clear blank rows and head row
full_lap_analysis <- full_lap_analysis[!(full_lap_analysis$LAP %in% c("","LAP")) , ]

#Merge in driver details

full_lap_analysis <- full_lap_analysis %>%
                    mutate(POS = str_extract(LAP, "(P[0-9]+)")) %>%
                    fill(POS)  %>% 
                    inner_join(teams) %>%
                    #Drop the Col and id columns
                    select(-c(id,Col)) %>%
                    #Drop the position header rows
                    filter(!startsWith(LAP,'P')) %>%
                    #Tidy the lap column
                    mutate(LAP = str_extract(LAP, "([0-9]+) ")) %>%
                    #Tidy the POS column
                    mutate(POS = str_extract(POS, "([0-9]+)"))

full_lap_analysis#[1:10,]

```

We now need to identify


Now let's tidy that up and apply it to several pages.

```
#muliple pages
pageCount <- 1

full_df = data.frame()

for(df in dfs){
    
    startrow <- which(startsWith(df[,1],'NO'))+1
    
    blanks <- which(df[,1]=='')
    endrow <- min(blanks[blanks>startrow]) -1
    
    df <- df %>% slice(startrow:endrow)
    
    cols = c('NO','BEHIND','LAPTIME','PIT')
    names(df) <- make.unique(rep(cols,5))
    
    df <- reshape(df, direction="long", new.row.names =1:10000,
        varying=list(c(1,5,9,13,17), c(2,6,10,14,18),c(3,7,11,15,19),c(4,8,12,16,20)),
        timevar='Count')
    
    df$Lap <- df$Count * pageCount
    
    full_df = rbind(full_df, df)
    
    
    pageCount <- pageCount + 1
}

full_df
```

```R
#df$OUT = lag(df$PIT,1)
```

## Safety Car Laps

Can we identify those? They are highlighed in yellow on the PDFs but `tabulizer` doesn't flag that up in any way.

It looks like there is a *flag* history that we can draw on to detect this, at least in terms of time.

We can also get lap start time by lap number from the `Lap Chart` tables and build up a picture of the race from those times and the flag times.

```R
extract_tables('results/Dunlop Endurance Championship.pdf', pages = 54, 
                          header=F, guess=F, output='data.frame')[[1]]

```

```R

```

```R

```

```R

```

## Comparing Driver Performance - In Class

To ensure balanced racing, race promoters need to ensure that cars and drivers are appropriately classed.

One way to check this is to compare racing lap times, which is to say laptimes:

- that are not PIT related (in-lap or out-lap);
- that are not completed under safety car or full course yellow flags.

Note that there other ways we might compare drivers:

- INLAP and OUTLAP times; (can we also get pit lane times somehow?)




```R

```

```R

```

```R

```

```R

```

```R

```

```R
extract_table_as_df(PDF, pages = 10, header=F)
```

```R
extract_tables("2019/191403cli.pdf", pages = 11)
```

```R
extract_tables(PDF, pages = 12)
```

```R
extract_tables(PDF, pages = 14)
```

```R
extract_tables(PDF, pages = 15)
```

```R
extract_tables(PDF, pages = 16)
```

```R
extract_tables(PDF, pages = 19)
```

```R
#Will need tidying
extract_tables(PDF, pages = 20:23)
```

```R
extract_tables(PDF, pages = 24)
```

```R
extract_tables(PDF, pages = 25)
```

```R
extract_tables(PDF, pages = 26:29)
```

```R
extract_tables(PDF, pages = 32)
```

```R
extract_tables(PDF, pages = 33)
```

```R
extract_tables(PDF, pages = 34)
```

```R

```
