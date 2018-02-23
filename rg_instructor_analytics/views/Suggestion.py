from abc import ABCMeta, abstractmethod

class Norma():
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_query(self):
        """
        Return dictionary where key - name of filter parameter and value - label for the user.
        """
        pass
    