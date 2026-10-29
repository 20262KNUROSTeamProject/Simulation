@echo off
setlocal

:: ROS2 및 RMW 설정
set ROS_DISTRO=humble
set RMW_IMPLEMENTATION=rmw_fastrtps_cpp

:: Isaac Sim ROS2 브리지 라이브러리 경로 추가
set PATH=%PATH%;C:\Users\User\env_isaaclab\Lib\site-packages\isaacsim\exts\isaacsim.ros2.core\humble\lib

:: 가상환경(env_isaaclab) 내부의 파이썬을 명시적으로 사용
set "PYTHON_EXE=C:\Users\User\env_isaaclab\Scripts\python.exe"

:: uv를 사용 중이시라면 아래와 같이 uv 환경 내 파이썬으로 직접 실행할 수도 있습니다.
:: (uv가 가상환경 내부를 바라보도록 강제)
uv run --python C:\Users\User\env_isaaclab\Scripts\python.exe build_map.py

:: 만약 uv 대신 일반 파이썬 명령어로 실행하고 싶다면 위 줄 대신 아래 줄의 주석을 해제하세요.
:: %PYTHON_EXE% build_map.py

pause
endlocal