# AI-Based Lost & Found Monitoring System with CCTV Integration

> Final Year Project

An AI-powered CCTV monitoring system designed to detect people and objects in real time, track their movement, and identify potentially unattended objects. The system automatically generates event snapshots and recorded video footage for later review through an interactive monitoring dashboard.

---

## Project Overview

The **AI-Based Lost & Found Monitoring System with CCTV Integration** combines computer vision, object detection, object tracking, and rule-based state analysis to monitor CCTV footage and identify potentially unattended belongings.

The system focuses on objects such as backpacks, handbags, and suitcases that may become unattended after being separated from nearby people. By continuously analyzing object movement and person-object proximity, the system determines whether an object should be considered potentially unattended.

Once an unattended-object condition is detected, the system automatically creates an event containing a snapshot and recorded video footage. These events can then be reviewed through the monitoring dashboard.

---

## Demo / Reference

A reference video demonstrating the system in action is available here:
[View Demo](https://drive.google.com/file/d/1NGMaObPkVK4Dh9x6J6HZlngZ2VCYFJD4/view?usp=sharing)

---

## How It Works

The system begins by receiving video from a webcam, recorded video, or CCTV/RTSP source. OpenCV processes the incoming video stream, while YOLOv8 performs real-time detection of people and relevant objects.

Detected objects are assigned persistent tracking IDs using ByteTrack, allowing the system to monitor their movement across frames. The tracking information is combined with object movement and person-object proximity analysis.

A rule-based state machine evaluates the object's condition and transitions it through different states, including **Attended**, **Potentially Unattended**, and **Unattended**.

When the system confirms an unattended-object event, it captures a snapshot and records the surrounding video footage, including relevant pre-event and post-event frames. The generated event is then made available through the monitoring dashboard for further review.

---

## Key Features

Real-time CCTV and video monitoring with support for webcam, recorded video, and CCTV/RTSP sources.

YOLOv8-based detection for people, backpacks, handbags, suitcases, and other configured objects.

ByteTrack-based object tracking for maintaining object identities across video frames.

Movement analysis and person-object proximity monitoring for determining object activity and separation.

Rule-based unattended-object state management for identifying potentially unattended situations.

Automatic event snapshot generation and event video recording with surrounding footage.

Live MJPEG monitoring feed with dynamic video source switching.

Event history and snapshot gallery for reviewing previously detected events.

Interactive monitoring dashboard for viewing live footage and generated security events.

---

## System Architecture

```text
                  ┌──────────────────────┐
                  │   Video Input Source │
                  │                      │
                  │ Webcam / CCTV / MP4  │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │    OpenCV Capture    │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │       YOLOv8         │
                  │   Object Detection   │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │      ByteTrack       │
                  │   Object Tracking    │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │    Object Memory     │
                  │   Movement Analysis  │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │    State Machine     │
                  │                      │
                  │      ATTENDED        │
                  │          ↓           │
                  │   POTENTIALLY        │
                  │    UNATTENDED        │
                  │          ↓           │
                  │     UNATTENDED       │
                  └──────────┬───────────┘
                             │
                       Event Detected
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
     ┌─────────────────┐          ┌─────────────────┐
     │ Snapshot (.jpg) │          │ Event Video     │
     │                 │          │ (.mp4)          │
     └────────┬────────┘          └────────┬────────┘
              │                            │
              └─────────────┬──────────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Monitoring Dashboard │
                 └──────────────────────┘
```

---

## Technology Stack

The system is built around **Python** and computer vision technologies, using **YOLOv8** for object detection, **ByteTrack** for object tracking, and **OpenCV** for video processing and stream handling.

The monitoring and event management components are integrated with an interactive dashboard that provides live monitoring, event history, snapshots, and recorded event footage.

---

## Event Detection Workflow

The monitoring process continuously evaluates detected objects and their surrounding environment. When an object is detected, its movement and relationship with nearby people are tracked over time.

The system first considers whether the object is associated with a nearby person. If the object becomes separated and remains in a relevant location for the configured conditions, its state can transition from **Attended** to **Potentially Unattended** and eventually to **Unattended**.

Once the final condition is reached, an event is generated automatically and the corresponding evidence is stored as a snapshot and video recording for later investigation.

---

## Dashboard

The monitoring dashboard provides a centralized interface for reviewing the system's activity.

It allows users to view the live monitoring feed, switch between available video sources, review detected events, browse generated snapshots, and access recorded event videos.

This provides a practical interface for monitoring CCTV environments and reviewing potentially unattended-object incidents.

---

## Applications

The system can be applied in environments where unattended belongings need to be monitored, including hospitals, railway stations, airports, educational institutions, shopping malls, offices, and other public or controlled spaces.

The system is designed as a monitoring and alert-support solution that can assist security personnel by automatically identifying events that may require human attention.

---

## Project Team

**Moin Farooqui**
**Yasir Qureshi**
**Abdul Kareem**
**Saad Mansoori**

---

## Acknowledgement

This project was developed as a final year project with the goal of exploring practical applications of computer vision, object detection, object tracking, and intelligent video monitoring.

Claude AI was used during development to assist with parts of the project, including documentation and code refinement.

---

## Connect With Me

**GitHub**
https://github.com/MoinFarooqui

**LinkedIn**
https://linkedin.com/in/moinfrqi

**Portfolio**
https://portfolio-seven-lilac-usgh240hmm.vercel.app

---
