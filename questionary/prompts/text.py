# -*- coding: utf-8 -*-

from questionary.question import Question
from questionary.prompts.common import build_validator
from questionary.constants import DEFAULT_STYLE, DEFAULT_QUESTION_PREFIX
from typing import Union, Callable, Optional, Any
from prompt_toolkit.document import Document
from prompt_toolkit.shortcuts.prompt import (
    PromptSession, CompleteStyle)
from prompt_toolkit.styles import merge_styles, Style
from prompt_toolkit.validation import Validator

from questionary.completer import PathCompleter, ExecutableCompleter
from prompt_toolkit.completion import WordCompleter

try:
    from typing import Text, Type
except ImportError:
    from typing_extensions import Text, Type


def text(message: Text,
         default: Text = "",
         validate: Union[Validator,
                         Callable[[Text], bool],
                         None] = None,  # noqa
         qmark: Text = DEFAULT_QUESTION_PREFIX,
         style: Optional[Style] = None,
         path_autocomplete=False,
         exec_autocomplete=False,
         custom_autocomplete=None,
         ** kwargs: Any) -> Question:
    """Prompt the user to enter a free text message.

       This question type can be used to prompt the user for some text input.

       Args:
           message: Question text

           default: Default value will be returned if the user just hits
                    enter.

           validate: Require the entered value to pass a validation. The
                     value can not be submited until the validator accepts
                     it (e.g. to check minimum password length).

                     This can either be a function accepting the input and
                     returning a boolean, or an class reference to a
                     subclass of the prompt toolkit Validator class.

           qmark: Question prefix displayed in front of the question.
                  By default this is a `?`

           style: A custom color and style for the question parts. You can
                  configure colors as well as font types for different elements.

       Returns:
           Question: Question instance, ready to be prompted (using `.ask()`).
    """

    merged_style = merge_styles([DEFAULT_STYLE, style])

    validator = build_validator(validate)

    def get_prompt_tokens():
        return [("class:qmark", qmark),
                ("class:question", ' {} '.format(message))]
    promptArgs = dict({
        'style': merged_style,
        'validator': validator,
        'complete_style': CompleteStyle.READLINE_LIKE,
    })
    if path_autocomplete:
        promptArgs['completer'] = PathCompleter(
            expanduser=True, delimiters=' \t\n;,')
    elif exec_autocomplete:
        promptArgs['completer'] = ExecutableCompleter(delimiters=' \t\n;,')
    elif custom_autocomplete is not None and len(custom_autocomplete):
        promptArgs['completer'] = WordCompleter(
            custom_autocomplete, ignore_case=True)

    p = PromptSession(get_prompt_tokens,
                      **promptArgs,
                      **kwargs)
    p.default_buffer.reset(Document(default))

    return Question(p.app)
