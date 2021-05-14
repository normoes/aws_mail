# AWS mail client

This client uses the `boto3` library to send emails through AWS SES.
The AWS EC2 instance should have an instance role attached, which allows sending emails through AWS SES.

The tool is written to send everything piped into it from `stdin` as an email, considering the settings found in `config.yml`.

By default it just sends everything from `stdin`, i.e. `--tool all` (or leave this argument altogether).
If called with `--tool logwatch` it tries to parse and include only results from `logwatch`.

`aws_mail.py` ignores unknown cli arguments, e.g. the ones usually sent to `sendmail`.

## Installation
Deploy into a suitable directory, the following examples will use `/somewhere/`:
* `aws_mail.py`
* `config.yml`
* `requirements.txt`
* `build_requirements.txt`

```
# Create virtualenv.
cd /somewhere/
python3 -m venv venv
```

### Dependencies
Python dependencies can be added in `requirements.in`.

Please just run `./update_requirements.sh` to compile `requirements.txt` (using `pip-tools`) containing only pinned dependency versions eventually.

```
# Install build dependencies.
/somewhere/venv/bin/pip install -r build_requirements.txt

# Install dependencies.
/somewhere/venv/bin/pip-sync --dry-run requirements.txt
/somewhere/venv/bin/pip-sync requirements.txt
```

### Code style
The necessary configuration files for tools like:
* `flake8`
* `black`
* `pylint`
* `pre-commit`

are kept in the common reporitory `https://github.com/normoes/python_style_generalt`.
The tool `copier` can be used to get the latest version of those files.
By default the latest tag is retrieved, the option ` --vcs-ref=HEAD` retrieves from the most ecent commit.
```
# Initial command, sets some values for the project.
copier --vcs-ref=HEAD copy  'git@github.com:normoes/python_style_general.git'  ./

# Update the files
copier --vcs-ref=HEAD update
```

*_Note_*:
* Local changes need to be committed to make `copier` work.

## Configuration
Email settings can be configured in `config.yml`.
This file is expected to be located witihn the same drecoty as `aws_mali.py`.

The file `aws_mail.py` needs ot be executable:
```
chmod +x aws_mail.py
```

Also, change the shebang of `aws_mal.py` to the python installed witihn the `virtualenv`:
```
#!/somewhere/venv/bin/python
```
This ensures the prepared python environment execute the script.

Before running te script set the correct AWS region (according to yur AWS SES SMTP settings):
```
export export AWS_DEFAULT_REGION=us-east-1
```


### logwatch
When `logwatch` is installed, there will also be a daily cronjob by default, created in `/etc/cron.daily/00logwatch` on debian or `/etc/cron.daily/0logwatch` on RHEL/CentOS.

* On `debian/Ubuntu`:
    - There are 2 locations: `/usr/share/logwatch/default.conf/logwatch.conf` and `/usr/share/logwatch/dist.conf/logwatch.conf`.
    - `/usr/share/logwatch/dist.conf/logwatch.conf` is read after `/usr/share/logwatch/default.conf/logwatch.conf`.
* On `AmazonLinux/RHEL/CentOS`:
    - There is only `/usr/share/logwatch/default.conf/logwatch.conf`.

Configure `aws_mail.py` as email client application in the appropriate file:
* `/usr/share/logwatch/dist.conf/logwatch.conf` on `debian/Ubuntu`.
* `/usr/share/logwatch/default.conf/logwatch.conf` on `AmazonLinux/RHEL/CentOS`.
```
mailer = "/somewhere/aws_mail.py --tool logwatch --region us-east-1"
```

### Tools relying on /usr/sbin/sendmail
Tools like:
* `unattended-upgrade` (debian)
* `cron`
    - `cron` will send out emails using `sendmail` in case of error logs in `/var/log/syslog` (`debian/Ubuntu`)/`/var/log/messages` (`AmazonLinux/RHEL/CentOS`).
    - `aws_mail.py` is configured to log `ERORR`s with imported modules only.

I could not find a place to actually configure the `mailer` client, so the only option left is to symlink `/usr/bin/sendmail` to `aws_mail.py`:
```
sudo ln -s /somewhere/app_.py /usr/sbin/sendmail
```

*_Note_*:
* `aws_mail.py` ignores unknown cli arguments, the ones usually sent to `sendmail`.

## Usage
* With `logwatch`:
    ```
        # '-E' to preserve environment variables.
        sudo -E /usr/sbin/logwatch --output mail --format text --archives --detail 10 --mailto root --range yesterday
    ```
* Everything else:
    ```
        echo "Good day today." | /somewhere/aws_client.py [--tool all --debug]
    ```


## Deployment
