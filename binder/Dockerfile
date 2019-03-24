FROM jupyter/base-notebook


USER root

#https://www.kaggle.com/dierickx3/kaggle-web-scraping-via-headless-firefox-selenium
RUN apt-get update \
    && apt-get install -y libgtk-3-0 libdbus-glib-1-2 xvfb \
    && apt-get install -y firefox \
    && apt-get clean
ENV DISPLAY=":99"

USER $NB_UID

RUN pip install --no-cache selenium webdriverdownloader
#from webdriverdownloader import GeckoDriverDownloader
#gdd = GeckoDriverDownloader()
#gdd.download_and_install("v0.23.0")
