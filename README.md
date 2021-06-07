# AWS mail client

The tool is written to send everything piped into it from `stdin` as an email, considering the settings found in `config.yml`.

As this client uses the `boto3` library to send emails through AWS SES, it can be used as replacement for `sendmail` or any other mailer client on AWS instances - I could not make the `postfix` configuration work at all for that scenario.

Please also see the below: *Configure tools relying on /usr/sbin/sendmail*.

The AWS EC2 instance should have an instance role attached, which allows sending emails through AWS SES.

By default it just sends everything from `stdin`.
Also by default,The tool recognizes certain tools' log structure and will leave everything not part of it. This works for:
* `logwatch`
* `unattended-upgrade`
* `cron`

*_Note_*:
* `aws_mail` ignores unknown cli arguments, e.g. the ones usually sent to `sendmail`.

## Quick start

```
# Install.
python3 -mvenv venv
venv/bin/pip install aws_mail

# Configuration.
mkdir /etc/aws_mail/
touch /etc/aws_mail/config.yml
# Copy fromthe example 'config.yml' into '/etc/aws_mail/config.yml'.
# Adapt the configuration options.

# Use.
echo -e "subject: update\nto: email@address.com\n\nGood day today." | venv/bin/aws_mail --region us-east-1
```

## Installation

This tool is available on pypi.
It is best to install it into a virtual environment:
```
python3 -m venv venv
venv/bin/pip install aws_mail
```

Instaalled this way you will find an executable called `aws_mail`.
Its location depends on the way you installed the tool - I recommend to work with absolute paths when referring to the `aws_mail` location.

*_Note_*:
* The default location for the configuration file is `/etc/aws_mail/config.yml`.
* The default log path is `/var/log/aws_mail`.
* Make sure those directories/files exist.

## Usage

In general `aws_mail` works like this:
```
    echo "Good day today." | venv/bin/aws_mail --region us-east-1
```

The above reads the configuration from `/etc/aws_mail/config.yml` and logs into `/var/log/aws_mail/aws_mail.log`.

## Configuration

| option | description | default | configuration options |
|--------|-------------|---------|-----------------------|
| `--log-path`  | Path to the log file directory. | `/var/log/aws_mail` | Absolute, relative path and/or symlink. |
| `--config`  | Path to the configuration file. | `/etc/aws_mail/config.yml` | Absolute, relative path and/or symlink. |
| `--region`  | AWS region to use. | `us-east-1` | Can also be set in the configuration file. |
| `--default-subject`  | Forces subject to be loaded from the configuration file <\br> Otherwise considers a line starting with `Subject:`. | `False` (not set) | Default value is the name of the event in the configuration file. |
| `--default-recipients`  | Forces recipients to be loaded from the configuration file <\br> Otherwise considers a line starting with `To:`. | `False` (not set) | Default value is set in configuration file. |
| `--log-level`  | Sets log level. | `ERROR` | `log_level` as `str`. |

Examples:
* Set a different log level:
    ```bash
        echo "Some message." | venv/bin/aws_mail --log-level INFO
    ```
*

### Configuration file
Email settings need to be configured in `config.yml`.
This configures an `AwsSesEmailHook` event from the [`eventhooks`](https://github.com/normoes/events) module.

Since the default path to the configuration file is `/etc/aws_mail/config.yml`, you need to make sure both, path and file, exist.
However, you can also give another configuration file location by passing:
```
--config /path/to/config.yml
```

Example configuration file:
```
log_level: "ERROR"
events:
  example_mail_event_name:  # <-- Name of the event, used as default subject.
    enabled: true  # <-- Everything but 'true' disables this event.
    type: AwsSesEmailHook  # <-- Type of hook to use.
    sender: "{{ sender_address }}"  # <-- Change that to your sender address.
    sender_name: "{{ sender_name }}"  # <-- Change that to your sender name.
    region: "{{ aws_region }}"  # <-- AWS region the AWS SES endpoint is listening on.
    recipients:  # <-- Change that if you like or configure the tool properly, see below.
      - "{{ recipient_address}}"
```

If set, the cli option `--log-level` overwrites the configuration `log_level` read from the configuration file.

### Email subject
If the tool should find a line starting with `subject:` (piped into it), this will be used as email subject.
```
    # The subject will be 'Daily logs from server1'.
    echo -e "subject: Daily logs from server1\nGood day today." | venv/bin/aws_mail
```
Otherwise or when forced with `--default-subject`, the event name (key in `config.yml`) is used as email subject.
```
    # If event in 'config.yml' is called 'example_mail_event_name'
    events:
      example_mail_event_name:
      ...
    # the actual subject will be 'example_mail_event_name':
    echo -e "subject: Daily logs from server1\nGood day today." | venv/bin/aws_mail --default-subject
```

### Email recipients
If the tool should find a line starting with `to:` (piped into it), this will be used as email recipients.
```
    # The recipients will be 'email@address.com,another@address.com'.
    echo -e "to: email@address.com,another@address.com\nGood day today." | venv/bin/aws_mail
```
Otherwise or when forced with `--default-recipients`, the recipients defined in `config.yml` are used as email recipients.
```
    # If the recipients in 'config.yml' are defined as:
    events:
      example_mail_event_name:
        recipients:
          - "email@address.com"
          - "another@address.com"
        ...
    # the actual recipients will be 'email@address.com,another@address.com':
    echo -e "to: some@address.com\nGood day today." | aws_client. --default-recipients
```

### AWS region
To make sure the `boto3` client is initialized with the correct AWS SES region, add it to your `config.yml`.

Another option is to directly pass the parameter to the tool:
```
--region us-east-1
```

### Configure logwatch
When `logwatch` is installed, there will also be a daily cronjob by default, created in `/etc/cron.daily/00logwatch` on debian or `/etc/cron.daily/0logwatch` on RHEL/CentOS. Make sure the cronjob is configured with `--output mail`.

* On `debian/Ubuntu`:
    - There are 2 locations: `/usr/share/logwatch/default.conf/logwatch.conf` and `/usr/share/logwatch/dist.conf/logwatch.conf`.
    - `/usr/share/logwatch/dist.conf/logwatch.conf` is read after `/usr/share/logwatch/default.conf/logwatch.conf`.
* On `AmazonLinux/RHEL/CentOS`:
    - There is only `/usr/share/logwatch/default.conf/logwatch.conf`.

Configure `aws_mail.py` as email client application in the appropriate file (depending on your `config.yml`):
* `/usr/share/logwatch/dist.conf/logwatch.conf` on `debian/Ubuntu`.
* `/usr/share/logwatch/default.conf/logwatch.conf` on `AmazonLinux/RHEL/CentOS`.
```
MailTo = <email@address.com>
mailer = "/complete/path/to/venv/bin/aws_mail --region us-east-1"
```

*_Note_*:
* It is also possible toleave `sendmail` as `mailer` client and just create a symlink to `aws_mail.py` as described below.
* `aws_mail.py` ignores unknown cli arguments, the ones usually sent to `sendmail`.
* If you like to just use the recipients defined within `config.yml`, add the following option to the `mailer`:
```
mailer = "/complete/path/to/venv/bin/aws_mail --region us-east-1 --default-recipients"
```


### Configure tools relying on /usr/sbin/sendmail
Tools like:
* `unattended-upgrade` (debian)
* `cron`
    - `cron` will send out emails using `sendmail` in case of error logs in `/var/log/syslog` (`debian/Ubuntu`)/`/var/log/messages` (`AmazonLinux/RHEL/CentOS`).
    - `aws_mail` is configured to log `ERORR`s with imported modules only.

I could not find a place to actually configure the `mailer` client apart from changing the actual code.
So the only option left is to symlink `/usr/bin/sendmail` to `venv/bin/aws_mail`:
```
# Create symlink, remove existing file if necessary.
sudo ln -s /complete/path/to/venv/bin/aws_mail /usr/sbin/sendmail
```

*_Note_*:
* `aws_mail` ignores unknown cli arguments, the ones usually sent to `sendmail`.

*_Note_*:
* Recipients for both, `unattended-upgrade`and `cron`, can be configured simliar to `logwatch`:
    - `unattended-upgrade`
        ```
            # '/etc/apt/apt.conf.d/50unattended-upgrades'
            Unattended-Upgrade::Mail "email@address.com"
        ```
    - `cron`
        ```
            # Set in according crontab or cron file in '/etc/cron*'.
            MAILTO=email@address.com
        ```

### Development and dependencies
A local developemnt environment can be created the following way:
```
# Clone the repo.
python3 -m venv venv

# Install build dependencies.
venv/bin/pip install -r build_requirements.txt

# Check below for updating python dependencies.

# Install dependencies.
venv/bin/pip-sync --dry-run requirements.txt
venv/bin/pip-sync requirements.txt

# Run.
venv/bin/python -m aws_mail.aws_mail
```

Python dependencies can be added in `requirements.in`.

Please just run `./update_requirements.sh` to compile `requirements.txt` (using `pip-tools`) containing only pinned dependency versions eventually.


## Deployment

## Code style
The necessary configuration files for tools like:
* `flake8`
* `black`
* `pylint`
* `pre-commit`

are kept in the common reporitory `https://github.com/normoes/python_style_generalt`.
The tool `copier` can be used to get the latest version of those files.
By default the latest tag is retrieved, the option ` --vcs-ref=HEAD` retrieves from the most recent commit.
```
# Initial command, sets some values for the project.
copier --vcs-ref=HEAD copy  'git@github.com:normoes/python_style_general.git'  ./

# Update the files
copier --vcs-ref=HEAD update
```

*_Note_*:
* Local changes need to be committed to make `copier` work.
