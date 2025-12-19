package com.example.springbootragchat.api;

import java.util.HashMap;
import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

@RestController
@RequestMapping("/api/rag")
public class RagChatController {

    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${rag.python.url:http://localhost:11435/rag_query}")
    private String pythonRagUrl;

    @PostMapping("/chat")
    public Map<String, Object> chat(@RequestParam("message") String message) {
        return forwardToPython(message);
    }

    @PostMapping(value = "/chat", consumes = MediaType.APPLICATION_JSON_VALUE)
    public Map<String, Object> chatJson(@org.springframework.web.bind.annotation.RequestBody Map<String, Object> body) {
        Object msgObj = body.get("message") != null ? body.get("message") : body.get("query");
        String message = msgObj != null ? String.valueOf(msgObj) : "";
        return forwardToPython(message);
    }

    private Map<String, Object> forwardToPython(String message) {
        Map<String, Object> result = new HashMap<>();
        Map<String, String> req = new HashMap<>();
        req.put("query", message);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, String>> entity = new HttpEntity<>(req, headers);

        try {
            ResponseEntity<Map> resp = restTemplate.postForEntity(pythonRagUrl, entity, Map.class);
            Map body = resp.getBody();
            Object answer = (body != null) ? body.get("answer") : null;
            Object timestamp = (body != null) ? body.get("timestamp") : null;

            // Map to frontend contract: { response, conversationId, timestamp }
            result.put("response", answer != null ? answer : "No response from RAG.");
            result.put("conversationId", "");
            result.put("timestamp", timestamp != null ? timestamp : System.currentTimeMillis());
        } catch (RestClientException e) {
            result.put("response", "[Error] Could not reach Python RAG service: " + e.getMessage());
            result.put("conversationId", "");
            result.put("timestamp", System.currentTimeMillis());
        }
        return result;
    }
}


