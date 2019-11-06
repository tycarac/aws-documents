import math

MULTIPLES = ['', "k{}B", "M{}B", "G{}B", "T{}B", "P{}B", "E{}B", "Z{}B", "Y{}B"]


# _____________________________________________________________________________
def url_join_path(*args):
    return '/'.join(map(lambda x: x.strip().strip('/'), args))


# _____________________________________________________________________________
def remove_filename_invalid_characters(filename: str):
    # https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file
    for ch in ['\\', '/', ':', '*', '|', '?', '>', '<', '"']:
        if ch in filename:
            filename = filename.replace(ch, '-')
    return filename
