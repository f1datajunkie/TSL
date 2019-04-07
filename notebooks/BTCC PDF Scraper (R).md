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
install.packages("tabulizer")
```

```R
#sudo R CMD javareconf
library("tabulizer")
```

```R
get_page_dims("2019/191403cli.pdf", pages=1)
```

```R
#locate_areas("2019/191403cli.pdf", pages=1)
```

## Extract Page Info

We can extract text from the PDFs using the `extract_text()` function:

```R
extract_metadata("2019/191403cli.pdf")
```

We can use the `area=` parameter to specify `(top, left, bottom, right)` area co-ordinates within which `tabulizer` should look for the table information.

```R
#Page header
t = extract_text("2019/191403cli.pdf", pages = 13, area = list(c(0, 0, 120, 600)))
cat(t)
```

Where the header is split over two lines, we can can split the string to access the separate components:

```R
paste(strsplit(t, '\n')[[1]][1], '*and*', strsplit(t, '\n')[[1]][2])
```

```R
#What happens with the empy second item?
t = extract_text("2019/191403cli.pdf", pages = 2, area = list(c(0, 0, 120, 600)))
paste(strsplit(t, '\n')[[1]][1], '*and*', strsplit(t, '\n')[[1]][2])
```

We can then grab the headings for each page. 

*TO DO: split the lines on line breaks and make a dataframe of this?*

```R
for (page in 1:extract_metadata("2019/191403cli.pdf")$pages){
    cat( paste('Page', page, '-',
               extract_text("2019/191403cli.pdf", pages = page, area = list(c(0, 0, 120, 600))), '\n' ))
}
```

The page footer may also contain useful information:

```R
#Page footer
t = extract_text("2019/191403cli.pdf", pages = 9, area = list(c(760, 0, 1000, 600)))
cat(t)
```

## Extract Table Data

We can automatically extract data from tables, although:

- it will need parsing within cell;
- some rows may missed by the extractor(?).

Some pages in the PDF report data as a list rather than a table, eg some of the statistics reports. These pages will need retrieving as text and then undergo some parsing, or will need to be scraped by a more structured scraper.

```R
extract_tables("2019/191403cli.pdf", pages = 2)
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
extract_table_as_df("2019/191403cli.pdf", pages=3)
```

Alternatively, use the in-built converter, which will always attempt to create a header from the first data row:

```R
extract_tables("2019/191403cli.pdf", pages=3, output="data.frame")
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
extract_tables("2019/191403cli.pdf", pages = 4)
```

Others may need cleaning, at least if we go with the guessed at settings.

For example, the following table extraction does not separate out some of the sector times into separate columns:

```R
t_n <- extract_tables("2019/191403cli.pdf", pages = 5:10)
t_n
```

### Using Explicit, Rather than Guessed At, Co-ordinate Values to Separate Columns

We can pass in co-ordinatates to force particular column splits, telling `tabulizer` not to guess at the table columns and instead passing in explicit column co-ordinates. 

Note that this may require some juggling... For example, we may want to do a couple of passes:

- one to identify the name of the driver and row number markers for them;
- one to identify the timing columns.

We might also need to tune the column settings for different reports (e.g. for tracks where there are differnt numbers of sectors, or columns recorded).

```R
extract_tables("2019/191403cli.pdf", pages = 5, guess=FALSE, 
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
extract_table_as_df("2019/191403cli.pdf", pages = 3)
```

```R
#The following example seems to suggest we're not extracting tables the same way...
extract_table_as_df("2019/191403cli.pdf", pages = 5:10, header=F)
```

```R
extract_table_as_df("2019/191403cli.pdf", pages = 5, header=F)
```

```R
extract_table_as_df("2019/191403cli.pdf", pages = 10, header=F)
```

```R
extract_tables("2019/191403cli.pdf", pages = 11)
```

```R
extract_tables("2019/191403cli.pdf", pages = 12)
```

```R
extract_tables("2019/191403cli.pdf", pages = 14)
```

```R
extract_tables("2019/191403cli.pdf", pages = 15)
```

```R
extract_tables("2019/191403cli.pdf", pages = 16)
```

```R
extract_tables("2019/191403cli.pdf", pages = 19)
```

```R
#Will need tidying
extract_tables("2019/191403cli.pdf", pages = 20:23)
```

```R
extract_tables("2019/191403cli.pdf", pages = 24)
```

```R
extract_tables("2019/191403cli.pdf", pages = 25)
```

```R
extract_tables("2019/191403cli.pdf", pages = 26:29)
```

```R
extract_tables("2019/191403cli.pdf", pages = 32)
```

```R
extract_tables("2019/191403cli.pdf", pages = 33)
```

```R
extract_tables("2019/191403cli.pdf", pages = 34)
```

```R

```
