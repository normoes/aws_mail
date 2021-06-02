# Changelog of aws_mail.


## 2021-06-03
* Initial release.
* Supports general mail format in incoming data:
```
Subject: tool's email subject
To: Recipient addresses
```
* Supports specific tool logs (exclude everything else):
    - `logwatch`
    - `unattended-upgrade`
    - `cron`
