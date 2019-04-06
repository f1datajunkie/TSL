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


The python tabula wrapper doesnlt appear to work... so let's try the R one...

```R
install.packages("tabulizer")
```

```R
#sudo R CMD javareconf
library("tabulizer")
out1 <- extract_tables("2019/191403cli.pdf")
```

```R
out1
```

```R
#Need to  doc to get info about what's on each page
```

```R
extract_tables("2019/191403cli.pdf", pages = 2)
```

```R
extract_tables("2019/191403cli.pdf", pages = 3)
```

```R
extract_tables("2019/191403cli.pdf", pages = 4)
```

```R
#this sort of thing will need cleaning...
extract_tables("2019/191403cli.pdf", pages = 5:10)
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
