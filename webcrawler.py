from validators import url as url_validator
from validators.utils import ValidationFailure
from BeautifulSoup import BeautifulSoup
import urllib2
import re
from urlparse import urlparse
from utils import configure_and_get_logger
from data_store import InMemoryDataStore
from collections import deque


app_logger = configure_and_get_logger('common_loggers.log')
failure_logger = configure_and_get_logger('failure.log')


class Url(object):
    """
    Made a url obj for modularity and code reusablity.
    """

    def __init__(self, input_url):

        self._url = None
        self._url_host_name = None

        # for valid url will set self._url and self._url_host_name
        self.set_url(input_url)

    @property
    def url_str(self):
        return self._url

    @property
    def host_str(self):
        return self._url_host_name

    def is_valid_url(self, url=None):
        try:

            if not url:
                url = self._url

            # return True for all valid urls
            return url_validator(url)

        except ValidationFailure as e:

            app_logger.info("{} : Skipping since not a valid url".format(url))
            return False

        except Exception as e:

            app_logger.error("{} : Skipping as {}".format(url, e))
            return False

    def get_clean_url(self, input_url, base_host):

        url = ""
        host = ""

        try:
            oURL = urlparse(input_url)
        except Exception as e:
            failure_logger.exception(
                "URL:{}, status: exception , Error Msg:{}".format(input_url, error))
            return url, host

        if oURL.scheme == '':
            scheme = 'http'
        else:
            scheme = oURL.scheme

        if oURL.netloc:
            host = oURL.netloc
        elif base_host:
            host = base_host
        else:
            return url, host

        url = scheme + '://' + host + oURL.path

        return url, host

    def set_url(self, input_url, base_host=None):

        input_url, url_host = self.get_clean_url(input_url, base_host)

        if self.is_valid_url(input_url):
            self._url = input_url
            self._url_host_name = url_host

    def url_visited_success_msg(self):
        msg = "URL: {} : STATUS: success".format(self._url)
        return msg

    def url_visited_failure_msg(self):
        msg = "URL: {} : STATUS: failed".format(self._url)
        return msg


    def get_response_obj(self, base_url=None, base_host=None):
        '''
        Go to url and fetch the response obj
        '''

        if not base_url:
            base_url = self._url

        if not base_host:
            base_host = self._url_host_name

        if not base_url:
            return None

        try:

            response = urllib2.urlopen(base_url)

            return response

        except Exception as e:
            failure_logger.exception(
                "URL:{} ,STATUS: Error in get_response_obj, ERROR_MSG:{}".format(base_url, e))
            return None


class WebCrawler(object):
    '''
    NOTE1:
    webcrawler statrs crawling with root url and crawls each of the urls present in the response
    upto given depth

    NOTE2:
    Using InMemoryDataStore for datastore instead to any sql/nosql db
    '''

    def __init__(self, start_url="http://python.org/", max_depth=5,
     file_path="url_crawled_history.txt", data_store=InMemoryDataStore()):
        self._root_url = start_url
        self._max_depth = max_depth
        self._stored_url_file_path = file_path
        self._unique_url_to_visit = deque()
        self._datastore = data_store

    def run(self):

        # open file
        #NOTE: for now file handler is in "w" mode so it will rewrite on every run.
        with open(self._stored_url_file_path, 'w') as fh:

            # check if self._root_url is valid
            url_obj = Url(self._root_url)

            if not url_obj.url_str:

                failure_logger.exception("Invalid url to start crawling")

                # for console
                print "INVALID URL : Please provide a valid url to start crawling."

                return

            # start crawling with root url
            self.crawl(url_obj, fh)

        

    def is_url_visited(self, url):
        return self._datastore.get(url)


    def mark_url_visited(self, url):
        self._datastore.insert(url)


    def validate_and_handle_response_obj(self, response):
        '''
        Implement this method if need more validations on response.
        like response status 2XX, 3XX, 4XX, 5XX.

        Perform action on the basis of status code
        '''
        if not response:
            return "response is None"

        pass


    def perform_business_action(self, response):
        '''
        Need to write code according to bussiness requirements.
        I am not implementing this as this is usecase specific.
        '''
        pass


    def get_all_links_on_page(self, response):
        links = []
        try:
            html_page = response.read()
            soup = BeautifulSoup(html_page)
            for link in soup.findAll('a', attrs={'href': re.compile("^http://")}):
                links.append(link.get('href'))

        except Exception as e:
            failure_logger.exception(
                "URL:{}, Error: get_all_links_on_page raised exception , Error Msg:{}".format(response.url, e))

        return links

    def crawl(self, url_obj, fh, _depth=0):

        try:

            # get base host to help in making clean url

            base_host = url_obj.host_str
            base_url = url_obj.url_str

            if _depth > self._max_depth:  # if depth exceed maximum depth stop crawling further
                app_logger.info(
                    "URL:{}, STATUS: Skipping, Reason: reached maximum depth of crawling".format(base_url))
                return
            elif self.is_url_visited(base_url):  # web page already visited
                app_logger.info(
                    "URL:{}, STATUS: Skipping, Reason: already visited".format(base_url))
                return

            try:

                response = url_obj.get_response_obj(base_url, base_host)
                error = self.validate_and_handle_response_obj(response)

                if error:
                    app_logger.error(
                        "URL:{}, STATUS: Skipping, Reason:{}".format(base_url, error))
                    return

                # do some stuff according to requirement.
                self.perform_business_action(response)

                app_logger.info(url_obj.url_visited_success_msg())

                # mark url visited in datastore
                self.mark_url_visited(base_url)

            except Exception as e:
                failure_logger.exception(
                    "URL:{} , Action: Something went wrong in crawling, Error Msg:{}".format(base_url, e))
                return

            all_urls_on_page = self.get_all_links_on_page(response)

            for url in all_urls_on_page:
                url_obj = Url(url)

                if url_obj.url_str and not self.is_url_visited(url_obj.url_str):
                    self._unique_url_to_visit.append(url_obj)
                    fh.write(url_obj.url_str + '\n')

            while (self._unique_url_to_visit):
                url_obj = self._unique_url_to_visit.popleft()
                self.crawl(url_obj, fh, _depth+1)


        except Exception, e:
            failure_logger.exception(e)


if __name__ == "__main__":

    input_url = raw_input("Provide URL to crawl: ")
    input_depth = raw_input("Provide maximum depth to crawl: ")

    if input_depth.isdigit():
        input_depth = int(input_depth)
    else:
        input_depth = None

    if input_url and input_depth :
        wc = WebCrawler(start_url=input_url, max_depth=input_depth)
    elif input_url:
        wc = WebCrawler(start_url=input_url)
    elif input_depth :
        wc = WebCrawler(max_depth=input_depth)
    else:
        wc = WebCrawler()

        
    wc.run()