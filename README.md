# Working hours analysis with Toggl, Python and Grafana

> Collects Toggl time tracking events and uses them to analyse the time you are working for different projects and clients

Since I am using Toggl Track (https://toggl.com/track/) for tracking the time I am working on privat and work related projects, the time records became much more accurate, what
helps me to evaluate my own work and productivity.

To perform analyses and create customized visualisations with python and Grafana, I used the Toggl API to collect the data. For calculating
the target hours I have to work each week and month I stored the information to my own vacation days in config.py and pulled the data to puplic
holidays from suitable web pages.


## Toggl API
