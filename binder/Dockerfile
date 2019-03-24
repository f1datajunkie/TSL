FROM jupyter/base-notebook


USER root

ARG GECKO_VAR=v0.23.0
RUN wget https://github.com/mozilla/geckodriver/releases/download/$GECKO_VAR/geckodriver-$GECKO_VAR-linux64.tar.gz
RUN tar -x geckodriver -zf geckodriver-$GECKO_VAR-linux64.tar.gz -O > /usr/bin/geckodriver
RUN chmod +x /usr/bin/geckodriver
RUN rm geckodriver-$GECKO_VAR-linux64.tar.gz

#https://www.kaggle.com/dierickx3/kaggle-web-scraping-via-headless-firefox-selenium
RUN apt-get update \
    && apt-get install -y libgtk-3-0 libdbus-glib-1-2 xvfb \
    && apt-get install -y firefox \
    && apt-get clean
ENV DISPLAY=":99"


#Copy repo files over
COPY ./notebooks ${HOME}/work
RUN chown -R ${NB_USER} ${HOME}

USER $NB_UID

#There is also a Python package for installing geckodriver
RUN pip install --no-cache selenium webdriverdownloader
#from webdriverdownloader import GeckoDriverDownloader
#gdd = GeckoDriverDownloader()
#gdd.download_and_install("v0.23.0")
