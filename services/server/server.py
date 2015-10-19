import json
import logging
import requests
import requests.exceptions
import threading
import os
import sys
import time

if sys.version_info < (3, 3, 0):
    from requests import ConnectionError


# just for test
# TODO set it up so we can descend into dictionaries recursively (get it from cache or do a new request each time)
# TODO add timeout to post!
# Note: for convention, all urls will have trailing slash. So if you are appending to them, no beginning slash needed
class Server:
    _max_retries = 5            # max retries for post
    _req_timeout = 5                # timeout for requests
    _warn_results_count = 500   # when getting all results, will warn if there are >_warn_results_count results
    _max_results_count = 1000   # if # results > this, will throw error and return _max_results_count results

    _max_threads = 5            # if there are too many threads, will kill some of them. see postDataPoints
    _time_to_wait_for_threads = 0.1         # If we have too many threads, we will wait for this long and check again.
    _min_time_to_wait_for_threads = 0.1     # When we are decreasing the wait time, don't go lower than this
    _max_time_to_wait_for_threads = 2       # We don't want to wait for threads for longer than this

    _base_url = ''

    _post_datapoint_url = ''

    def __init__(self, base_url=None):
        # Get Server IP
        f = open(os.path.join('/home/pi/', 'server_ip.txt'), 'r')
        server_ip = f.readline();
        f.close()
        self._base_url = "http://" + server_ip.strip() + "/"
        self._post_datapoint_url = self._base_url + 'dataPoint/'        

        if base_url is not None:
            self._base_url = base_url
 
        # Authorization
        data = { 'username':'plantos', 'password':'plantos' }
        data_string = json.dumps(data)
        headers = {'Content-type': 'application/json'}
        req = requests.post(self._base_url+"auth/login/", params={"many": True}, data=data_string, headers=headers)
        if req.status_code != 200:
            logging.error('Failed to post %s: Code %d', data_string, req.status_code) 
        else:
            logging.debug('Acquired authentication token!')
        self._token = req.json()['key']
        
        # Get Urls       
        self._urls_dictby_name = self._getJsonWithRetry(self._base_url)
        self._cache_dictby_url = {}
        self._thread_list = []

        logging.debug('Server created, urls gotten!')

    # NOTE: this method will retry according to self._max_retries, so failure will take a little while
    # On start (first req), we may want the failure sooner, but this is a daemon, so we aren't worried about it
    def _getJsonWithRetry(self, url):
        """Private method to wrap getting json data with retries. Only gets single page, nothing fancy. See getJson
        :param url: url to get
        :return: json data returned from server
        """
        retry_count = 0
        req = None
        while retry_count < self._max_retries:
            try:
                #val = 'Token ' + self._token
                headers = {'Authorization': 'Token ' + self._token} 
                req = requests.get(url, timeout=self._req_timeout, headers=headers)
                if req.status_code == requests.codes.ok:
                    break
                logging.warning('Failed to get %s, status %d, retry %d' % (url, req.status_code, retry_count))
            except requests.exceptions.RequestException as e:
                logging.warning('Failed to get request for %s, RequestException: %s' % (url, e))
                pass        # Just pass it, we will include it as a retry ahead
            finally:
                retry_count += 1

        if retry_count >= self._max_retries:
            logging.error("Exceeded max connection retries for %s" % url)
            if req is not None:
                logging.error("Request failure reason: %s" % req.reason)
                raise ConnectionError(req.reason)
            else:
                logging.error("No request, no reason!")
                raise ConnectionError

        return req.json()

    # TODO check documentation
    def _cache(self, url, results):
        """Add the results to the cache
        :param url: url that was queried. If its an endpoint, will extract entries and cache both. If entry, just cache
        :param results: what you want to cache. dict or list
        """
        # TODO think about how to do this best. see ServerResourceLazyDict comments below
        self._cache_dictby_url[url] = results

        if type(results) == list:
            for item in results:
                if 'url' in item:
                    self._cache_dictby_url[item['url']] = item

    def getUrlByName(self, name: str):
        """Get the url for an endpoint. Uses the info in self_base_url
        :param name: name of the endpoint to get url for. Should be snake case, will be converted to lowerCamelCase
        :return: full url string
        """
        split_name = name.split('_')
        camel_name = split_name[0] + "".join(x.capitalize() for x in split_name[1:])
        return self._urls_dictby_name[camel_name]

    def getJson(self, url, allpages=True, update=True):
        """Get a url and return json. If update is False, will try to get it from local cache first.

        Assumes data is paginated, uses next to get all the data if allpages=True
        This method can get paginated lists or none paginated. Checks if 'results' is present to determine this
        :param url: url to get
        :param allpages: bool to specify whether to get all pages.
        Will get at most self._max_results_count, will warn num results>self._warn_results_count.
        :return: list of elements of whatever you are requesting
        """
        #

        # TODO test this
        if not update and url in self._cache_dictby_url:
            return self._cache_dictby_url[url]

        data = self._getJsonWithRetry(url)
        if 'results' not in data:                # If this is not paginated, it is a single result, return now
            self._cache(url, data)
            return data

        if not allpages or not data['next']:     # if we want just the first page or there is only one page, return now!
            self._cache(url, data['results'])
            return data['results']

        if data['count'] > self._warn_results_count:
            logging.warning('There are %d results for %s and you want all of them?!!', data['count'], url)

        results_list = []
        results_list += data['results']
        while data['next']:
            data = self._getJsonWithRetry(url)
            results_list += data['results']
            if len(results_list) >= self._max_results_count:
                logging.error('Got %d results for %s. Increase _max_results_count for more', len(results_list), url)
                break

        self._cache(url, results_list)
        return results_list

    def postDataPoints(self, values_list):
        """ Post data points to the server. Expects a list with timestamp, value, origin
        :param values_list: List of data points dicts, each should have timestamp, value, origin
        """
        # Check if any of the threads in the list are done and delete them
        self._thread_list = [th for th in self._thread_list if th.is_alive()]

        # Check if there are too many threads. If there are, sleep. Each time, increase the sleep time.
        # This way, we will slow down the main loop. NOTE: we decrease the time when len(threads) is ok
        # (so that we get more messages in between posting and don't post every new message)
        # In the main loop, if the sleep slows things down too much, we will see buffer overflow warnings there
        if len(self._thread_list) > self._max_threads:
            logging.warning('Too many post threads still alive! Sleeping for %d', self._time_to_wait_for_threads)
            if self._time_to_wait_for_threads < self._max_time_to_wait_for_threads:
                self._time_to_wait_for_threads += 0.05
            else:       # If we are already at the max sleep time, log warning
                logging.warning('Reached max sleep time for threads! Posting is too slow!')
            time.sleep(self._time_to_wait_for_threads)      # This should also give the threads some extra power
            self.postDataPoints(values_list)                # Call this fn again to check len, etc
            return
        else:   # If num threads is ok, decrease wait time. This prevents it from getting to max from occasional lag
            if self._time_to_wait_for_threads > self._min_time_to_wait_for_threads:
                self._time_to_wait_for_threads -= 0.01

        # we add the thread to the list
        t = threading.Thread(target=self._postDataPoints, args=(values_list,), name='post thread')
        t.start()
        self._thread_list.append(t)

    def _postDataPoints(self, values_list):
        if len(values_list) == 0:
            logging.debug('No new datapoints!')
        else:	
            headers = {'Authorization': 'Token ' + self._token}
            req = requests.post(self._post_datapoint_url, params={"many": True}, json=values_list, headers=headers)
            if req.status_code != 201:
                logging.error('Failed to post %s: Code %d', values_list, req.status_code)
            else:
                logging.debug('Posted %d datapoints, took %f secs. Datapoints: %s', len(values_list), req.elapsed.total_seconds(), values_list)


# TODO this implements caching, but we probably want it in the server... having it in both seems wasteful
# or maybe we can somehow use this to get recursive dictionary access to the json data so we don't have to do all the
# usual crap.
# If caching on server, need to think about how we can get multiple of the urls at once...
# ex if you get resourceProperty then resourceProperty/7
class ServerResourceLazyDict(dict):
    """Pass the name of the server resource to abstract. Will use the instance's ._server attribute to update

    This abstracts a resource on the server, ex resourceProperty, WITH caching!
    For example, we can get resourceProperty['http.../resourceProperty/1/'] on the Bot instance. This descriptor will
    check to see if this url is in the dict. If its not there, it will query the server and update the dict.
    :type name: str
    :type server: Server
    """
    def __init__(self, name, server, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.server = server
        self.base_url = self.server.getUrlByName(self.name)
        data_list = self.server.getJson(self.base_url)
        for item in data_list:
            self[item['url']] = item

    def __getitem__(self, url):
        try:
            return super().__getitem__(url)
        except KeyError:
            super().__setitem__(url, self.server.getJson(url))
        return super().__getitem__(url)

    # TODO should we get all the pages automatically? Prolly, otherwise things are weird. Or... ?
    def updateFromServer(self, url=None):
        """Update the dict. If url is specified, update that url and return. Else update all and return None
        :param url: url to update. If None, all existing will be updated
        :return: updated value if url is specified. else None
        """
        if url is None:     # if url not specified, update all
            for url in self.keys():
                self[url] = self.server.getJson(url)
        else:
            self[url] = self.server.getJson(url)
