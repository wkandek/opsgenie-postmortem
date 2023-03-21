# opsgenie-postmortem
Create a postmortem for Opsgenie incidents once an incident is closed

Currently (2023) OpsGenie post-mortem creation has to be kicked off manually once an anlyst indicates they want a post-mortem. Then a defaolt template is used to populate the post-mortem. A workflow where a post-mortem is mandatory, once a incident is closed is therefore not supported.

The following script ogmp.py runs periodically and enforces the creation of a postmortem and the definition of a new default format

It uses the OpsGenie APIs to: 
- check whether an incident is closed
- check whether it has a post-mortem
- if not creates a post-mortem with a locally defined format and registers the post-mortem ID in the incident as a key-value attribute

The logic is a bit convoluted as the OpsGenie post-mortem API is incomplete. See: https://community.atlassian.com/t5/Opsgenie-questions/Find-the-post-mortem-assocaied-with-an-incident-via-API/qaq-p/2216065 for an exploration of the subject.

The idea is to run this under cron every 10 minutes.

Note: configs.py and keys.py need to be adapted to your environment for OpsGenie API keys.
