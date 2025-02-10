# **AI-Powered Podcast Search & Fact-Checker API Documentation**

## **Introduction**

This FastAPI-based application enables users to fetch YouTube captions, search within them using FAISS indexing, summarize transcripts, and perform fact-checking on extracted context.

| Endpoint          | Method | Description                                                                 |
|-------------------|--------|-----------------------------------------------------------------------------|
| /fetch-captions   | POST   | Fetch YouTube captions, store them as a CSV, and generate a FAISS index for efficient search. |
| /search           | POST   | Search captions and return matching results with surrounding context and fact-checking. |
| /summarize        | GET    | Summarize the full video transcript for quick insights.                     |
| /fact-check       | POST   | Verify extracted context using AI and web crawling.                         |


## **📌 1️⃣ Fetch Captions API**

### **🔹Endpoint:**

`POST /fetch-captions/`

### **🔹Description:**

Fetches captions from a YouTube video, stores them in a CSV file, and builds a FAISS index for faster retrieval.

### **🔹Request Body (JSON):**
```
{
  "video_url": "https://youtu.be/MNeX4EGtR5Y?si=Gcp4EebogPkdNQXy"
}
```

### **🔹Response (JSON):
```
{
  "message": "Captions fetched and indexed successfully",
  "video_id": "MNeX4EGtR5Y"
}
```

### **🔹Error:**

-   **422**: Validation Error

## **📌 2️⃣ Search Captions API + Auto Fact-Check**

### **🔹Endpoint:**

`POST /search/`

### **🔹Description:**

Searches for a query within the video captions, retrieves the matching timestamp, provides surrounding context, and automatically performs fact-checking.

### **🔹Request Body (JSON):**
```
{
  "search_query": "C++ has steep learning curve.",
  "context_window": 10
}
```

🔹 Response (JSON):
```
{
  "message": "Captions searched successfully",
  "timestamp": "00:00:07",
  "caption": "steep  learning  curve  it  was  created  in",
  "full_context": "C++  a  statically  typed  compiled programming  language  famous  for  its widespread  use  in  software infrastructure  and  Infamous  for  its steep  learning  curve  it  was  created  in 1979  by  bej  Strauss  at  AT&T  Bell  Labs  he was  inspired  by  the  object-oriented nature  of  simula  but  needed  a  language with  a  high  performance  of  c  and  thus  C",
  "fact_check_results": {
    "refined_context": {
      "context": "C++ is a statically typed, compiled, object-oriented programming language famous for its widespread use in software infrastructure and infamous for its steep learning curve. It was created in 1979 by Bjarne Stroustrup at AT&T Bell Labs. He was inspired by the object-oriented nature of Simula but needed a language with a high performance of C and thus created C++.",
      "keywords": [
        "C++",
        "Statically Typed",
        "Compiled",
        "Object-Oriented",
        "Programming Language",
        "Software Infrastructure",
        "Steep Learning Curve",
        "Bjarne Stroustrup",
        "AT&T Bell Labs",
        "Simula",
        "High Performance",
        "C"
      ]
    },
    "articles": [],
    "verification_result": "```json\n{\n  \"factually_correct\": true,\n  \"confidence\": 1.0,\n  \"explanation\": \"The evidence supports the claim that C++ is a statically typed, compiled, object-oriented programming language, was created in 1979 by Bjarne Stroustrup at AT&T Bell Labs, and was inspired by Simula and C.\"\n}\n```\n\nThis response is based on the provided context, which accurately describes C++ as a statically typed, compiled, object-oriented programming language, its creation year and location, and its inspirations from Simula and C.",
    "resources": "FactCheck.org, Snopes, PolitiFact, Reuters Fact Check, AP Fact Check"
  }
}
```


### **🔹Error:**
-   **422**: Validation Error

## **📌 3️⃣ Summarize Video API**

### **🔹Endpoint:**

`GET /summarize/`

### **🔹Description:**

Summarizes the entire transcript of the video to provide a quick overview.

### **🔹Response (JSON):**

```
{
  "message": "Video summarized successfully",
  "summary": "Here's a concise summary of the transcript in bullet points:\n\n**Introduction to C++**\n\n* C++ is a statically typed, compiled programming language with a steep learning curve.\n* It was created in 1979 by Bjarne Stroustrup at AT&T Bell Labs.\n* C++ is designed as an extension of C, adding object-oriented features.\n\n**Features of C++**\n\n* Supports object-oriented programming with classes, polymorphism, encapsulation, and inheritance.\n* Provides low-level memory and hardware control like C, but with high-level abstractions.\n* Makes it harder to shoot yourself in the foot, but more severe when errors occur.\n\n**Getting Started with C++**\n\n* Install a C++ compiler like GCC or Clang.\n* Create a file ending in .cpp and include the iostream library for input/output.\n* Use the main function to start executing code.\n\n**Basic C++ Programming**\n\n* Use standard character output to print \"Hello, World!\".\n* Create a string variable as an array of characters or use the string type from the standard library.\n* Define attributes and methods in a class, which can be private or public.\n\n**Object-Oriented Programming in C++**\n\n* Define classes with attributes and methods.\n* Use constructors and destructors to run code when an object is created or destroyed.\n* Support inheritance to share logic throughout a program.\n* Use polymorphism with method overloading.\n\n**Memory Management in C++**\n\n* Use pointers and references to manage memory manually.\n* Use tools like unique pointers to manage memory in a safer and easier way.\n\n**Compiling and Running C++ Code**\n\n* Open a terminal and use a tool like Clang++ to compile the code.\n* Run the compiled code to execute the program."
}
```

### **🔹Errors:**

-   **500**: Internal server error

## **📌 4️⃣ Fact-Check API (Manual Check)**

### **🔹Endpoint:**

`POST /fact-check/`

### **🔹Description:**

Checks the accuracy of a given text against AI and web-crawled data.

### **🔹Request Body (JSON):**
```
{
  "context_text": "C++  a  statically  typed  compiled programming  language  famous  for  its widespread  use  in  software infrastructure  and  Infamous  for  its steep  learning  curve  it  was  created  in 1979  by  bej  Strauss  at  AT&T  Bell  Labs  he was  inspired  by  the  object-oriented nature  of  simula  but  needed  a  language with  a  high  performance  of  c  and  thus  C"
}
```

### **🔹Response (JSON):
```
{
  "message": "Fact-check completed",
  "results": {
    "refined_context": {
      "context": "C++ is a statically typed, compiled programming language famous for its widespread use in software infrastructure and infamous for its steep learning curve. It was created in 1979 by Bjarne Stroustrup at AT&T Bell Labs. He was inspired by the object-oriented nature of Simula but needed a language with a high performance of C and thus C++ was born.",
      "keywords": [
        "C++",
        "Statically typed",
        "Compiled programming language",
        "Software infrastructure",
        "Steep learning curve",
        "Bjarne Stroustrup",
        "AT&T Bell Labs",
        "Simula",
        "Object-oriented",
        "High performance",
        "C programming language"
      ]
    },
    "articles": [],
    "verification_result": "```json\n{\n  \"factually_correct\": true,\n  \"confidence\": 1.0,\n  \"explanation\": \"The provided context accurately describes C++ as a statically typed, compiled programming language with a steep learning curve, its widespread use in software infrastructure, and its creation by Bjarne Stroustrup at AT&T Bell Labs in 1979.\"\n}\n```\n\nThis response is based on the given context, which provides accurate information about C++. The confidence level is 1.0, indicating that the evidence fully supports the claim.",
    "resources": "FactCheck.org, Snopes, PolitiFact, Reuters Fact Check, AP Fact Check"
  }
}
```

### **🔹Errors:**

-   **500**: Internal server error
-  **422**: Validation Error