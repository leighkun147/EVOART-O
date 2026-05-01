cmake_minimum_required(VERSION 3.8)
project(evoart_bringup)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch worlds scripts
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
