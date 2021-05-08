#Use a base Jupyter notebook container
FROM jupyter/base-notebook


#We need to install some Linux packages
USER root

#Using Selenium to automate a firefox or chrome browser needs geckodriver in place
ARG GECKO_VAR=v0.23.0
RUN wget https://github.com/mozilla/geckodriver/releases/download/$GECKO_VAR/geckodriver-$GECKO_VAR-linux64.tar.gz
RUN tar -x geckodriver -zf geckodriver-$GECKO_VAR-linux64.tar.gz -O > /usr/bin/geckodriver
RUN chmod +x /usr/bin/geckodriver
RUN rm geckodriver-$GECKO_VAR-linux64.tar.gz

#Install packages required to allow us to use eg firefox in a headless way
#https://www.kaggle.com/dierickx3/kaggle-web-scraping-via-headless-firefox-selenium
RUN apt-get update \
    && apt-get install -y libgtk-3-0 libdbus-glib-1-2 xvfb \
    && apt-get install -y firefox \
    && apt-get clean
ENV DISPLAY=":99"


#Copy repo files over
COPY ./notebooks ${HOME}/work
#And make sure they are owned by the notebook user...
RUN chown -R ${NB_USER} ${HOME}

#Reset the container user back to the notebook user
USER $NB_UID

#Install Selenium python package
RUN pip install --no-cache selenium matplotlib pandas lxml


##By the by, there is also a Python package for installing geckodriver
#RUN pip install --no-cache webdriverdownloader
##This can be used as follows within a notebook
##from webdriverdownloader import GeckoDriverDownloader
##gdd = GeckoDriverDownloader()
##gdd.download_and_install("v0.23.0")
##If required, the path to the drive can be set explicitly:
##from selenium import webdriver
##browser = webdriver.Firefox(executable_path=geckobin, options=options)

