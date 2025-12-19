package com.example.springbootragchat.web;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class ChatPageController {
    @GetMapping({"/", "/chat"})
    public String chat() {
        // If a built frontend exists in `static/index.html`, forward to it.
        return "forward:/index.html";
    }
}


