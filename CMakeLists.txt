cmake_minimum_required(VERSION 2.6.0)

# pull in the pods macros. See cmake/pods.cmake for documentation
set(POD_NAME pods-utils)
include(cmake/pods.cmake)
include(cmake/pods-completion.cmake)


# install the pod-run shell script
install( PROGRAMS src/pod-run
    DESTINATION
    bin )
pods_add_bash_completion( pod-run src/pod-run.completion )


