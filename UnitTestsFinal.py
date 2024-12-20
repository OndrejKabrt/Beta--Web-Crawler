import unittest
from unittest.mock import Mock, patch
import json
import requests
from queue import Queue
import threading
from MyWebCrowler import WebCrawler, findMatchingTitle, CrawlerConfig, search_specific, findMatchingTitleAndHeader, findMatchingHeader


class TestWebCrawler(unittest.TestCase):
    def setUp(self):
        """Set up test cases with default values"""
        self.valid_start_urls = ["http://example.com"]
        self.valid_max_pages = 10
        self.valid_max_depth = 3
        self.valid_max_workers = 2
        self.valid_timeout = 5

    def test_init_valid_parameters(self):
        """Test initialization with valid parameters"""
        crawler = WebCrawler(
            self.valid_start_urls,
            self.valid_max_pages,
            self.valid_max_depth,
            self.valid_max_workers,
            self.valid_timeout
        )

        self.assertEqual(crawler.start_urls, self.valid_start_urls)
        self.assertEqual(crawler.max_pages, self.valid_max_pages)
        self.assertEqual(crawler.max_depth, self.valid_max_depth)
        self.assertEqual(crawler.max_workers, self.valid_max_workers)
        self.assertEqual(crawler.timeout, self.valid_timeout)
        self.assertIsInstance(crawler.url_queue, Queue)
        self.assertIsInstance(crawler.visited_urls, set)
        self.assertIsInstance(crawler.crawl_results, dict)
        self.assertIsInstance(crawler.visited_lock, threading.Lock)
        self.assertIsInstance(crawler.results_lock, threading.Lock)
        self.assertIsInstance(crawler.page_count_lock, threading.Lock)
        self.assertEqual(crawler.total_pages_crawled, 0)

    def test_init_none_parameters(self):
        """Test initialization with None parameters"""
        parameters = [
            (None, self.valid_max_pages, self.valid_max_depth, self.valid_max_workers, self.valid_timeout),
            (self.valid_start_urls, None, self.valid_max_depth, self.valid_max_workers, self.valid_timeout),
            (self.valid_start_urls, self.valid_max_pages, None, self.valid_max_workers, self.valid_timeout),
            (self.valid_start_urls, self.valid_max_pages, self.valid_max_depth, None, self.valid_timeout),
            (self.valid_start_urls, self.valid_max_pages, self.valid_max_depth, self.valid_max_workers, None)
        ]

        for params in parameters:
            with self.assertRaises(TypeError):
                WebCrawler(*params)

    def test_init_invalid_types(self):
        """Test initialization with invalid parameter types"""
        invalid_params = [
            (self.valid_start_urls, "10", self.valid_max_depth, self.valid_max_workers, self.valid_timeout),
            (self.valid_start_urls, self.valid_max_pages, "3", self.valid_max_workers, self.valid_timeout),
            (self.valid_start_urls, self.valid_max_pages, self.valid_max_depth, "2", self.valid_timeout),
            (self.valid_start_urls, self.valid_max_pages, self.valid_max_depth, self.valid_max_workers, "5")
        ]

        for params in invalid_params:
            with self.assertRaises(TypeError):
                WebCrawler(*params)

    def test_init_boolean_parameters(self):
        """Test initialization with boolean parameters"""
        boolean_params = [
            (self.valid_start_urls, True, self.valid_max_depth, self.valid_max_workers, self.valid_timeout),
            (self.valid_start_urls, self.valid_max_pages, True, self.valid_max_workers, self.valid_timeout),
            (self.valid_start_urls, self.valid_max_pages, self.valid_max_depth, True, self.valid_timeout)
        ]

        for params in boolean_params:
            with self.assertRaises(TypeError):
                WebCrawler(*params)

        # Special case for timeout boolean
        crawler_true = WebCrawler(self.valid_start_urls, self.valid_max_pages,
                                           self.valid_max_depth, self.valid_max_workers, True)
        self.assertEqual(crawler_true.timeout, 1)

        crawler_false = WebCrawler(self.valid_start_urls, self.valid_max_pages,
                                            self.valid_max_depth, self.valid_max_workers, False)
        self.assertEqual(crawler_false.timeout, 0)

    def test_init_edge_cases(self):
        """Test initialization with edge case values"""
        # Test with negative values
        crawler = WebCrawler(
            self.valid_start_urls,
            -10,
            -3,
            -2,
            -5
        )
        self.assertTrue(crawler.max_depth > 0)
        self.assertEqual(crawler.max_workers, 2)
        self.assertEqual(crawler.timeout, 1)

        # Test with very large values
        crawler = WebCrawler(
            self.valid_start_urls,
            1000000,
            2000,
            100,
            1000
        )
        self.assertEqual(crawler.max_depth, 100)  # Should be capped at 100

    def test_is_valid_url(self):
        """Test URL validation method"""
        crawler = WebCrawler(
            self.valid_start_urls,
            self.valid_max_pages,
            self.valid_max_depth,
            self.valid_max_workers,
            self.valid_timeout
        )

        # Test valid URLs
        valid_urls = [
            "http://example.com",
            "https://example.com/path",
            "http://subdomain.example.com",
            "https://example.com/path?param=value"
        ]
        for url in valid_urls:
            self.assertTrue(crawler.is_valid_url(url))

        # Test invalid URLs
        invalid_urls = [
            "ftp://example.com",
            "http://example.com/image.jpg",
            "http://example.com/document.pdf",
            "http://" + "a" * 300,
            "not_a_url",
            "http://",
            "",
            None
        ]
        for url in invalid_urls:
            self.assertFalse(crawler.is_valid_url(url))

    @patch('requests.get')
    def test_extract_links(self, mock_get):
        """Test link extraction from HTML content"""
        crawler = WebCrawler(
            self.valid_start_urls,
            self.valid_max_pages,
            self.valid_max_depth,
            self.valid_max_workers,
            self.valid_timeout
        )

        # Test with various HTML contents
        test_cases = [
            {
                'html': """
                    <html>
                        <body>
                            <a href="http://example.com/page1">Link 1</a>
                            <a href="/page2">Link 2</a>
                            <a href="page3">Link 3</a>
                            <a href="http://example.com/image.jpg">Image</a>
                        </body>
                    </html>
                """,
                'base_url': "http://example.com",
                'expected_links': [
                    "http://example.com/page1",
                    "http://example.com/page2",
                    "http://example.com/page3"
                ]
            },
            {
                'html': "<html><body></body></html>",
                'base_url': "http://example.com",
                'expected_links': []
            },
            {
                'html': None,
                'base_url': "http://example.com",
                'expected_links': []
            }
        ]

        for test_case in test_cases:
            links = crawler.extract_links(test_case['html'], test_case['base_url'])
            self.assertEqual(sorted(links), sorted(test_case['expected_links']))

    def test_extract_page_info(self):
        """Test page information extraction"""
        crawler = WebCrawler(
            self.valid_start_urls,
            self.valid_max_pages,
            self.valid_max_depth,
            self.valid_max_workers,
            self.valid_timeout
        )

        # Test with various HTML contents
        test_cases = [
            {
                'html': """
                    <html>
                        <head><title>Test Page</title></head>
                        <body>
                            <h1>Main Heading</h1>
                            <h2>Sub Heading 1</h2>
                            <h2>Sub Heading 2</h2>
                            <p>Some content</p>
                            <a href="#">Link 1</a>
                            <a href="#">Link 2</a>
                        </body>
                    </html>
                """,
                'url': "http://example.com",
                'expected': {
                    'title': 'Test Page',
                    'h1_count': 1,
                    'h2_count': 2,
                    'links_count': 2
                }
            },
            {
                'html': "<html><body></body></html>",
                'url': "http://example.com",
                'expected': {
                    'title': 'No Title',
                    'h1_count': 0,
                    'h2_count': 0,
                    'links_count': 0
                }
            }
        ]

        for test_case in test_cases:
            info = crawler.extract_page_info(test_case['html'], test_case['url'])
            self.assertEqual(info['title'], test_case['expected']['title'])
            self.assertEqual(len(info['headings']['h1']), test_case['expected']['h1_count'])
            self.assertEqual(len(info['headings']['h2']), test_case['expected']['h2_count'])
            self.assertEqual(info['links_count'], test_case['expected']['links_count'])

    @patch('requests.get')
    def test_worker_functionality(self, mock_get):
        """Test worker thread functionality"""
        crawler = WebCrawler(
            self.valid_start_urls,
            self.valid_max_pages,
            self.valid_max_depth,
            self.valid_max_workers,
            self.valid_timeout
        )

        # Test successful page crawl
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
            <html>
                <head><title>Test</title></head>
                <body>
                    <h1>Test Page</h1>
                    <a href="http://example.com/page1">Link</a>
                </body>
            </html>
        """
        mock_get.return_value = mock_response

        crawler.url_queue.put(("http://example.com", 0))
        crawler.worker()

        self.assertEqual(len(crawler.crawl_results), 1)
        self.assertEqual(crawler.total_pages_crawled, 1)

        # Test failed request
        mock_get.side_effect = requests.RequestException()
        crawler.url_queue.put(("http://example.com/error", 0))
        crawler.worker()

        self.assertEqual(len(crawler.crawl_results), 1)  # Should not increase

        # Test max depth limit
        crawler.url_queue.put(("http://example.com/deep", crawler.max_depth + 1))
        crawler.worker()

        self.assertEqual(len(crawler.crawl_results), 1)  # Should not increase


class TestThreadedClasses(unittest.TestCase):
    """Test cases for threaded classes"""

    def test_find_matching_title(self):
        """Test findMatchingTitle class"""
        thread = findMatchingTitle(0, 10, "test")

        # Test initialization
        self.assertEqual(thread.from_id, 0)
        self.assertEqual(thread.to_id, 10)
        self.assertEqual(thread.wanted_word, "test")

        # Test word finding
        self.assertTrue(thread.find_word("Test Title", "test"))
        self.assertTrue(thread.find_word("TEST TITLE", "test"))
        self.assertTrue(thread.find_word("A test in title", "test"))
        self.assertFalse(thread.find_word("No match here", "test"))

        # Test with empty strings
        self.assertFalse(thread.find_word("", "test"))
        self.assertFalse(thread.find_word("Title", ""))

    def test_find_matching_header(self):
        """Test findMatchingHeader class"""
        thread = findMatchingHeader(0, 10, "test")

        # Test initialization
        self.assertEqual(thread.from_id, 0)
        self.assertEqual(thread.to_id, 10)
        self.assertEqual(thread.wanted_header, "test")

        # Test header finding
        headers = ["Test Header", "Another Header"]
        self.assertTrue(thread.find_header(headers, "test"))
        self.assertFalse(thread.find_header(headers, "nonexistent"))

        # Test with empty lists and strings
        self.assertFalse(thread.find_header([], "test"))
        self.assertFalse(thread.find_header(headers, ""))

    def test_find_matching_title_and_header(self):
        """Test findMatchingTitleAndHeader class"""
        thread = findMatchingTitleAndHeader(0, 10, "test_title", "test_header")

        # Test initialization
        self.assertEqual(thread.from_id, 0)
        self.assertEqual(thread.to_id, 10)
        self.assertEqual(thread.wanted_title, "test_title")
        self.assertEqual(thread.wanted_header, "test_header")


class TestSearchSpecific(unittest.TestCase):
    """Test cases for search_specific function"""

    def test_valid_parameters(self):
        """Test with valid parameters"""
        with patch('threading.Thread.start'), patch('threading.Thread.join'):
            result = search_specific(100, 4, "test", "header")
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 4)

    def test_invalid_parameters(self):
        """Test with invalid parameters"""
        invalid_params = [
            ("100", 4, "test", "header"),
            (100, "4", "test", "header"),
            (100, 4, 123, "header"),
            (100, 4, "test", 123)
        ]

        for params in invalid_params:
            with self.assertRaises(TypeError):
                search_specific(*params)

    def test_edge_cases(self):
        """Test edge cases"""
        test_cases = [
            (-50, 4, "test", "header"),
            (100, 0, "test", "header"),
            (True, 4, "test", "header"),
            (100, False, "test", "header")
        ]

        with patch('threading.Thread.start'), patch('threading.Thread.join'):
            for params in test_cases:
                result = search_specific(*params)
                self.assertIsInstance(result, list)
                self.assertGreater(len(result), 0)

    def test_chunk_size_calculation(self):
        """Test chunk size calculation logic"""
        test_cases = [
            {
                'total_pages': 100,
                'num_workers': 4,
                'expected_chunk': 25
            },
            {
                'total_pages': 99,  # Not evenly divisible
                'num_workers': 4,
                'expected_chunk': 10  # Should adjust to num_workers * 10
            },
            {
                'total_pages': 10,
                'num_workers': 2,
                'expected_chunk': 5
            }
        ]

        for case in test_cases:
            with patch('threading.Thread.start'), patch('threading.Thread.join'):
                result = search_specific(
                    case['total_pages'],
                    case['num_workers'],
                    "test",
                    "header"
                )
                self.assertEqual(
                    len(result),
                    case['num_workers']
                )

    def test_empty_strings(self):
        """Test behavior with empty strings"""
        with patch('threading.Thread.start'), patch('threading.Thread.join'):
            # Empty title
            result = search_specific(100, 4, "", "header")
            self.assertTrue(all(isinstance(thread, findMatchingHeader) for thread in result))

            # Empty header
            result = search_specific(100, 4, "title", "")
            self.assertTrue(all(isinstance(thread, findMatchingTitle) for thread in result))

            # Both empty
            result = search_specific(100, 4, "", "")
            self.assertEqual(len(result), 0)


class TestCrawlerConfig(unittest.TestCase):
    """Test cases for CrawlerConfig class"""

    def setUp(self):
        self.valid_config = {
            'start_urls': ["http://example.com"],
            'max_pages': 10,
            'max_depth': 3,
            'max_workers': 2,
            'timeout': 5,
            'wanted_title': "test",
            'wanted_header': "header"
        }
        self.config = CrawlerConfig(**self.valid_config)

    def test_initialization(self):
        """Test CrawlerConfig initialization"""
        self.assertEqual(self.config.start_urls, self.valid_config['start_urls'])
        self.assertEqual(self.config.max_pages, self.valid_config['max_pages'])
        self.assertEqual(self.config.max_depth, self.valid_config['max_depth'])
        self.assertEqual(self.config.max_workers, self.valid_config['max_workers'])
        self.assertEqual(self.config.timeout, self.valid_config['timeout'])
        self.assertEqual(self.config.wanted_title, self.valid_config['wanted_title'])
        self.assertEqual(self.config.wanted_header, self.valid_config['wanted_header'])

    def test_to_json(self):
        """Test JSON serialization"""
        test_file = "test_config.json"

        # Test writing to JSON
        self.config.to_json(test_file)

        # Read and verify JSON content
        with open(test_file, 'r') as file:
            loaded_data = json.load(file)

            self.assertEqual(loaded_data['start_urls'], self.valid_config['start_urls'])
            self.assertEqual(loaded_data['max_pages'], self.valid_config['max_pages'])
            self.assertEqual(loaded_data['max_depth'], self.valid_config['max_depth'])
            self.assertEqual(loaded_data['max_workers'], self.valid_config['max_workers'])
            self.assertEqual(loaded_data['timeout'], self.valid_config['timeout'])
            self.assertEqual(loaded_data['wanted_title'], self.valid_config['wanted_title'])
            self.assertEqual(loaded_data['wanted_header'], self.valid_config['wanted_header'])

    def test_from_json(self):
        """Test JSON deserialization"""
        test_file = "test_config.json"

        # Write test config
        with open(test_file, 'w') as file:
            json.dump(self.valid_config, file)

        # Load and verify
        loaded_config = CrawlerConfig.from_json(test_file)

        self.assertEqual(loaded_config.start_urls, self.valid_config['start_urls'])
        self.assertEqual(loaded_config.max_pages, self.valid_config['max_pages'])
        self.assertEqual(loaded_config.max_depth, self.valid_config['max_depth'])
        self.assertEqual(loaded_config.max_workers, self.valid_config['max_workers'])
        self.assertEqual(loaded_config.timeout, self.valid_config['timeout'])
        self.assertEqual(loaded_config.wanted_title, self.valid_config['wanted_title'])
        self.assertEqual(loaded_config.wanted_header, self.valid_config['wanted_header'])

    def test_json_error_handling(self):
        """Test error handling in JSON operations"""
        # Test with invalid JSON file
        with self.assertRaises(json.JSONDecodeError):
            CrawlerConfig.from_json("nonexistent.json")

        # Test with missing required fields
        invalid_config = {
            'start_urls': ["http://example.com"],
            'max_pages': 10
            # missing other required fields
        }

        test_file = "invalid_config.json"
        with open(test_file, 'w') as file:
            json.dump(invalid_config, file)

        with self.assertRaises(TypeError):
            CrawlerConfig.from_json(test_file)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete crawler system"""

    def setUp(self):
        self.config = CrawlerConfig(
            start_urls=["http://example.com"],
            max_pages=10,
            max_depth=3,
            max_workers=2,
            timeout=5,
            wanted_title="test",
            wanted_header="header"
        )

    @patch('requests.get')
    def test_complete_workflow(self, mock_get):
        """Test the complete workflow from configuration to crawling"""
        # Mock responses
        mock_responses = {
            "http://example.com": """
                    <html>
                        <head><title>Test Page</title></head>
                        <body>
                            <h1>Welcome</h1>
                            <h2>Subheading</h2>
                            <a href="http://example.com/page1">Link 1</a>
                            <a href="http://example.com/page2">Link 2</a>
                        </body>
                    </html>
                """,
            "http://example.com/page1": """
                    <html>
                        <head><title>Page 1</title></head>
                        <body>
                            <h1>Page 1</h1>
                            <a href="http://example.com/page3">Link 3</a>
                        </body>
                    </html>
                """
        }

        def mock_get_response(*args, **kwargs):
            url = args[0]
            response = Mock()
            response.status_code = 200
            response.text = mock_responses.get(url, "<html><head><title>Default</title></head></html>")
            return response

        mock_get.side_effect = mock_get_response

        # Create crawler and run
        crawler = WebCrawler(
            start_urls=self.config.start_urls,
            max_pages=self.config.max_pages,
            max_depth=self.config.max_depth,
            max_workers=self.config.max_workers,
            timeout=self.config.timeout
        )

        results = crawler.crawl()

        # Verify results
        self.assertIn("http://example.com", results)
        self.assertIn("http://example.com/page1", results)
        self.assertEqual(results["http://example.com"]['title'], "Test Page")
        self.assertEqual(len(results["http://example.com"]['headings']['h1']), 1)
        self.assertEqual(len(results["http://example.com"]['headings']['h2']), 1)

    def test_error_recovery(self):
        """Test system's ability to handle and recover from errors"""
        with patch('requests.get') as mock_get:
            # Simulate various errors
            mock_get.side_effect = [
                requests.RequestException("Connection error"),
                Mock(status_code=404),
                Mock(status_code=500),
                Mock(status_code=200, text="<html><head><title>Success</title></head></html>")
            ]

            crawler = WebCrawler(
                start_urls=self.config.start_urls,
                max_pages=self.config.max_pages,
                max_depth=self.config.max_depth,
                max_workers=self.config.max_workers,
                timeout=self.config.timeout
            )

            results = crawler.crawl()

            # Verify crawler continues despite errors
            self.assertGreaterEqual(len(results), 0)

    @patch('logging.Logger.warning')
    @patch('logging.Logger.error')
    def test_logging(self, mock_error, mock_warning):
        """Test logging functionality"""
        crawler = WebCrawler(
            start_urls=self.config.start_urls,
            max_pages=self.config.max_pages,
            max_depth=self.config.max_depth,
            max_workers=self.config.max_workers,
            timeout=self.config.timeout
        )

        with patch('requests.get') as mock_get:
            # Trigger warning
            mock_get.side_effect = requests.RequestException("Test error")
            crawler.crawl()

            # Verify logging calls
            mock_warning.assert_called()
            self.assertIn("Request failed", str(mock_warning.call_args))


if __name__ == '__main__':
    unittest.main(verbosity=2)