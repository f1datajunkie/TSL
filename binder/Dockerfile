FROM jupyter/base-notebook

#Via https://jpmelos.com/articles/how-use-chrome-selenium-inside-docker-container-running-python/

USER root
RUN apt-get update && apt-get install -y firefox && apt-get clean

USER $NB_UID

RUN pip install --no-cache selenium
