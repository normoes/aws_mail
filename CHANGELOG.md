# Changelog of aws_mail.

## 2021-06-07
* Log into `/var/log/aws_log/aws_log.log`.
* Allow to set log level.


## 2021-06-03
* Add `--version` to output the current version.

## 2021-06-02
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
