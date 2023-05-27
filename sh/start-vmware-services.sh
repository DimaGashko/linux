#!/bin/bash

sudo systemctl start vmware-networks-configuration.service
sudo systemctl start vmware-networks.service
sudo systemctl start vmware-usbarbitrator.service
