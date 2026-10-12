$env:ROS_DISTRO = "humble"
$env:RMW_IMPLEMENTATION = "rmw_fastrtps_cpp"

$env:PATH += ";C:\Users\User\env_isaaclab\Lib\site-packages\isaacsim\exts\isaacsim.ros2.core\humble\lib"

uv run python .\build_map.py