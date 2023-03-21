"""
checkpm.py - check the existence post-mortems of OpsGenie Incidents and creates if needed

Uses the incident API to list resolved and closed incidents without post-mortems,then creates a post-mortem and sets
it to standard format. The idea is to run it evey 10 minutes and enforce a standard postmortem format.
"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import argparse
import json
import smtplib
import time
from secrets import og_key, sender_pass
import requests
from configs import mailuser, mailreceiver, actor

# timeout value for HTTP REST API calls
TM=60


def logMessage(m):
  """ log message to prefered medium - here an email"""
  mail_content = "Hello, there is a new Issue: " + m

  #The mail addresses and password
  sender_address = mailuser
  receiver_address = mailreceiver
  #Setup the MIME
  message = MIMEMultipart()
  message['From'] = sender_address
  message['To'] = receiver_address
  message['Subject'] = 'New Issue'   #The subject line
  #The body and the attachments for the mail
  message.attach(MIMEText(mail_content, 'plain'))
  #Create SMTP session for sending the mail
  session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
  session.starttls() #enable security
  session.login(sender_address, sender_pass) #login with mail_id and password
  text = message.as_string()
  session.sendmail(sender_address, receiver_address, text)
  session.quit()


def getIncidents(priority, status, hourdelta):
  """ returns resolved incidents with no postmortem with specified priority/status and the passed hour query time"""

  if priority not in ("P1","P2","P3","P4","P5"):
    priority = "P1"
  now = int(time.time())
  deltaback = now - 60*60*hourdelta
  initialURL = "https://api.opsgenie.com/v1/incidents"
  query = "?query=status%3A" + status + "%20AND%20postmortemStatus%3Ano-postmortem%20AND%20priority%3A" + priority + "%20AND%20updatedAt%3E"+str(deltaback)
  if args.debug:
    print(initialURL,query)
  URL = initialURL + query
  headers = {"Content-Type": "application/json", "Authorization": og_key}
  try:
    result = requests.get(URL, headers=headers, timeout=TM)
    messages = result.json()
    return messages["data"]
  except:
    messages = {}
    return messages 


def insertExtraProperty(incidentid,key,value):
  """ record in extra property """

  initialURL = "https://api.opsgenie.com/v1/incidents/"
  URL = initialURL + incidentid + "/details"
  jsondata = {"details": { key :value }}
  if args.debug:
    print(URL,jsondata)
  headers = {"Content-Type": "application/json", "Authorization": og_key}
  try:
    data = json.dumps(jsondata)
    result = requests.post(URL, data=data, headers=headers, timeout=TM)
    if args.debug:
      print(result)
    if result.status_code >= 200 and result.status_code < 300:
      json_obj = result.json()
      if args.debug:
        print(json_obj)
    else:
      logMessage("Non 200 code from OpsGenie")
  except Exception as e:
    print(e)
    logMessage(f"JSON conversion error in InsertExtraProperty: {e}")


def writeStandardPostMortem( postmortemid ):
  """ write the standard string to the postmortem specified """
  initialURL = "https://api.opsgenie.com/v2/postmortem/"
  URL = initialURL + postmortemid + "/content"
  # for the time being still hard coded, very long, note the continuation \ in each line
  jsondata = {"type":"adf", "content":'{"version":1,"type":"doc","content":[{"type":"heading","attrs":{"level":4},\
"content":[]},{"type":"paragraph","content":[{"type":"text","text":"Please make sure the post-mortem\
 answers the following questions, even though some items might already be part of information in the\
 OpsGenie Incident. Aim for making the post-mortem self contained, i.e. copy the information necessary\
 from Slack or the Incident itself so that it can be read without referring to other information sources.\
 Refrain from internal jargon, and make the post-mortem as readable as possible."}]},{"type":"paragraph",\
"content":[{"type":"text","text":" "}]},{"type":"bulletList","content":[{"type":"listItem","content":\
[{"type":"paragraph","content":[{"type":"text","text":"What happened? "}]}]},{"type":"listItem","content":\
[{"type":"paragraph","content":[{"type":"text","text":"When did it start, when did it end? What was the\
 downtime?"}]}]},{"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":\
"How did we fix it? What steps were taken?"}]}]},{"type":"listItem","content":[{"type":"paragraph",\
"content":[{"type":"text","text":"How and when did we get notified?"}]}]},{"type":"listItem","content":\
[{"type":"paragraph","content":[{"type":"text","text":"What application and geography?"}]}]},{"type":\
"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":"What subset of customers?"\
}]}]},{"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":"Root Cause"}]}]}\
,{"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":"What can we do\
 to solve the issue in the future?"}]}]}]},{"type":"paragraph","content":[{"type":"text","text":"For\
 example a hostname like “orion” only has meaning to a part of SRE. We need to\
 say  Application XYZ in Asia  was affected - x accounts, no UI login, no API login, Batch not \
affected. "}]},{"type":"paragraph","content":[{"type":"text","text":"Please add tickets for all \
 actions-items."}]},{"type":"paragraph","content":[{"type":"text","text":"When\
 done, add a note to Support in the related incident Slack channel so that they can start a customer\
 facing RCA. Keep times in UTC."}]},{"type":"paragraph","content":[{"type":"text","text":"We have 48  business hours to\
 finish the post-mortem."}]},{"type":"paragraph","content":[{"type":"text","text":"Work on Action Item\
 tickets is higher priority than Business as Usual work, but lower than ongoing incidents."}]},{"type":"paragraph",\
"content":[{"type":"text","text":"Delete the above and us this template/example. Maintain the bolded \
sections."}]},{"type":"heading","attrs":{"level":4},"content":[{"type":"text","text":"Description"}]}\
,{"type":"paragraph","content":[{"type":"text","text":"The database server orion\
 in Application XYZ  in Asia was not accessible and SQL services were down . The server went offline on \
Oct 11th, at 19:42 UTC and was brought up at 19:50 UTC. "}]},{"type":"heading","attrs":{"level":4},\
"content":[{"type":"text","text":"Detection"}]},{"type":"paragraph","content":[{"type":"text","text":\
"Monitoring detected that the system was down at x:xx UTC."}]},{"type":"paragraph",\
"content":[{"type":"text","text":"OR? A client notified us at x:xx UTC"}]},{"type":"heading","attrs":\
{"level":4},"content":[{"type":"text","text":"Impact"}]},{"type":"paragraph","content":[{"type":"text",\
"text":"During the above window all clients on the server were unable to login via UI and API, all \
Campaigns were stopped as well."}]},{"type":"heading","attrs":{"level":4},"content":[{"type":"text",\
"text":"Root Cause"}]},{"type":"paragraph","content":[{"type":"text","text":"In September 2022 the \
underlying storage for the orion server was changed or increased with a new device. Due to the new \
device disk space monitoring needed to be reestablished, but the ticket stalled"}]},{"type":"heading",\
"attrs":{"level":4},"content":[{"type":"text","text":"Mitigation"}]},{"type":"paragraph","content":\
[{"type":"text","text":"The Systems SRE team added space to the underlying server"}]},{"type":\
"heading","attrs":{"level":4},"content":[{"type":"text","text":"Action Items"}]},{"type":"bulletList",\
"content":[{"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":\
"Establish disk space monitoring for orion"}]},{"type":"bulletList","content":\
[{"type":"listItem","content":[{"type":"paragraph","content":[{"type":"text","text":\
"https://ticket-link/ticket"}]}]}]}]},{"type":"listItem","content":\
[{"type":"paragraph","content":[{"type":"text","text":"Review disk space monitoring in Asia, US and \
Europe"}]}]}]},{"type":"paragraph","content":[{"type":"text","text":"PS: All action items\
 with owners and tickets - label tickets with “postmortem”"},{"type":"hardBreak"}]},\
{"type":"paragraph","content":[]}]}'}
# jsondata config done
  data = json.dumps(jsondata)
  headers = {"Content-Type": "application/json", "Authorization": og_key}
  try:
    result = requests.put(URL, data=data, headers=headers, timeout=TM)
    if result.status_code >= 200 and result.status_code < 300:
      json_obj = result.json()
      if args.debug:
        print(json_obj)
    else:
      logMessage("Non 200 code from OpsGenie")
  except Exception as e:
    print(result.status_code)
    if "Expecting value: line 1 column 1 (char 0)" in str(e):
      print("Normal Error: expecting value 1 of 1")
    else:
      logMessage(f"JSON conversion error in writeStandardPostMortem: {e}")


def createPostMortem( incidentid ):
  """ create a PM for an incident is done by simploy posting to the PM API """

  URL = "https://api.opsgenie.com/v2/postmortem"
  jsondata = {"incidentId": incidentid, "actorUserId": actor }
  headers = {"Content-Type": "application/json", "Authorization": og_key}
  try:
    data = json.dumps(jsondata)
    result = requests.post(URL, data=data, headers=headers, timeout=TM)
    if args.debug:
      print(result)
    if result.status_code >= 200 and result.status_code < 300:
      json_obj = result.json()
      if args.debug:
        print(json_obj)
      postmortemid = json_obj["postmortemId"]
      time.sleep(5)
      # once it is created we want to reocrd it in the incident as an extraproperty
      # and then overwrite it with our template since the system template is not configurable
      print( "PMID:", postmortemid)
      insertExtraProperty(incidentid, "postmortemId", postmortemid)
      writeStandardPostMortem(postmortemid)
    else:
      logMessage("Non 200 code from OpsGenie")
  except Exception as e:
    logMessage(f"JSON conversion error in createPostMortem: {e}")


def checkIncidents(incidents):
  """ these incdents should have post-mortem created: we are looking for resolved incidents that have no post-mortem """

  nrofincidents = len(incidents)
  if args.debug:
    print(nrofincidents)
  if nrofincidents > 0:
    for i in range(0, nrofincidents):
      incidentid = incidents[i]["id"]
      print(incidentid, incidents[i]["message"], ":", incidents[i]["description"])
      if "extraProperties" in incidents[i]:
        if "postmortemId" in incidents[i]["extraProperties"]:
          # this should not happen, we recorded an automaticaly generated PM, but it is not there
          pmid = incidents[i]["extraProperties"]["postmortemId"]
          error = f"PMId exists but no PM {pmid} {incidentid}"
          print(error)
          #logMessage(error)
        else:
          print(incidentid)
          createPostMortem(incidentid)


""" main function """
# build commandline options and defaults - default = remote = false, record = false, details = false
parser = argparse.ArgumentParser(description='Just True and False')
parser.add_argument('--debug', dest="debug", default=False, action="store_true", help="debug")
args = parser.parse_args()

p1incidents = getIncidents("P1","resolved", 30000)
p1incidents = p1incidents + getIncidents("P1","closed", 30000)
p2incidents = getIncidents("P2","resolved", 30000)
p2incidents = p2incidents + getIncidents("P2","closed", 30000)
incidents = p1incidents + p2incidents
checkIncidents(incidents)

