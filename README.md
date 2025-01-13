

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

### **How to start program
```plaintext
Open \dist\MyWebCrowler and than double clic Crawler.json and configure parametrs by your will
If you dont want to configure anything just double click MyWebCrowler.exe and take a look 
how Web Crawler crawl threw Novinky.cz
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

# Command that install all necessary packages at once
pip install requests beautifulsoup4 coverage

# Than you should open Crawler.json and set attributes there
notepad Crawler.json

{
  "start_urls": [ "url addres you want to search, or other page you want to search"],
    "max_pages": Enter number of pages you want to search in numbers,
    "max_depth": Enter maximal depth which crawler can search,
    "max_workers": Enter number of threads you want to run,
    "timeout": Enter time lenght that thread wait until page answer,
    "wanted_title": "Enter specific title you want to try to find",
    "wanted_header": "Enter specific header you want to try to find"
}

#After setting values in Crawler.json just run command

python MyWebCrowler.py



```




