# Spring Boot Backend Architecture

## Overview
Spring Boot REST API gateway that connects React frontend to Python RAG service. Serves static frontend files and proxies API requests to the Python RAG service.

## Core Components

### 1. **Spring Boot Application**
- **Main Class:** `SpringbootRagChatApplication.java`
- **Port:** 8080
- **Framework:** Spring Boot 3.x
- **Purpose:** Serves frontend + Acts as API gateway to Python service

### 2. **REST Controller**
- **File:** `api/RagChatController.java`
- **Endpoints:** `/api/rag/chat` - Proxy to Python RAG service
- **Method:** POST
- **Purpose:** Routes user queries to Python service and returns responses

### 3. **Web Layer**
- **Directory:** `src/main/resources/static/` or `src/main/resources/templates/`
- **Purpose:** Serves static frontend files (React build output)

### 4. **Build Artifacts**
- **Target:** `target/springboot-rag-chat-0.0.1-SNAPSHOT.jar`
- **Purpose:** Packaged Spring Boot application for deployment

## Data Flow

```
React Frontend (Browser)
    ↓
Spring Boot (Port 8080)
    ↓
RagChatController (/api/rag/chat)
    ↓
Python FastAPI Service (Port 11435)
    ↓
RAG Query Processing (Vector Search + LLM)
    ↓
Response → Controller → Frontend
```

## Key Configuration

**Application Properties:** `src/main/resources/application.properties`
```properties
server.port=8080
rag.python.url=http://localhost:11435/rag_query
spring.application.name=springboot-rag-chat
```

This configuration is changeable for different deployment environments (development, staging, production).

## Dependencies

- **Spring Boot Web** - REST API framework
- **Spring Boot Actuator** - Health checks and monitoring
- **RestTemplate** - HTTP client for calling Python service
- **Jackson** - JSON serialization/deserialization
- **Tomcat** - Embedded application server

## Build & Run

### Build
```bash
mvn clean package
```

### Run
```bash
java -jar target/springboot-rag-chat-0.0.1-SNAPSHOT.jar
```

### Development
```bash
mvn spring-boot:run
```

## Project Structure

```
backend/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/example/springbootragchat/
│   │   │       ├── SpringbootRagChatApplication.java
│   │   │       └── api/
│   │   │           └── RagChatController.java
│   │   └── resources/
│   │       ├── application.properties
│   │       ├── static/          (Frontend build files)
│   │       └── templates/
│   └── test/
├── target/                       (Build output)
├── pom.xml                       (Maven configuration)
└── README.md
```
