# 시뮬레이션 개요
> 시뮬레이션은 가상의 센서 데이터를 생성하고 주행 명령이 정상적으로 작동하는 지 확인하기 위해 구현한다.

# 시뮬레이션 구현
### 사용하는 툴
- isaac sim

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

<br><br><br>

**데이터 인터페이스**

***topic***

| 이름 | 역할 | 타입 | 파라미터 | 단위 | 추가 내용 |
| --- | --- | --- | --- | --- | --- |
| `/cmd_vel` | 로봇의 주행 명령 | `geometry_msgs/Twist` | `geometry_msgs/Vector3 linear`<br>`geometry_msgs/Vector3 angular` | m/s<br>rad/s | - |
| `/scan` | 라이다 센서 값 발행 | `sensor_msgs/msg/LaserScan` | - | - | intensity 데이터는 라이다 센서를 기준으로 시계 방향으로 진행 |
| `/imu` | imu 센서 값 발행 | `sensor_msgs/msg/Imu` | - | - | 칼만 필터 구현 시 활용 가능 |

### 결과
**Isacc sim GUI 결과**
<br><br>
![시범운전](data/imgs/drive.gif)