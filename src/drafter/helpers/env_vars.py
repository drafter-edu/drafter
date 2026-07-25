"""Selective extraction and typed conversion of environment variables."""


class EnvVars:
    """Extract and convert values from an environment-like mapping.

    Each `get_*_if_exists` method looks up a key in the source mapping and,
    if present, stores the (possibly converted) value in an internal result
    dictionary. The accumulated results are retrieved with `as_dict`.

    Attributes:
        _source: Mapping of string keys to string values to read from.
        _result: Accumulated extracted values keyed by target name.
    """

    def __init__(self, source):
        """Initialize with a source mapping and an empty result store.

        Args:
            source: Mapping of string keys to string values (e.g. os.environ).
        """
        self._source = source
        self._result = {}

    def get_string_if_exists(self, source_key: str, target_key: str | None = None):
        """Store the raw string value for a key if it exists in the source.

        Args:
            source_key: Key to look up in the source mapping.
            target_key: Key to store the value under in the result; defaults
                to source_key when not provided.
        """
        if source_key in self._source:
            self._result[target_key or source_key] = self._source[source_key]

    def get_string_list_if_exists(
        self, source_key: str, target_key: str | None = None, delimiter: str = ";"
    ):
        """Store a delimited value as a list of strings if the key exists.

        Args:
            source_key: Key to look up in the source mapping.
            target_key: Key to store the value under in the result; defaults
                to source_key when not provided.
            delimiter: String used to split the value into list items.
        """
        if source_key in self._source:
            self._result[target_key or source_key] = self._source[source_key].split(
                delimiter
            )

    def get_bool_if_exists(self, source_key: str, target_key: str | None = None):
        """Store a value interpreted as a boolean if the key exists.

        The value is truthy when it case-insensitively equals "1", "true",
        or "yes"; any other value is stored as False.

        Args:
            source_key: Key to look up in the source mapping.
            target_key: Key to store the value under in the result; defaults
                to source_key when not provided.
        """
        if source_key in self._source:
            value = self._source[source_key].lower()
            self._result[target_key or source_key] = value in ("1", "true", "yes")

    def get_int_if_exists(
        self,
        source_key: str,
        target_key: str | None = None,
        raise_error: bool = False,
    ):
        """Store a value converted to an integer if the key exists.

        Values that cannot be converted are silently skipped unless
        raise_error is set.

        Args:
            source_key: Key to look up in the source mapping.
            target_key: Key to store the value under in the result; defaults
                to source_key when not provided.
            raise_error: Whether to re-raise the conversion error instead of
                skipping the value.

        Raises:
            ValueError: If the value is not a valid integer and raise_error
                is True.
        """
        if source_key in self._source:
            try:
                self._result[target_key or source_key] = int(self._source[source_key])
            except ValueError:
                if raise_error:
                    raise

    def get_float_if_exists(
        self,
        source_key: str,
        target_key: str | None = None,
        raise_error: bool = False,
    ):
        """Store a value converted to a float if the key exists.

        Values that cannot be converted are silently skipped unless
        raise_error is set.

        Args:
            source_key: Key to look up in the source mapping.
            target_key: Key to store the value under in the result; defaults
                to source_key when not provided.
            raise_error: Whether to re-raise the conversion error instead of
                skipping the value.

        Raises:
            ValueError: If the value is not a valid float and raise_error
                is True.
        """
        if source_key in self._source:
            try:
                self._result[target_key or source_key] = float(self._source[source_key])
            except ValueError:
                if raise_error:
                    raise

    def as_dict(self):
        """Return the values accumulated by the get_* methods.

        Returns:
            Dictionary mapping target keys to extracted, converted values.
        """
        return self._result
