
# Network Event Monitoring System (UDP-Based)

## Overview
This project is a distributed network event monitoring system that uses UDP sockets for communication between multiple clients (nodes) and a central server. The system collects real-time events such as heartbeats and status updates from clients and visualizes them through a web dashboard.

The goal of this project is to demonstrate concepts in networking, concurrent systems, and backend design.

---

## Features
- UDP-based client-server communication
- Real-time event streaming
- Multiple concurrent clients
- Heartbeat monitoring for node health
- Web dashboard for visualization
- Event logging and tracking
- Lightweight and scalable design

---

## Architecture

```bash

Clients (Nodes)
↓ (UDP Packets)
UDP Server (Event Collector)
↓
Backend Processing
↓
Web Dashboard (Visualization)

````

### Components

#### 1. UDP Client
- Sends periodic heartbeat messages
- Can simulate events (failures, alerts, etc.)
- Runs on multiple machines or instances

#### 2. UDP Server
- Listens for incoming UDP packets
- Handles multiple clients concurrently
- Parses and processes incoming events
- Maintains state of active nodes

#### 3. Backend Logic
- Processes events
- Tracks node status (alive/down)
- Stores recent activity

#### 4. Web Dashboard
- Displays active nodes
- Shows real-time updates
- Allows filtering/searching of nodes

---

## Tech Stack

- **Languages:** Python 
- **Networking:** UDP Sockets
- **Backend:** Event handlers
- **Frontend:** HTML/CSS
- **Tools:** Git

---

## How It Works

1. Clients send periodic heartbeat messages to the server.
2. Server receives UDP packets and identifies the sender.
3. Events are parsed and stored in memory.
4. Dashboard fetches or receives updates and displays:
   - Active nodes
   - Last seen timestamps
   - Event logs

---

## Running the Project

### 1. Start the Server

```bash
go run server.go
# or
python server.py
````

### 2. Start Clients

```bash
go run client.go
# or
python client.py
```

You can run multiple clients (even on different machines).

---

### 3. Start Web Dashboard

```bash
cd web
npm install
npm run dev
```

---

## Example Events

* HEARTBEAT
* NODE_UP
* NODE_DOWN
* ALERT

---

## Key Concepts Demonstrated

* Socket programming (UDP)
* Concurrent server handling
* Distributed systems basics
* Event-driven architecture
* Real-time monitoring systems

---

## Use Cases

* Monitoring distributed systems
* Learning networking concepts
* Simulating real-time event pipelines
* Backend systems practice

---


```
