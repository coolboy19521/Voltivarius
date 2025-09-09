# Voltivarius
> Our team name comes from our electric's two big obsessions. Electronics (Volt) and classic music (Ivarius).

[![YouTube - Race & Installing Videos](https://img.shields.io/badge/YouTube-▶️%20Race_&_Installing_Videos-df3e3e?logo=youtube)](https://www.youtube.com/playlist?list=PLiso-udvas0o-0Et_wnVIpQN-5FDyN6-4)

<img src="media/nizest.png" alt="Logo" width="500">

**This README.md file contains our team report on all electronic components used, required software and mechanical design of our robot.**

<table cellspacing="0" cellpadding="0" style="margin:0; padding:0; border-collapse:collapse;">
  <tr>
    <td style="margin:0; padding:0;"><img src="t-photos/funny.jpg" height="300"><br></td>
    <td><img src="t-photos/official.jpg" height="300"><br></td>
  </tr>
</table>

Our team consists of **Əhməd Qəmbərli** (Coding, Planning strategy, [ehmedqemberli09](mailto:ehmedqemberli09@gmail.com), rightmost in the official photo), **Melisa Yıldız** (General Design, [melisa.17.yildiz](mailto:melisa.17.yildiz@gmail.com), center in the official photo) and **Eyüp Şenal** (Electronics, Mechanics, Printing, Market research for used materials, [arduinoaz2022](mailto:arduinoaz2022@gmail.com), leftmost in the official photo).

### Table of contents

- [Introduction](#introduction)
- [Report of used materials](#report-of-used-materials)
  - [Design materials](#design-materials)
  - [Electronic materials](#electronic-materials)
- [Robot setup](#robot-setup)
  - [Printing 3D pieces](#printing-3d-pieces)
- [Programming Environment Setup](#programming-environment-setup)
  - [Raspberry OS configuration](#raspberry-os-configuration)
  - [Installing used modules](#installing-used-modules)
- [Explanation of Strategy](#explanation-of-strategy)
- [Photos & Videos of robot](#photos--videos-of-robot)


## Introduction

We started working 2-3 months prior to the local competition. All the details are provided in the report below.

Our robot is called “miav”. Miav is a ROS2-based four-wheeled mobile robot developed on the Raspberry Pi 5 platform. It also has a lidar sensor and a gyro sensor, which it uses to avoid obstacles and make accurate turns.

## Report of used materials
### Design materials

We designed all the parts of the robot we built using SolidWorks. First, we modeled the components one by one and then assembled them, which allowed us to both preview the final look and avoid surprises during the actual assembly. Thanks to the exploded view, we could clearly see all the internal parts of the robot and easily plan how everything would fit together.

### Electronic materials

**Raspberry Pi 5 (Main Controller):** The central processing unit running the ROS-based software. It collects data from all sensors and generates motor and servo commands.

**RRC Lite Controller (Motor Controller):** Controls the encoder motor and servo motor. It converts commands from the Raspberry Pi into motor/servo movements and sends feedback data back to the Pi.

**Encoder DC Motor:** Provides forward and backward motion. Through the encoder, it sends speed and position feedback to the Raspberry Pi via the RRC Lite controller.

**Servo Motor:** Handles robot turns, with the servo angle controlled via the RRC Lite controller.

## Robot setup
### Printing 3D pieces

You can find all design materials inside the models folder. Colors of the components are up to you to choose as they don't effect the behaviour of our robot.

## Programming Environment setup
### Raspberry OS Configuration
>Make sure to insert an SD card of size at least 16GB to your computer. We will use it as our destination for installation.

We are using Ubuntu Server 24.04.3 LTS (64-bit) as our primary OS in Raspberry Pi. You can flash this OS any way you want but recommended way is to use [Raspberry Pi Imager tool](https://www.raspberrypi.com/software/) from the official website.

![Raspberry Pi Imager](media/Imager.PNG)

After choosing the device click to "Choose OS". Then `Other general-purpose OS` > `Ubuntu` > `Ubuntu Server 24.04.3 LTS (64-bit)`

![Ubuntu Server 24.04.3 LTS (64-bit)](media/OS.PNG)

>Ubuntu Server 24.04.3 LTS (64-bit) is the latest server release of Ubuntu. Yet it is already supporting a wide variety of Raspberry Pi versions you can also install another release of Ubuntu Server if you need. But the recommended release is Ubuntu Server 24.04.3 LTS (64-bit) as we were testing with it.

>P.S. Raspberry Pi OS is not working for this project as we will be installing `ROS2 Jazzy` (which is not supportted in Raspberry Pi OS).

Now to Configure the OS you should press `Ctrl` `Shift` `X` / `⌘` `Shift` `X`. Under the `General` tab set up hostname, username and password; configure wireless LAN and also set the locale settings. Then switch to `Services` tab and enable SSH and password authentication. Save your configuration and now you are ready to install the OS (press `Next` button).

After doing the installation it is most recommended to run commands:
```bash
$ sudo apt update
$ sudo apt upgrade
```
### Installing used modules
You need to build packages `rpicam-apps` and `libcamera` from source. Also make sure to install `ROS2 Jazzy` on your Raspberry Pi. After installing `ROS2 Jazzy` install `camera_ros`, `rplidar_ros` ros packages. Now you are ready to run our code.

## Explanation of Strategy

![Diagram of Strategy](media/Diagram_Future_Engineers.png)
## Photos & Videos of robot
<table cellspacing="0" cellpadding="0" style="margin:0; padding:0; border-collapse:collapse;">
  <tr>
    <td align="center" colspan="2">
      <img src="v-photos/right.jpg" height="300"><br>
      <b>Right</b>
    </td>
    <td align="center" colspan="2">
      <img src="v-photos/left.jpg" height="300"><br>
      <b>Left</b>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="v-photos/up.jpg" height="300"><br>
      <b>Up</b>
    </td>
    <td align="center">
      <img src="v-photos/front.jpg" height="300"><br>
      <b>Front</b>
    </td>
    <td align="center">
      <img src="v-photos/back.jpg" height="300"><br>
      <b>Back</b>
    </td>
    <td align="center">
      <img src="v-photos/down.jpg" height="300"><br>
      <b>Down</b>
    </td>
  </tr>
</table>

[![YouTube - Open Challange](https://img.shields.io/badge/YouTube-▶️%20Open_Challange-df3e3e?logo=youtube)](https://www.youtube.com/watch?v=AVoUPSBA6hs)
[![YouTube - Obstacle Challange](https://img.shields.io/badge/YouTube-▶️%20Obstacle_Challange-df3e3e?logo=youtube)](https://www.youtube.com/watch?v=ACrtoZzavfY)