#!/bin/bash

# get directory of script
DIR="$( cd "$( dirname "$0" )" && pwd )"

# assuming a local guacmole version is located properly
#LOCAL_GUACAMOLE="$DIR/../../../guacamole"
#LOCAL_AVANGO="$DIR/../../../avango"

# if not, this path will be used
GUACAMOLE=/opt/guacamole/new_renderer
AVANGO=/opt/avango/new_renderer

# third party libs
export LD_LIBRARY_PATH=/opt/boost/boost_1_55_0/lib:/opt/zmq/current/lib:/opt/Awesomium/lib:/opt/pbr/inst_cb/lib

# schism
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/schism/current/lib/linux_x86

# avango
export LD_LIBRARY_PATH="$LOCAL_AVANGO/lib":$AVANGO/lib:$LD_LIBRARY_PATH:/opt/pbr/inst_cb/lib:/opt/Awesomium/lib
export PYTHONPATH=$AVANGO/lib/python3.4

# guacamole
export LD_LIBRARY_PATH="$LOCAL_GUACAMOLE/lib":$GUACAMOLE/lib:$LD_LIBRARY_PATH


# run daemon
python3 ./daemon.py > /dev/null &
#python3 daemon.py

# run program
cd "$DIR" && python3 ./main.py

# kill daemon
kill %1
