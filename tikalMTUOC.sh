#!/bin/bash
"jdk-17.0.15+6-jre/bin/java" -cp "`dirname $0`/lib/*" net.sf.okapi.applications.tikal.Main "$@"
