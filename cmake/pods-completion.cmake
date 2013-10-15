##
# Adds a bash completion script for a particular target.
# use as:
# pods_add_bash_completion( <target> <completion-script-filename> )
#     -- OR --
# pods_add_bash_completion( <target> COMPLETE <arguments-to-complete> )
# 
#
# This will install the completion script under 
# BUILD_PREFIX/bash-completion/<target>.completion
#
# Also, the completion script file will be configured and every @VAR@ 
# will be expanded according to the VAR in the CMake context.
# This means that *every* completion script should have line
# linke hte following:
#     complete <flags> @EXECUTABLE_INSTALL_PATH@/<target>
function( pods_add_bash_completion target_name completion_script_input_filename )

  # make sure we have at least 2 inputs
  if( ARGC LESS 2 )
    message( FATAL_ERROR "pods_add_bash_completion needs <target> <filename>")
  endif()

  if( ARGC GREATER 2 )
    if( ${completion_script_input_filename} STREQUAL "COMPLETE" )
      # this is ok
    else()
      message( FATAL_ERROR "pods_add_bash_completion needs <target> <filename> --OR-- <target> COMPLETE <args-to-complete>")
    endif()
  endif()

  # make sure we have the bash-completion/ directory setup
  file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/bash-completion/)
  #message(STATUS "ensured directory: ${CMAKE_BINARY_DIR}/bash-completion/")

  string(CONFIGURE "${CMAKE_BINARY_DIR}/bash-completion/${target_name}.completion" completion_script_output_filename )
  string(CONFIGURE "${CMAKE_INSTALL_PREFIX}/bash-completion/" completion_script_install_dir )

  # do file configuration if we have a file
  if( ARGC LESS 3 )

    # chekc that the comp[letion script actually at least
    # *uses* the @EXECUTABLE_INSTALL_PATH@ variable
    file(STRINGS ${completion_script_input_filename} found_string REGEX ".*\@EXECUTABLE_INSTALL_PATH\@.*")
    if( found_string STREQUAL "" )
      message(FATAL_ERROR "completion script did NOT include \@EXECUTABLE_INSTALL_PATH\@ inside of it! (script: ${completion_script_input_filename})")
    endif()
    
    # Ok, now simply configure the completion script
    configure_file( 
      ${completion_script_input_filename}
      ${completion_script_output_filename}
      @ONLY
      )
    
    #message( STATUS "configured file: ${completion_script_input_filename} TO: ${completion_script_output_filename}")

  else()

    # ok, we have a COMPLETE style, so configure the string
    string(CONFIGURE "complete ${ARGN} ${EXECUTABLE_INSTALL_PATH}/${target_name}" 
      complete_command )
    
    # now write out the file for hte completion using hte complete command
    file(WRITE ${completion_script_output_filename} 
      ${complete_command} )

  endif()

  # Tell the installation what to do
  install(FILES ${completion_script_output_filename}
    DESTINATION ${completion_script_install_dir} )

endfunction( pods_add_bash_completion )