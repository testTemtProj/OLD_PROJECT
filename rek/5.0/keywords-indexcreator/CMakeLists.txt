project( getmyad-worker )
cmake_minimum_required( VERSION 2.6 )
set ( CMAKE_BUILD_TYPE Release )
add_definitions ( -Wall )

find_package(Boost
 COMPONENTS system filesystem thread 
	program_options date_time regex REQUIRED)

INCLUDE_DIRECTORIES( ${clucene-demo_SOURCE_DIR} )
INCLUDE_DIRECTORIES( ${clucene_SOURCE_DIR}/src/core )

include_directories (
	${CMAKE_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR}
	)
set ( EXECUTABLE_OUTPUT_PATH bin )
set ( keywords_indexcreator_HDRS
	src/pch.h
	src/DB.h
	src/OfferKeywords.h
	src/Core.h
	src/IndexCreatorService.h
	)

set ( keywords_indexcreator_SRCS
	
	src/DB.cpp
	src/Core.cpp
	src/main.cpp
	src/IndexCreatorService.cpp
	)
	
IF(CMAKE_COMPILER_IS_GNUCXX)
    ADD_DEFINITIONS(-std=c++0x)
ENDIF()

add_executable ( keywords_indexcreator ${keywords_indexcreator_SRCS} )
target_link_libraries ( keywords_indexcreator
	${Boost_FILESYSTEM_LIBRARY}
	${Boost_SYSTEM_LIBRARY}
	${Boost_PROGRAM_OPTIONS_LIBRARY}
	${Boost_DATE_TIME_LIBRARY}
	${Boost_THREAD_LIBRARY}
    ${Boost_REGEX_LIBRARY}
	glog
	mongoclient
	XmlRpc
	amqpcpp
	rabbitmq
	fcgi 
	GeoIP
	clucene-core clucene-shared clucene-contribs-lib${EXTRA_LIBS}
)
