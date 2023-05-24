#!/bin/bash

systemctl start vmware-networks-configuration.service
systemctl start vmware-networks.service
systemctl start vmware-usbarbitrator.service
