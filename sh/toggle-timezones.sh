#!/bin/bash

tz1=Europe/Kiev
tz2=America/Los_Angeles

newTz=$tz1
if [[ $(timedatectl show) == *Timezone=$tz1* ]]; then
   newTz=$tz2
fi

sudo -n timedatectl set-timezone $newTz
