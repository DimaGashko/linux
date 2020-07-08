#!/bin/bash

tz1=Europe/Kiev
tz2=America/Los_Angeles

if [[ $(timedatectl show) == *Timezone=$tz1* ]]; then
   newTz=$tz2
else
   newTz=$tz1
fi

timedatectl set-timezone $newTz
