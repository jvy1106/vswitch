# VSwitch - Easy way to turn on/off entire AWS environments

##installing vswitch

vswitch is a python package. It is recommended to use virtualenv.

### steps to install

create a virutal environment to install
<pre>
virtualenv venv --distribute
</pre>

activate environment
<pre>
source venv/bin/activate
</pre>

install repo
<pre>
git clone git@github.com:jvy1106/vswitch.git
</pre>

<pre>
cd vswitch
</pre>

build/install vswitch package
<pre>
pip install -I .
</pre>

note: we are using the dot because we are in the same dir as setup.py

##configuring your environments

to create an environment just edit/create .vswitch.yml config file

<pre>

aws-settings:
    region: us-west-2
    aws_access_key_id: REDACT
    aws_secret_access_key: REDACT

environments:
    staging:
        instances:
            - i-6b051860
            - i-1673a3ad
            - i-c54644ce
        loadbalancers:
            STAGE-LB0:
                - i-6b051a60

    dev:
        instances:
            - i-2a65a521
            - i-066bab0d
            - i-56e2a45d
        loadbalancers:
            DEV-LB0:
                - i-ba8d76ad
            DEV-LB1:
                - i-54c9a95f
</pre>

just add the ec2 instance id in the list. Or create a new environment by creating a new list


##web interface
http://localhost:8888

##command line

to list environments
<pre>
ubuntu@server:~$ vswitch --list
available environments:
 - dev
 - staging
</pre>

to get stats on an environment
<pre>
ubuntu@server:~$ vswitch --status staging
Instance Id	Name		status
i-2a65a521	STAGE queue1	running
i-066bba0d	STAGE worker1	running
i-56a2e45d	STAGE worker2	running
</pre>

turn off environment
<pre>
ubuntu@server:~$ vswitch --stop staging
</pre>

turn on environment
<pre>
ubuntu@server:~$ vswitch --start staging
</pre>

##crontab

<pre>
#turn off staging and dev environments at 7pm PDT
0 2 * * * vswitch --stop staging
0 2 * * * vswitch --stop dev

#turn on dev every morning at 7am PDT
0 14 * * * vswitch --start dev
</pre>

##todo
 - clean up logging so it can be installed globally and not require a virtualenv
 - release to pypi for easy install
 - better handle adding things to the loadbalancer current implementation kind of hacky
