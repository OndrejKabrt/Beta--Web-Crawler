

# **Documentation: Web Crawler**

## **Overview**
The `WebCrawler` is a multithreaded web crawler designed to traverse web pages starting from a list of seed URLs. It extracts information such as titles, headers, text length, and links, storing the results in a structured format. Additional functionalities include searching for specific titles and headers using multi-threaded processing.

---

## **Modules and Dependencies**
- **Python Standard Libraries**:
  - `dataclasses`: Defines the `CrawlerConfig` for configuration management.
  - `queue`: Implements a thread-safe queue for URL management.
  - `concurrent.futures`: Manages multithreading for efficient crawling.
  - `threading`: Provides thread synchronization and custom thread creation.
  - `logging`: Enables logging for debugging and tracking.
  - `time`: Introduces delays to respect server responses.

- **Third-Party Libraries**:
  - `requests`: Handles HTTP requests for fetching web page content.
  - `bs4 (BeautifulSoup)`: Parses and extracts content from HTML.
  - `urllib.parse`: Handles URL parsing and manipulation.

---

## **Classes**

### **WebCrawler**
The core class for crawling websites.

#### **Initialization**
```python
def __init__(self, start_urls, max_pages, max_depth, max_workers, timeout)
```

### **WebCrawler**
```python
class CrawlerConfig:
    start_urls: List[str]
    max_pages: int
    max_depth: int
    max_workers: int
    timeout: int
    wanted_title: str
    wanted_header:str
```
# **Logging**
- Logs are printed to the console and include:
  - Timestamps
  - Log levels (e.g., `INFO`, `WARNING`, `ERROR`)
  - Descriptive messages
  
### **Example Log Output**
```plaintext
2024-12-20 14:55:00 - INFO: Starting crawl for ['https://example.com']
2024-12-20 14:55:05 - INFO: Crawled: https://example.com/page1
2024-12-20 14:55:10 - WARNING: Request failed for https://example.com/page2: TimeoutError
2024-12-20 14:55:15 - INFO: Crawl completed. Total pages: 50
```

### **Commands for activating program in virtual environment**
```plaintext
cd name_of_project_directory

#For creating virtual environment, needed just one time
python -m venv venv

#Activate virtual environment
venv\Scripts\activate

# Than you have to install packages taht are needed and are not in default python library
pip install requests
pip install beautifulsoup4
pip install coverage
pip install requests beautifulsoup4 coverage


```




