from dataclasses import dataclass
from wsgiref import headers
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures
import threading
from queue import Queue, Empty
import time
import logging
from threading import Thread
from typing import List
import json
from coverage import results


class WebCrawler:
    def __init__(self, start_urls, max_pages, max_depth, max_workers,timeout):
        if start_urls is None:
            raise TypeError("start_urls cannot be None")
        if max_pages is None:
            raise TypeError("max_pages cannot be None")
        if max_depth is None:
            raise TypeError("max_depth cannot be None")
        if max_workers is None:
            raise TypeError("max_workers cannot be None")
        if timeout is None:
            raise TypeError("timeout cannot be None")

        if not isinstance(max_pages, int):
            raise TypeError("max_pages must be a number bigger or even than 1")
        if not isinstance(max_depth, int):
            raise TypeError("max_depth must be a number bigger than 1")
        if not isinstance(max_workers, int):
            raise TypeError("max_workers must be a 2 or bigger")
        if not isinstance(timeout, int):
            raise TypeError

        if max_pages is True or max_pages is False:
            raise TypeError("max_pages cannot be True or False")
        if max_depth is True or max_depth is False:
            raise TypeError("max_depth cannot be True or False")
        if max_workers is True or max_workers is False:
            raise TypeError("max_workers cannot be True or False")
        if timeout is True:
            #I set default time out on one because mot mustch pages have slower response than 1 but there are some exceptions
            self.timeout = 1
        elif timeout is False:
            #There is possibility that program will fail somewhere because som pages have slower response
            self.timeout = 0

        if max_pages < max_depth:
            self.max_pages = max_depth *2
        else:
            self.max_depth = max_depth

        self.start_urls = start_urls if isinstance(start_urls, list) else [start_urls]
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.max_workers = max_workers
        self.timeout = timeout

        if max_depth <= 0:
            self.max_depth = 10
        if max_depth >= 1000:
            self.max_depth = 100
        if max_workers <= 0:
            self.max_workers = 2
        if timeout < 0:
            self.timeout = 1

        self.url_queue = Queue()
        self.visited_urls = set()
        self.crawl_results = {}

        self.visited_lock = threading.Lock()
        self.results_lock = threading.Lock()
        self.page_count_lock = threading.Lock()

        self.total_pages_crawled = 0

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        for start_url in self.start_urls:
            self.url_queue.put((start_url, 0))

    def is_valid_url(self, url):

        try:
            parsed = urlparse(url)

            checks = [
                parsed.scheme in ['http', 'https'],
                url not in self.visited_urls,
                not url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webm', '.pdf', '.mp4')),
                len(url) < 300,
            ]

            return all(checks)

        except Exception as e:
            self.logger.warning(f"URL validation error for {url}: {e}")
            return False

    def extract_links(self, html_content, current_url):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []

            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(current_url, link['href'])

                if self.is_valid_url(absolute_url):
                    links.append(absolute_url)

            return links

        except Exception as e:
            self.logger.error(f"Link extraction error: {e}")
            return []

    def extract_page_info(self, html_content, url):

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            self.page_count_lock.acquire()
            page_info = {
                'id': self.total_pages_crawled,
                'url': url,
                'title': soup.title.string if soup.title else 'No Title',
                'headings': {
                    'h1': [h.get_text(strip=True) for h in soup.find_all('h1')],
                    'h2': [h.get_text(strip=True) for h in soup.find_all('h2')]
                },
                'text_length': len(soup.get_text()),
                'links_count': len(soup.find_all('a', href=True))
            }
            self.page_count_lock.release()

            return page_info

        except Exception as e:
            self.logger.error(f"Page info extraction error for {url}: {e}")
            return {'url': url, 'error': str(e)}

    def worker(self):
        while True:
            # Check if crawl limit reached
            with self.page_count_lock:
                if self.total_pages_crawled + (self.max_workers /4) >= self.max_pages:
                    break

            try:
                current_url, depth = self.url_queue.get(timeout=self.timeout)

                if depth > self.max_depth:
                    self.url_queue.task_done()
                    continue

                with self.visited_lock:
                    if current_url in self.visited_urls:
                        self.url_queue.task_done()
                        continue
                    self.visited_urls.add(current_url)

                try:
                    response = requests.get(current_url, timeout=self.timeout)

                    if response.status_code == 200:
                        page_info = self.extract_page_info(response.text, current_url)

                        self.page_count_lock.acquire()
                        self.total_pages_crawled += 1
                        self.logger.info(f"Crawled: {current_url}")
                        self.page_count_lock.release()

                        self.results_lock.acquire()
                        self.crawl_results[current_url] = page_info
                        self.results_lock.release()

                        discovered_links = self.extract_links(response.text, current_url)

                        for link in discovered_links:
                            self.url_queue.put((link, depth + 1))

                        time.sleep(0.5)

                except requests.RequestException as e:
                    self.logger.warning(f"Request failed for {current_url}: {e}")
                finally:
                    self.url_queue.task_done()
            except Empty:
                # No more URLs to process
                break

            except Exception as e:
                self.logger.error(f"Unexpected worker error: {e}")
                break
        time.sleep(1)


    def crawl(self):
        self.logger.info(f"Starting crawl for {self.start_urls}")

        # Create thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self.worker)
                for _ in range(self.max_workers)
            ]

            # Wait for all threads to complete
            concurrent.futures.wait(futures)

        self.logger.info(f"Crawl completed. Total pages: {self.total_pages_crawled}")
        return self.crawl_results

class findMatchingTitle(Thread):
    def __init__(self, from_id, to_id, wanted_word):
        Thread.__init__(self)
        self.from_id = from_id
        self.to_id = to_id
        self.wanted_word = wanted_word

    def find_word(self, title, wanted_word):
            title_low = title.lower()
            wanted_word_low = wanted_word.lower()

            if wanted_word_low in title_low:
                return True
            return False

    def find(self):
        found = 0
        i = 0
        for url, data in results.items():
            if self.from_id < i < self.to_id and self.find_word(data.get('title'), self.wanted_word):
                print("Wanted word is on row {} with title {} and url address {}.".format(i, data.get('title'), data.get('url')))
                found += 1
            i = i + 1
        if found == 0:
            print("This thread have not found title you are looking for.")

    def run(self):
        self.find()

class findMatchingHeader(Thread):
    def __init__(self, from_id, to_id, wanted_header):
        Thread.__init__(self)
        self.from_id = from_id
        self.to_id = to_id
        self.wanted_header = wanted_header

    def find_header(self, headers, wanted_header):
            wanted_header_low = wanted_header.lower()

            for header in headers:
                if wanted_header_low in header.lower():
                    return True
                return False

    def find(self):
        found = 0
        i = 0
        for url, data in results.items():
            if self.from_id < i < self.to_id and self.find_header(data.get('headers'), self.wanted_header):
                print("Wanted word is on row {} with title {} and url address {}.".format(i, data.get('title'), data.get('url')))
                found += 1
            i = i + 1
        if found == 0:
            print("This thread have not found title you are looking for.")

    def run(self):
        self.find()


class findMatchingTitleAndHeader(Thread):
    def __init__(self, from_id, to_id, wanted_title, wanted_header):
        Thread.__init__(self)
        self.from_id = from_id
        self.to_id = to_id
        self.wanted_title = wanted_title
        self.wanted_header = wanted_header

def search_specific(total_pages, num_workers, wanted_title, wanted_header):
    if total_pages % num_workers != 0:
        total_pages = num_workers * 10
    if not isinstance(total_pages, int):
        raise TypeError
    if not isinstance(num_workers, int):
        raise TypeError
    if not isinstance(wanted_title, str):
        raise TypeError
    if not isinstance(wanted_header, str):
        raise TypeError

    if total_pages < num_workers or total_pages < 0:
        total_pages = num_workers * 2
    if num_workers <= 0:
        num_workers = 2

    if total_pages is True or total_pages is False:
        total_pages = 100
    if num_workers is False or num_workers is True:
        num_workers = 2


    chunk_size = total_pages // num_workers
    threads = []

    for i in range(num_workers):
        from_id = i * chunk_size
        to_id = from_id + chunk_size if i < num_workers - 1 else total_pages
        if wanted_title == "":
            thread = findMatchingHeader(from_id, to_id, wanted_header)
            threads.append(thread)
            thread.start()
        if wanted_header == "":
            thread = findMatchingTitle(from_id, to_id, wanted_title)
            threads.append(thread)
            thread.start()
        else:
            thread = findMatchingTitleAndHeader(from_id, to_id,wanted_title, wanted_header)
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()


@dataclass
class CrawlerConfig:
    start_urls: List[str]
    max_pages: int
    max_depth: int
    max_workers: int
    timeout: int
    wanted_title: str
    wanted_header:str

    @classmethod
    def from_json(cls, json_file: str) -> 'Crawler':
        with open(json_file, 'r') as file:
            data = json.load(file)
            return cls(**data)

    def to_json(self, json_file: str) -> None:
        with open(json_file, 'w') as file:
            json.dump(self.__dict__, file, indent=4)


if __name__ == "__main__":
    loaded_config = CrawlerConfig.from_json('Crawler.json')
    crawler = WebCrawler(start_urls=loaded_config.start_urls,max_pages=loaded_config.max_pages,max_depth=loaded_config.max_depth,max_workers=loaded_config.max_workers, timeout=loaded_config.timeout)

    results = crawler.crawl()

    if not(loaded_config.wanted_title == "" and loaded_config.wanted_header == ""):
        search_specific(loaded_config.max_pages, loaded_config.max_workers, loaded_config.wanted_title, loaded_config.wanted_header)
    else:
        for url, data in results.items():
         print(f"id: {data.get('id')}")
         print(f"URL: {url}")
         print(f"Title: {data.get('title', 'No Title')}")
         print(f"Text Length: {data.get('text_length', 0)}")
         print(f"H1 Headings: {data.get('headings', {}).get('h1', [])}")
         print("\n")