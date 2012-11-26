# Install library files into lib/${FLAVOR}, while skipping unneeded files
macro(install_lib path)
  if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    set(dest "${lib}")
  else()
    set(dest "${lib}/${MCCODE_NAME}")
  endif()

  install (
    DIRECTORY "${path}"
    DESTINATION "${dest}"
    PATTERN "Makefile*" EXCLUDE  # skip makefiles
    PATTERN "#*"        EXCLUDE  # skip backup files
    PATTERN ".*"        EXCLUDE  # skip hidden files
    PATTERN "*.out"     EXCLUDE  # skip binary files
  )
endmacro()


# Check whether we are being run through mkdist
macro(is_mkdist outvar)
  string(REPLACE "@" "_" TMP "@MCCODE_NAME@")
  string(COMPARE NOTEQUAL "${TMP}" "_MCCODE_NAME_" ${outvar})
endmacro()


# Setup McCode constants using either mkdist or SVN-defaults
macro(setup_mccode_mkdist FLAVOR)

  # Set 32-bit flags
  if(ARCH EQUAL 32)
    set(CMAKE_C_FLAGS  "-m32")
    set(CMAKE_C_LFLAGS "-m32")
  endif()
  message("Compiling for ${ARCH}-bit ${CMAKE_SYSTEM_NAME}")


  # Set macros
  if("${FLAVOR}" STREQUAL "mcstas")
    set(NAME             "McStas")

    set(FLAVOR           "mcstas")
    set(FLAVOR_UPPER     "MCSTAS")

    set(FLAVOR_FMT       "mcformat")

    set(FLAVOR_LIB       "nlib")
    set(MCCODE_LIBENV    "${FLAVOR_UPPER}")

    set(MCCODE_PARTICULE "neutron")
    set(MCCODE_PROJECT    1)

    set(MCCODE_PREFIX     "mc")
  endif()

  if("${FLAVOR}" STREQUAL "mcxtrace")
    set(NAME             "McXtrace")

    set(FLAVOR           "mcxtrace")
    set(FLAVOR_UPPER     "MCXTRACE")

    set(FLAVOR_FMT       "mxformat")

    set(FLAVOR_LIB       "xlib")
    set(MCCODE_LIBENV    "${FLAVOR_UPPER}")

    set(MCCODE_PARTICULE "xray")
    set(MCCODE_PROJECT   2)

    set(MCCODE_PREFIX     "mx")
  endif()


  set_property(DIRECTORY ${CMAKE_SOURCE_DIR} APPEND PROPERTY COMPILE_DEFINITIONS
    NAME="${NAME}" FLAVOR="${FLAVOR}" FLAVOR_UPPER="${FLAVOR_UPPER}"
    FLAVOR_FMT="${FLAVOR_FMT}" FLAVOR_LIB="${FLAVOR_LIB}"
    MCCODE_LIBENV="${MCCODE_LIBENV}" MCCODE_PARTICULE="${MCCODE_PARTICULE}"
    MCCODE_PROJECT=${MCCODE_PROJECT}
    )

  # Check for mkdist values
  is_mkdist(MKDIST)

  if(MKDIST)
    ## Set mkdist-provided version
    set(MCCODE_VERSION "@MCCODE_VERSION@")
    set(MCCODE_NAME "@MCCODE_NAME@")
    set(MCCODE_DATE "@MCCODE_DATE@")
    set(MCCODE_STRING "@MCCODE_STRING@")
    set(MCCODE_TARNAME "@MCCODE_TARNAME@")
  else()
    ## Set SVN-specific version
    set(MCCODE_VERSION "2.9999-svn")
    set(MCCODE_NAME "${NAME}")
    set(MCCODE_DATE "svn")
    set(MCCODE_STRING "${NAME} ${MCCODE_VERSION}, ${MCCODE_DATE}")
    set(MCCODE_TARNAME "${FLAVOR}")
  endif()


  # Set default installation paths
  foreach(name bin doc etc include lib man sbin share src)
    if(NOT(DEFINED ${name}))
      # The Windows platform installs everything in same dir
      if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
        set(${name} ".")
      else()
        set(${name} "${name}")
      endif()
    endif()
  endforeach()


  # Setup mccode name and paths
  set(MCCODE_NAME "${FLAVOR}-${MCCODE_VERSION}")

  if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    set(MCCODE_BIN "${CMAKE_INSTALL_PREFIX}/${MCCODE_NAME}/${MCCODE_NAME}")
    set(MCCODE_LIB "${CMAKE_INSTALL_PREFIX}/${MCCODE_NAME}/")
  else()
    set(MCCODE_BIN "${CMAKE_INSTALL_PREFIX}/${bin}/${MCCODE_NAME}")
    set(MCCODE_LIB "${CMAKE_INSTALL_PREFIX}/${lib}/${MCCODE_NAME}")
  endif()

  # Set instrument suffix (after compilation)
  if(NOT DEFINED OUT_SUFFIX)
    if(DEFINED EXE_SUFFIX)
      set(OUT_SUFFIX "${EXE_SUFFIX}")
    else()
      set(OUT_SUFFIX "out")
    endif()
  endif()

  # Helper for adding leading "."
  macro(add_dot name val)
    if(NOT DEFINED ${name} AND NOT ${val} STREQUAL "")
      set(${name} ".${val}")
    endif()
  endmacro()

  # Define suffix-macros that include a leading dot "."
  add_dot(DOT_EXE_SUFFIX "${EXE_SUFFIX}")
  add_dot(DOT_OUT_SUFFIX "${OUT_SUFFIX}")

  add_dot(DOT_PYTHON_SUFFIX "${PYTHON_SUFFIX}")
  add_dot(DOT_PERL_SUFFIX   "${PERL_SUFFIX}")


  # Add some special Windows/Unix CPACK configuration
  if(CMAKE_SYSTEM_NAME STREQUAL "Windows")

    # Fix installation root and folder (installs to ${ROOT}\${DIRECTORY})
    set(CPACK_NSIS_INSTALL_ROOT "C:")
    set(CPACK_PACKAGE_INSTALL_DIRECTORY "${FLAVOR}-${MCCODE_VERSION}")

    # Windows program files do not have any version-suffix
    set(PROGRAM_SUFFIX "")

  else()

    # Have CMake respect install prefix
    set(CPACK_SET_DESTDIR "ON")
    set(CPACK_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

    # Add "-VERSION" to all program files (executables)
    set(PROGRAM_SUFFIX "-${MCCODE_VERSION}")

  endif()


endmacro()