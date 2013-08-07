#!/bin/bash


# This script jsut takes as input a pod name and a url
# and creates a new pod which has a nice template Makefile for 
# downloading, untaring, and calling configure/make with the right --prefix

pod_name=$1
fetch_url=$2
prefix=LOCATION

# creat the pod
pods create-pod library $pod_name

# create the makefile
sed -e s!FFFFF!$fetch_url! -e s!NNNNN!$pod_name! $prefix/Makefile.template > $pod_name/Makefile

