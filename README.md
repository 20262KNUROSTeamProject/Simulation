# 시뮬레이션 개요
> 시뮬레이션은 가상의 센서 데이터를 생성하고 주행 명령이 정상적으로 작동하는 지 확인하기 위해 구현한다.

# 시뮬레이션 구현
### 사용하는 툴
- isaac sim(6.0.1)
- ros2(humble)
<br><br><br>

### 시스템 구성

**로봇 스펙**

NVIDIA의 jetbot을 에셋으로 사용하고 localizing을 위해 IMU 센서와 Lidar 센서를 추가함.

| 이름 | 단위 | 정량 |
| --- | --- | --- |
| maxLinearSpeed | m/s | - |
| maxAngularSpeed | rad/s | 3.0 |
| wheelDistance | m | 0.1125 |
| wheelRadius | m | 0.03 |

<br>

**데이터 인터페이스**

***msgs***

| 이름 | 역할 | 타입 | 파라미터 | 단위 | 추가 내용 |
| --- | --- | --- | --- | --- | --- |
| `/cmd_vel` | 로봇의 주행 명령 | `geometry_msgs/Twist` | `geometry_msgs/Vector3 linear`<br>`geometry_msgs/Vector3 angular` | m/s<br>rad/s | - |
| `/scan` | 라이다 센서 값 발행 | `sensor_msgs/msg/LaserScan` | - | - | intensity 데이터는 라이다 센서를 기준으로 시계 방향으로 진행 |
| `/imu` | imu 센서 값 발행 | `sensor_msgs/msg/Imu` | - | - | 칼만 필터 구현 시 활용 가능 |
|`/odom` | 초기 로봇 위치에서 현재 위치의 translation, rotation | - | - | - | - |
|`/tf` | odom to base_link, base_link to base_scan tf | - | - | - | - |

***actions***

***services***

# 결과

### How to run (Windows)

`src/run.bat` 파일 실행

### Isacc sim GUI 결과
<br>

![시범운전](data/imgs/drive.gif)

**Notice**

| slam toolbox 실행 시 base_frame 파라미터가 반드시 `base_link`로 되어있어야 함. odom_frame은 `odom`