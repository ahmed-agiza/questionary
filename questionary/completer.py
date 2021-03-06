from __future__ import unicode_literals
from six import string_types

from prompt_toolkit.completion import Completer, Completion
import os
import re

__all__ = [
    'PathCompleter',
    'ExecutableCompleter',
    'WordCompleter'

]


class PathCompleter(Completer):
    """
    Complete for Path variables.
    :param get_paths: Callable which returns a list of directories to look into
                      when the user enters a relative path.
    :param file_filter: Callable which takes a filename and returns whether
                        this file should show up in the completion. ``None``
                        when no filtering has to be done.
    :param min_input_len: Don't do autocompletion when the input string is shorter.
    """

    def __init__(self, only_directories=False, get_paths=None, file_filter=None,
                 min_input_len=0, expanduser=False, delimiters=None):
        assert get_paths is None or callable(get_paths)
        assert file_filter is None or callable(file_filter)
        assert delimiters is None or isinstance(delimiters, str)
        assert isinstance(min_input_len, int)
        assert isinstance(expanduser, bool)

        self.only_directories = only_directories
        self.get_paths = get_paths or (lambda: ['.'])
        self.file_filter = file_filter or (lambda _: True)
        self.min_input_len = min_input_len
        self.expanduser = expanduser
        self.delimiters = delimiters

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.strip()
        if self.delimiters is not None:
            regexPattern = '[' + \
                '|'.join(map(re.escape, self.delimiters.split())) + ']'
            text = re.split(regexPattern, text)[-1].strip()

        # Complete only when we have at least the minimal input length,
        # otherwise, we can too many results and autocompletion will become too
        # heavy.
        if len(text) < self.min_input_len:
            return

        try:
            # Do tilde expansion.
            if self.expanduser:
                text = os.path.expanduser(text)

            # Directories where to look.
            dirname = os.path.dirname(text)
            if dirname:
                directories = [os.path.dirname(os.path.join(p, text))
                               for p in self.get_paths()]
            else:
                directories = self.get_paths()

            # Start of current file.
            prefix = os.path.basename(text)

            # Get all filenames.
            filenames = []
            for directory in directories:
                # Look for matches in this directory.
                if os.path.isdir(directory):
                    for filename in os.listdir(directory):
                        if filename.startswith(prefix):
                            filenames.append((directory, filename))

            # Sort
            filenames = sorted(filenames, key=lambda k: k[1])

            # Yield them.
            for directory, filename in filenames:
                completion = filename[len(prefix):]
                full_name = os.path.join(directory, filename)

                if os.path.isdir(full_name):
                    # For directories, add a slash to the filename.
                    # (We don't add them to the `completion`. Users can type it
                    # to trigger the autocompletion themselves.)
                    filename += '/'
                elif self.only_directories:
                    continue

                if not self.file_filter(full_name):
                    continue

                yield Completion(completion, 0, display=filename)
        except OSError:
            pass


class ExecutableCompleter(PathCompleter):
    """
    Complete only executable files in the current path.
    """

    def __init__(self):
        PathCompleter.__init__(
            self,
            only_directories=False,
            min_input_len=1,
            get_paths=lambda: os.environ.get('PATH', '').split(os.pathsep),
            file_filter=lambda name: os.access(name, os.X_OK),
            expanduser=True)


class WordCompleter(Completer):
    """
    Simple autocompletion on a list of words.
    :param words: List of words or callable that returns a list of words.
    :param ignore_case: If True, case-insensitive completion.
    :param meta_dict: Optional dict mapping words to their meta-text. (This
        should map strings to strings or formatted text.)
    :param WORD: When True, use WORD characters.
    :param sentence: When True, don't complete by comparing the word before the
        cursor, but by comparing all the text before the cursor. In this case,
        the list of words is just a list of strings, where each string can
        contain spaces. (Can not be used together with the WORD option.)
    :param match_middle: When True, match not only the start, but also in the
                         middle of the word.
    :param pattern: Optional regex. When given, use this regex
        pattern instead of default one.
    """

    def __init__(self, words, ignore_case=False, meta_dict=None, WORD=False,
                 sentence=False, match_middle=False, pattern=None):
        assert not (WORD and sentence)
        assert callable(words) or all(isinstance(w, string_types)
                                      for w in words)

        self.words = words
        self.ignore_case = ignore_case
        self.meta_dict = meta_dict or {}
        self.WORD = WORD
        self.sentence = sentence
        self.match_middle = match_middle
        self.pattern = pattern

    def get_completions(self, document, complete_event):
        # Get list of words.
        words = self.words
        if callable(words):
            words = words()
        # Get word/text before cursor.
        if self.sentence:
            word_before_cursor = document.text_before_cursor
        else:
            word_before_cursor = document.get_word_before_cursor(
                # WORD=self.WORD, pattern=self.pattern)
                WORD=self.WORD)

        if self.ignore_case:
            word_before_cursor = word_before_cursor.lower()

        def word_matches(word):
            """ True when the word before the cursor matches. """
            if self.ignore_case:
                word = word.lower()

            if self.match_middle:
                return word_before_cursor in word
            else:
                return word.startswith(word_before_cursor)

        for a in words:
            if word_matches(a):
                display_meta = self.meta_dict.get(a, '')
                yield Completion(a, -len(word_before_cursor), display_meta=display_meta)
