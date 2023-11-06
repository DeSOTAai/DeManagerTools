#!/bin/bash
echo "4">__launch_flag__
handshake=false
while : ; do
  lauch_flag_raw=$(<__launch_flag__)
  if [ $? -ne 0 ]; then
    if $handshake ; then exit ; fi
    sleep 2
    continue
  fi
  lauch_flag=${lauch_flag_raw##*( )}
  if [ $lauch_flag -eq 3 ] || [ $lauch_flag -eq 2 ]; then
    handshake=true
    cd __exe_dir__
    __exe_path__
    res=$?
    if [ $res -eq 0 ]; then
      echo "0"> __launch_flag__
      exit
    fi
    echo "1"> __launch_flag__
    if [ $lauch_flag -eq 2 ]; then
      exit
    fi
  fi
  sleep 2
done
