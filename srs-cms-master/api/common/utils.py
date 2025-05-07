import os
import datetime
import json
import re
import ast
import functools
from django.utils.timezone import is_naive, make_aware


class Utils:
    @classmethod
    def expand_path(cls, local_path):
        """
        Expands the given local path into a full path.

        Args:
            local_path: The local path to expand.

        Returns:
            Absolute path string of the expanded path.
        """
        var_path = os.path.expandvars(local_path)
        expanded_path = os.path.expanduser(var_path)
        return os.path.abspath(expanded_path)

    @classmethod
    def ensure_dirs(cls, local_path):
        """
        Ensures the directories in local_path exist.

        Args:
            local_path: The local path to ensure.

        Returns:
            None
        """
        if not os.path.isdir(local_path):
            os.makedirs(local_path)

    @classmethod
    def timestamp_str(cls):
        """
        Generate a timestamp string.

        Returns:
            String representation of the timestamp as "YmdHMSf".
        """
        return datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

    @classmethod
    def start_of_day(cls, dt=None):
        """
        Get the start of the day for a given datetime.

        Args:
            dt (datetime): The datatime to return the start of the day for, or None to get the current date.

        Returns:
            datetime for the start of the day.
        """
        dt = dt if dt is not None else datetime.datetime.now()
        return cls.to_aware_datetime(dt.replace(hour=0, minute=0, second=0, microsecond=0))

    @classmethod
    def end_of_day(cls, dt=None):
        """
        Get the end of the day for a given datetime.

        Args:
            dt (datetime): The datatime to return the end of the day for, or None to get the current date.

        Returns:
            datetime for the end of the day.
        """
        dt = dt if dt is not None else datetime.datetime.now()
        return cls.to_aware_datetime(dt.replace(hour=23, minute=59, second=59, microsecond=999999))

    @classmethod
    def to_aware_datetime(cls, dt):
        dt = dt if dt is not None else datetime.datetime.now()
        if is_naive(dt):
            dt = make_aware(dt)
        return dt

    @classmethod
    def to_date_string(cls, value, format="%Y-%m-%d", default=''):
        """
        Converts a date or datetime object to a formatted string.

        Args:
            value (date, datetime): The date object to convert.
            format (String): The format to return (default: YYYY-MM-DD).
            default (String): The default value to return if value is None.

        Returns:
            Formatted date/time string.
        """
        if not value:
            return default
        return value.strftime(format)

    @classmethod
    def to_datetime_string(cls, value, format="%Y-%m-%d %H:%M:%S", default=''):
        """
        Converts a datetime object to a formatted string.

        Args:
            value (datetime): The datetime object to convert.
            format (String): The format to return (default: YYYY-MM-DD HH:MM:SS).
            default (String): The default value to return if value is None.

        Returns:
         Formatted datetime string.
        """
        return cls.to_date_string(value, format=format, default=default)

    @classmethod
    def to_list(cls, arg):
        """
        Converts the given argument into a list with any None values removed.
        This is mainly used for converting method args to lists when the arg supports a single object or list.

        Args:
            arg: Argument to convert to list.

        Returns:
            List of arg.
        """
        args = list(filter(lambda a: a is not None, (arg if isinstance(arg, list) else [arg])))
        return args

    @classmethod
    def get_field(cls, obj, *keys, default=None):
        """
        Get the value from a dictionary or object at the specified keys, or returns a default value.

        Args:
            obj: The starting object to get the value from.
            *keys: The keys path to get the value from.
            default: The default value to return if the key does not exist.

        Returns:
            The value of the specified key or the default value.
        """
        for current_obj, last_obj, has_key, key, keys, index in cls._yield_fields_from(obj, *keys, default=default):
            if has_key and key == keys[-1]:
                return current_obj
            elif not has_key:
                return current_obj
        return default

    @classmethod
    def has_field(cls, obj, *keys):
        """
        Gets if a dictionary or object has the specified keys.

        Args:
            obj: The starting object to check.
            *keys: The keys path to check.

        Returns:
            True if the specified key exists, otherwise False.
        """
        for current_obj, last_obj, has_key, key, keys, index in cls._yield_fields_from(obj, *keys):
            if not has_key:
                return False
            elif has_key and key == keys[-1]:
                return True

    @classmethod
    def _yield_fields_from(cls, obj, *keys, default=None):
        """
        Drills into an object from properties path/keys and yields the object and keys.

        Args:
            obj: The starting object to get the value from.
            *keys: The keys path to get the value from.
                Formats:
                    1. Simple Path: "parent.child.property_name"
                    2. List Path: "parent.child.list_property_name[0]"
                                  "parent.child.list_property_name[0].list_obj.property_name"
            default: The default value to return if the key does not exist.

        Yields: (current_obj, last_obj, has_key, key, keys, index)

        Returns:
            None. This is a generator.
        """
        if len(keys) == 0:
            raise Exception('At least one key must be provided.')

        # Flatten keys by splitting on periods.
        keys = [part for key in keys for part in key.split('.')]

        last_obj = obj
        current_obj = obj
        for key in keys:
            orig_key = key
            index = None
            if key.endswith(']'):
                match = re.search(r'\[(\d+)\]', key)
                if match:
                    index = int(match.group(1))
                    key = key.rsplit('[', 1)[0]

            is_dict = isinstance(current_obj, dict)
            has_attr = hasattr(current_obj, key)
            is_method = key.endswith(')')
            has_key = False
            if is_dict or has_attr or is_method:
                if is_dict:
                    has_key = key in current_obj
                    last_obj = current_obj
                    current_obj = current_obj.get(key, default)
                    if index is not None and isinstance(current_obj, list):
                        last_obj = current_obj
                        if len(current_obj) >= index:
                            current_obj = current_obj[index]
                        else:
                            current_obj = default
                elif has_attr:
                    has_key = True
                    last_obj = current_obj
                    current_obj = getattr(current_obj, key, default)
                    if index is not None and isinstance(current_obj, list):
                        last_obj = current_obj
                        if len(current_obj) >= index:
                            current_obj = current_obj[index]
                        else:
                            current_obj = default
                elif is_method:
                    method_name, method_pos_args, method_kw_args = cls.parse_str_method(key)
                    has_key = method_name is not None
                    last_obj = current_obj
                    method = getattr(current_obj, method_name, None)
                    if method and callable(method):
                        current_obj = method(*method_pos_args, **method_kw_args) or default
                    else:
                        current_obj = default

                yield current_obj, last_obj, has_key, orig_key, keys, index
            else:
                has_key = False
                yield default, last_obj, has_key, orig_key, keys, index

    @classmethod
    @functools.lru_cache(maxsize=50)
    def parse_str_method(cls, method_str: str):
        """
        Parses method name and arguments from a string.

        param method_str (String): Method call string (e.g., 'get_something("zero", format="1", other_arg=2)')

        Returns:
            Tuple (method_name, positional_args, keyword_args)
        """
        match = re.match(r"(\w+)\((.*)\)", method_str)
        if not match:
            return None, None, None

        method_name = match.group(1)
        args_str = match.group(2).strip()

        pos_args = []
        kw_args = {}

        if args_str:
            parsed_args = ast.parse(f"fn({args_str})").body[0].value.args
            parsed_kwargs = ast.parse(f"fn({args_str})").body[0].value.keywords
            pos_args = [ast.literal_eval(arg) for arg in parsed_args]
            kw_args = {kw.arg: ast.literal_eval(kw.value) for kw in parsed_kwargs}

        return method_name, pos_args, kw_args

    @classmethod
    def load_json(cls, path):
        """
        Load and parse a JSON file.

        Args:
            path (str): Path to the JSON file.

        Returns:
            dict: Parsed JSON data as a dictionary.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        try:
            with open(path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("The file '{}' does not exist.".format(path))
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError("Invalid JSON in file '{}': {}".format(e.doc, e.pos))

    @classmethod
    def save_json(cls, data, file_path):
        """
        Save data to a JSON file.

        Args:
            data (dict or list): The data to save in JSON format.
            file_path (str): The path to the JSON file to save.

        Returns:
            bool: True if the file was saved successfully, False otherwise.
        """
        try:
            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4, sort_keys=True)
            return True
        except (TypeError, OSError) as ex:
            print('Error saving JSON file: {}'.format(ex))
            return False
