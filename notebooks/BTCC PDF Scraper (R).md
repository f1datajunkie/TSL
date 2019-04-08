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

# BTCC PDF Scraper


The python tabula wrapper doesn't appear to work... so let's try the R one...

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
library(stringi)

#Clean whitespace
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

```R
extract_tables(PDF, pages = 5, guess=FALSE, 
               columns=list(c(50, 120, 160, 200, 300, 390, 410, 450, 500, 600)), output='data.frame')
```

Where the data is contained over mutliple lists, we need to make a single list from them.

```R
full <- do.call(rbind, t_n)
full
```

Let's patch the function that converts the extracted list to a dataframe to accommodate that...

```R
extract_table_as_df = function(f, pages=NULL, area=NULL, header=TRUE){
    t = extract_tables(f, pages = pages, area=area)
    
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

```R
#Check it still works for a single page
extract_table_as_df(PDF, pages = 3)
```

```R
#The following example seems to suggest we're not extracting tables the same way...
extract_table_as_df(PDF, pages = 5:10, header=F)
```

```R
extract_table_as_df(PDF, pages = 5, header=F)
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
