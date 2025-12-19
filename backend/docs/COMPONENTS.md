# Spring Boot Backend - Component Details

## Components Breakdown

### 1. RagChatController
**File:** `src/main/java/com/example/springbootragchat/api/RagChatController.java`

**Responsibility:** HTTP endpoint handling and request routing

**Main Endpoints:**
- `POST /api/rag/chat` - Accepts chat messages, calls Python service, returns responses
- `GET /api/rag/health` - (Optional) Health check endpoint

**How it works:**
1. Receives query/message from React frontend
2. Validates request parameters
3. Makes HTTP POST request to Python FastAPI service (http://localhost:11435/rag_query)
4. Parses JSON response from Python service
5. Formats response for frontend consumption
6. Returns response with proper HTTP status codes

**Key Methods:**
- `chat(ChatRequest request)` - Main chat endpoint
- `callPythonService(String query)` - Calls Python RAG service

**Error Handling:**
- Validates query is not empty
- Catches HTTP exceptions from Python service
- Returns appropriate error messages

---

### 2. Spring Boot Application
**File:** `src/main/java/com/example/springbootragchat/SpringbootRagChatApplication.java`

**Responsibility:** Application initialization and configuration

**Duties:**
- Initializes Spring context
- Configures beans (RestTemplate, etc.)
- Starts embedded Tomcat server (port 8080)
- Loads application properties
- Enables auto-configuration features

**Key Annotations:**
- `@SpringBootApplication` - Main entry point
- `@EnableWebMvc` - Web layer configuration

---

### 3. Static Resource Serving
**Directory:** `src/main/resources/static/` or `src/main/resources/templates/`

**Purpose:** Serves React frontend build files

**Contains:**
- `index.html` - Entry point for React app
- React JavaScript bundles (compiled from frontend/)
- CSS stylesheets
- Static assets (images, fonts, etc.)

**How it works:**
1. Maven build copies React build output to this directory
2. Spring Boot serves these files on `http://localhost:8080/`
3. Frontend requests proxied to `/api/rag/*` endpoints for data

---

### 4. HTTP Client (RestTemplate)
**Purpose:** Makes HTTP requests to Python FastAPI service

**Configuration:**
```java
@Bean
public RestTemplate restTemplate() {
    return new RestTemplate();
}
```

**Usage in Controller:**
```java
ResponseEntity<Map> response = restTemplate.postForEntity(
    pythonServiceUrl,
    requestBody,
    Map.class
);
```

---

### 5. Data Models

**ChatRequest:**
```java
public class ChatRequest {
    private String query;
    private Integer k;  // Top-k results
}
```

**ChatResponse:**
```java
public class ChatResponse {
    private String answer;
    private String query;
    private Long timestamp;
}
```

---

## Dependencies

| Library | Purpose | Version |
|---------|---------|---------|
| spring-boot-starter-web | REST API framework | 3.x |
| spring-boot-starter-actuator | Health & monitoring endpoints | 3.x |
| jackson-databind | JSON processing | 2.x |
| spring-boot-starter-tomcat | Embedded web server | Built-in |

---

## Configuration Files

### `pom.xml`
Maven build configuration:
- Project metadata
- Dependency declarations
- Build plugins
- Java version (17+)

### `application.properties`
Runtime configuration:
```properties
# Server configuration
server.port=8080
server.servlet.context-path=/

# Python service URL
rag.python.url=http://localhost:11435/rag_query

# Logging
logging.level.root=INFO
logging.level.com.example.springbootragchat=DEBUG

# Application name
spring.application.name=springboot-rag-chat
```

---

## Build & Deployment

### Maven Phases
- `clean` - Remove previous build artifacts
- `package` - Build JAR file
- `install` - Install to local Maven repository

### JAR Execution
```bash
java -jar target/springboot-rag-chat-0.0.1-SNAPSHOT.jar
```

### Output
- Starts Tomcat on port 8080
- Loads application.properties
- Serves frontend on `http://localhost:8080/`
- Proxies requests to Python service (11435)
