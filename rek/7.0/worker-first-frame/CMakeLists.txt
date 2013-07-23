project( getmyad-worker-first-frame )
cmake_minimum_required( VERSION 2.6 )
set ( CMAKE_BUILD_TYPE Release )
add_definitions ( -Wall )

find_package(Boost
 COMPONENTS system filesystem thread 
	program_options date_time regex REQUIRED)


include_directories (
	${CMAKE_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR}
	)
set ( EXECUTABLE_OUTPUT_PATH bin )
set ( getmyad-worker-first-frame_HDRS
	src/pch.h
	src/Informer.h
	src/DB.h
	src/Core.h
	src/FrameTemplate.h
	src/utils/UrlParser.h
	src/utils/base64.h
	src/utils/benchmark.h
	src/CgiService.h
	)

set ( getmyad-worker-first-frame_SRCS
	src/Informer.cpp
	src/DB.cpp
	src/Core.cpp
	src/FrameTemplate.cpp
	src/utils/UrlParser.cpp
	src/utils/base64.cpp
	src/main.cpp
	src/CgiService.cpp
	)
	
IF(CMAKE_COMPILER_IS_GNUCXX)
    ADD_DEFINITIONS(-std=c++0x)
ENDIF()

add_executable ( getmyad-worker-first-frame ${getmyad-worker-first-frame_SRCS} )
target_link_libraries ( getmyad-worker-first-frame
	${Boost_FILESYSTEM_LIBRARY}
	${Boost_SYSTEM_LIBRARY}
	${Boost_PROGRAM_OPTIONS_LIBRARY}
	${Boost_DATE_TIME_LIBRARY}
	${Boost_THREAD_LIBRARY}
    ${Boost_REGEX_LIBRARY}
	glog
	mongoclient
	amqpcpp
	rabbitmq
	fcgi 
)
