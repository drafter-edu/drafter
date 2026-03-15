from typing import Optional

class EnvVars:
    def __init__(self, source):
        self._source = source
        self._result = {}
        
    def get_string_if_exists(self, source_key: str, target_key: Optional[str] = None):
        if source_key in self._source:
            self._result[target_key or source_key] = self._source[source_key]
            
    def get_string_list_if_exists(self, source_key: str, target_key: Optional[str] = None, delimiter: str = ";"): 
        if source_key in self._source:
            self._result[target_key or source_key] = self._source[source_key].split(delimiter)

    def get_bool_if_exists(self, source_key: str, target_key: Optional[str] = None):
        if source_key in self._source:
            value = self._source[source_key].lower()
            self._result[target_key or source_key] = value in ("1", "true", "yes")
            
    def get_int_if_exists(self, source_key: str, target_key: Optional[str] = None, raise_error: bool = False):
        if source_key in self._source:
            try:
                self._result[target_key or source_key] = int(self._source[source_key])
            except ValueError:
                if raise_error:
                    raise

            
    def as_dict(self):
        return self._result