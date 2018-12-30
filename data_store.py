
class BaseDataStore(object):
    '''
    Simple persistence wrapper. Subclass this to use a different data store.
    '''
    def insert(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()
        
    def get(self):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()


class InMemoryDataStore(BaseDataStore):
    '''
    Sample implementation of BaseDataStore. Saves everything in-memory. Not recommended for production use.
    '''

    def __init__(self):
        self._datastore = set()

    def insert(self, url):
        self._datastore.add(url)

    def delete(self, url):
        self._datastore.remove(url)

    def get(self, url):
        if url in self._datastore:
            return url
