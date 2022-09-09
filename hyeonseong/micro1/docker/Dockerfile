FROM python:3.6
EXPOSE 5000
RUN mkdir /hsapp
RUN mkdir /hsapp/templates
WORKDIR /hsapp
COPY ./hsdef/* /hsdef/
COPY ./hslib/* /hslib/
COPY ./templates/* /hsapp/templates/
ADD ./micro1/ /hsapp/
RUN apt-get upgrade -y
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
CMD ["python3",  "/hsapp/Request.py"]
# CMD ["python3",  "/hsapp/main.py"]