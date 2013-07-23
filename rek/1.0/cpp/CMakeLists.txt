project( getmyad-worker )
cmake_minimum_required( VERSION 2.6 )
set ( CMAKE_BUILD_TYPE Release )
add_definitions ( -Wall )

find_package(Boost
 COMPONENTS system filesystem thread 
	program_options date_time REQUIRED)


include_directories (
	${CMAKE_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR}
	)
set ( EXECUTABLE_OUTPUT_PATH bin )
set ( getmyad-worker_HDRS
	src/pch.h
	src/Rules.h
	src/Informer.h
	src/Campaign.h
	src/CampaignShowOptions.h
	src/DB.h
	src/RandomEntity.h
	src/Core.h
	src/Offer.h
	src/InformerTemplate.h
	src/utils/UrlParser.h
	src/utils/base64.h
	src/utils/GeoIPTools.h
	src/utils/benchmark.h
	src/CgiService.h
	)

set ( getmyad-worker_SRCS
	src/Rules.cpp
	src/Informer.cpp
	src/Campaign.cpp
	src/CampaignShowOptions.cpp
	src/DB.cpp
	src/RandomEntity.cpp
	src/Core.cpp
	src/Offer.cpp
	src/utils/UrlParser.cpp
	src/utils/base64.cpp
	src/main.cpp
	src/utils/GeoIPTools.cpp
	src/CgiService.cpp
	)
	
IF(CMAKE_COMPILER_IS_GNUCXX)
    ADD_DEFINITIONS(-std=c++0x)
ENDIF()

add_executable ( getmyad-worker ${getmyad-worker_SRCS} )
target_link_libraries ( getmyad-worker
	${Boost_FILESYSTEM_LIBRARY}
	${Boost_SYSTEM_LIBRARY}
	${Boost_PROGRAM_OPTIONS_LIBRARY}
	${Boost_DATE_TIME_LIBRARY}
	${Boost_THREAD_LIBRARY}
	glog
	mongoclient
	XmlRpc
	amqpcpp
	rabbitmq
	fcgi 
	GeoIP
)
