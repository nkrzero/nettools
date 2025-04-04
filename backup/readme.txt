Prerequisites
Python: Version 3.x (e.g., 3.9 or higher) installed on your system.
Paramiko: A Python library for SSH (installation instructions below).

Input Files:
deviceip.txt: List of device IP addresses (one per line, e.g., 10.0.250.1).
commands.txt: List of commands to execute (one per line, e.g., show ip route).


*****************
# 711 jumpbox already has paramiko installed
pip install --user paramiko

***************************
How to run it after deviceip.txt and commands.txt are updated:

open CMD:
python backup.py