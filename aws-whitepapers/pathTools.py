import os
from pathlib import Path
import string
import unicodedata
from urllib import parse

# https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file
_FOLDER_SEPARATOR_CHARS = ['\\', '/']
_DASH_CHARS = ['\u2012', '\u2013', '\u2014', '\u2015', '\u2053']
_WINDOWS_INVALID_CHARS = [':', '*', '|', '?', '>', '<', '"']
_WINDOWS_INVALID_FILENAME_CHARS = _WINDOWS_INVALID_CHARS + _FOLDER_SEPARATOR_CHARS
_FILENAME_REPLACE_CHARS = _WINDOWS_INVALID_FILENAME_CHARS + _DASH_CHARS
_PATHNAME_REPLACE_CHARS = _WINDOWS_INVALID_CHARS + _DASH_CHARS
_URL_STRIP_CHARS = string.whitespace + '/'


# _____________________________________________________________________________
def is_parent(parent: Path, path: Path):
    """Returns True is path has the same parent path as parent
    :param parent:
    :param path:
    :return: True if parent path is contained in path
    """
    parent = parent.resolve()
    path = path.resolve()
    return str(path).startswith(str(parent))


# _____________________________________________________________________________
def delete_empty_directories(folder):
    """Deletes all empty child folders under a parent folder
    :param folder: parent folder
    :return: List of deleted folders
    """
    deleted_folders = []
    for root, dirs, _ in os.walk(folder, topdown=False):
        for dir in dirs:
            loc = os.path.join(root, dir)
            with os.scandir(loc) as it:
                if next(it, None) is None:
                    deleted_folders.append(loc)
                    os.rmdir(loc)

    return deleted_folders


# _____________________________________________________________________________
def sanitize_filename(filename: str):
    """Returns MS-Windows sanitized filename using ASCII character set
    :param filename: string
    :return: sanitized filename

    Leading/trailing/multiple whitespaces removed.
    Unicode dashes converted to ASCII dash but other unicode characters removed.
    No checks on None, leading/trailing dots, or filename length.
    """
    filename = ' '.join(parse.unquote(filename).split())
    for ch in _FILENAME_REPLACE_CHARS:
        if ch in filename:
            filename = filename.replace(ch, '-')
    if not filename.isascii():
        filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode('ASCII')

    return filename


# _____________________________________________________________________________
def join_urlpath(url, *paths):
    """Returns URL by combining url with each of the arguments in turn
    :param url: base URL
    :param paths: paths to be added
    :return: URL

    Does not validate URL
    """
    u = url.strip(_URL_STRIP_CHARS)
    p = '/'.join(map(lambda x: x.strip(_URL_STRIP_CHARS), paths))
    return '%s/%s' % (u, p) if p else u


# _____________________________________________________________________________
def urlpath_to_pathname(url: str):
    """Returns MS-Windows sanitized filepath from a URL
    :param url: string
    :return: sanitized filename

    RFC 8089: The "file" URI Scheme
    """
    urlp = parse.urlparse(' '.join(parse.unquote(url).strip().split()))
    path = urlp.path.strip(_URL_STRIP_CHARS).replace('/', '\\')

    if not urlp.hostname:
        pathname = path
    else:
        pathname = '%s\\%s' % (urlp.hostname, path) if path else urlp.hostname

    for ch in _PATHNAME_REPLACE_CHARS:
        if ch in pathname:
            pathname = pathname.replace(ch, '-')
    if not pathname.isascii():
        pathname = unicodedata.normalize('NFKD', pathname).encode('ASCII', 'ignore').decode('ASCII')

    return pathname


# _____________________________________________________________________________
def url_suffix(url: str):
    """
    The final component's last suffix, if any.  Includes leading period (eg: .'html').

    Parsing:
    1. Use urlparse to remove any trailing URL parameters.  Note a) "path" will contain the hostname when the URL
    does not start with '//' and b) "path" can be empty string but never None.
    2. Strip traling URL separator '/' and remove LHS far right URL separator
    """
    path = parse.urlparse(parse.unquote(url)).path.strip()
    if (j := path.rfind('.', path.rfind('/') + 1, len(path) - 1)) >= 0:
        return path[j:]
    return ''
