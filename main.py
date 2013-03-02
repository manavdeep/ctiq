import webapp2
import jinja2
import os
import json
import math
import datetime

from google.appengine.ext import db

temp_dir=os.path.join(os.path.dirname(__file__), "")
jinja_env=jinja2.Environment(loader = jinja2.FileSystemLoader(temp_dir), autoescape = True)


class User(db.Model):
    email = db.StringProperty()
    msg = db.TextProperty()
    time = db.DateTimeProperty(auto_now_add = True)

class Main(webapp2.RequestHandler):
    def render_front(self, users):
        template = jinja_env.get_template("templates/basic.html")
        self.response.out.write(template.render(users = users))

    def get(self):
        users = db.GqlQuery("select * from User order by time desc")
        users = list(users)
        self.render_front(users)

    def post(self):
        email = self.request.get("email")
        msg = self.request.get("message")
        u = User(email = email, msg = msg)
        u.put()
        self.redirect("/")


class Accident(db.Model):
    point = db.GeoPtProperty(required = True)
    sev = db.RatingProperty(required = True)
    #userid = db.StringProperty()
    desc = db.TextProperty()
    time = db.DateTimeProperty(auto_now_add = True)


def generate_accident_dict(accident):
    d = {}
    d["lat"] = accident.point.lat
    d["longi"] = accident.point.lon
    d["descr"] = accident.desc
    d["severity"] = accident.sev
    d["time"] = accident.time.strftime("%c")
    return d


class AccidentJson(webapp2.RequestHandler):
    def get(self):
        accidents = db.GqlQuery("select * from Accident order by time desc")
        accidents = list(accidents)
        l = list(generate_accident_dict(accident) for accident in accidents)
        self.response.headers["Content-Type"] = "application/json; charset=utf-8"
        self.response.out.write(json.dumps(l))


class ReportAccident(webapp2.RequestHandler):
    def get(self):
        template = jinja_env.get_template("templates/report_accident.html")
        self.response.out.write(template.render())

    def post(self):
        lat = self.request.get("lat")
        lon = self.request.get("longi")
        sev = self.request.get("severity")
        sev = int(sev)
        desc = self.request.get("descr")
        geopt = db.GeoPt(lat = float(lat), lon = float(lon))
        a = Accident(point = geopt, 
                     sev = sev, 
                     desc = desc)
        a.put()
        self.redirect("/report/accident")

class AccidentUpdate(webapp2.RequestHandler):
    def get(self):
        template = jinja_env.get_template("templates/accident_update.html")
        self.response.out.write(template.render())
    
    def post(self):
        lat = self.request.get("lat")
        lat = float(lat)
        lon = self.request.get("longi")
        lon = float(lon)
        dtnow = datetime.datetime.now()
        dtold = dtnow - datetime.timedelta(hours = 5)
        accidents = db.GqlQuery("select * from Accident where time > :1", dtold)
        accidents = list(accidents)
        close = []
        for accident in accidents:
            dist = self.get_distance(lat, lon, accident.point.lat, accident.point.lon)
            if  dist < 20:
                close.append(accident)
        l = list(generate_accident_dict(accident) for accident in close)
        self.response.headers["Content-Type"] = "application/json; charset=utf-8"
        self.response.out.write(json.dumps(l))

    def get_distance(self, lat1, lon1, lat2, lon2):
        Radius = 6371
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat / 2)* math.sin(dLat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
        temp = Radius * c
        return temp


app = webapp2.WSGIApplication([('/', Main), 
                               ('/accidents\.json', AccidentJson),
                               ('/report/accident', ReportAccident),
                               ('/accidentupdate', AccidentUpdate)])
