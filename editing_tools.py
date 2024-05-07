import os
import json
from rich import print as rich_print

class Error(Exception):
    def __init__(self, error: str) -> Exception:
        self.error = error
        super().__init__(self.error)

def custom_error(error_type: str, error: str) -> Exception:
    rich_print(f'[red]{error}')
    error_class = type(error_type, (Error,), {})
    raise error_class(error=error)

class JSONEditor:
    def __init__(self, json_file_path: str = None) -> None:
        if not json_file_path:
            error = "Json File Path Not Provided to 'JSONEditor' class!"
            custom_error(error_type="FilePathNotProvidedError", error=error)
        
        elif type(json_file_path) != str:
            error = f"Json File Path Type is '{type(json_file_path)}', provide 'str' path to the JSONEditor class!"
            custom_error(error_type="InvalidFilePathTypeError", error=error)
        
        self.path: str = json_file_path

    def edit_json_file(self, content: dict=None) -> None:
        if not content:
            error = "Content Not Provided to 'edit_json_file' function!"
            custom_error(error_type="ContentNotProvidedError", error=error)

        elif type(content) != dict:
            error = f"Provided Content Type is Invalid - '{type(content)}', provide 'dict' type content to the function!"
            custom_error(error_type="InvalidContentTypeError", error=error)

        file_path=self.path

        if not os.path.exists(path=file_path):
            make_file(file_path=file_path)

        with open(file=file_path, mode='r') as file:
            try:
                existing_data = json.load(file)
            except json.decoder.JSONDecodeError:existing_data={}
            
            existing_data.update(content)

            with open(file_path, 'w') as upgrade_file:
                json.dump(obj=existing_data, fp=upgrade_file, indent=4)

    def get_json_value(self, key: str|int) -> str|int:
        if not key:
            error = "key Not Provided to 'get_json_value' function!"
            custom_error(error_type="KeyNotProvidedError", error=error)

        elif type(key) != str or int:
            error = f"Provided Key Type is Invalid - '{type(key)}', provide 'int' or 'str' type key to the function!"
            custom_error(error_type="InvalidKeyTypeError", error=error)

        with open(file=self.path, mode='r') as file:
            try:
                existing_data = json.load(file)
            except json.decoder.JSONDecodeError:existing_data={}

            try:return existing_data[key]

            except KeyError:
                rich_print('Provided Key not Found!')
                raise KeyError

    def get_json_data(self) -> dict:
        with open(file=self.path, mode='r') as file:
            try:
                existing_data = json.load(file)
            except json.decoder.JSONDecodeError:existing_data={}

            return existing_data
        
    @staticmethod
    def build_json_file(file_path: str=None, content: dict=None) -> None:
        if not file_path:
            error = f"File Path Not Provided to 'build_json_file' function!"
            custom_error(error_type="FilePathNotProvidedError", error=error)
        
        elif type(file_path) != str:
            error = f"File Path Type is '{type(file_path)}', provide 'str' path to the function!"
            custom_error(error_type="InvalidFilePathTypeError", error=error)

        if not content:
            error = "Content Not Provided to 'build_json_file' function!"
            custom_error(error_type="ContentNotProvidedError", error=error)

        elif type(content) != dict:
            error = f"Provided Content Type is Invalid - '{type(content)}', provide 'dict' type content to the function!"
            custom_error(error_type="InvalidContentTypeError", error=error)

        file = JSONEditor(json_file_path=file_path)
        file.edit_json_file(content=content)

    @staticmethod
    def duplicate_json_file(from_file_path: str=None, to_file_path: str=None):
        if not from_file_path:
            error = f"'from_file_path' Not Provided to 'duplicate_json_file' function!"
            custom_error(error_type="FromFilePathNotProvidedError", error=error)
        
        elif type(from_file_path) != str:
            error = f"'from_file_path' is '{type(from_file_path)}', provide 'str' path to the function!"
            custom_error(error_type="InvalidFilePathTypeError", error=error)

        if not to_file_path:
            error = f"'to_file_path' Not Provided to 'duplicate_json_file' function!"
            custom_error(error_type="TpFilePathNotProvidedError", error=error)
        
        elif type(to_file_path) != str:
            error = f"'to_file_path' is '{type(to_file_path)}', provide 'str' path to the function!"
            custom_error(error_type="InvalidFilePathTypeError", error=error)

        with open(from_file_path, 'r') as from_file:
            data = json.load(from_file)

        with open(to_file_path, 'w') as to_file:
            json.dump(data, to_file, indent=4)

def make_file(file_path: str=None) -> None:
    if not file_path:
        error = "File Path Not Provided to 'make_file' function!"
        custom_error(error_type="FilePathNotProvidedError", error=error)
    
    elif type(file_path) != str:
        error = f"File Path Type is '{type(file_path)}', provide 'str' path to the function!"
        custom_error(error_type="InvalidFilePathTypeError", error=error)

    with open(file=file_path, mode='w') as _:
        pass

if __name__=='__main__':
    pass