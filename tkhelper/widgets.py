"""Includes common used tkinter based widgets

Author: Erdogan Onal
mailto: erdoganonal@windowslive.com
"""
import os
import enum
import string
import random
from typing import Union, Any, Type, Tuple, Callable, Iterable

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import font
from PIL import Image, ImageTk

from .package_info import __version__, __author__, __mail__

# pylint: disable=too-many-ancestors

LETTERS_AND_DIGITS = string.ascii_letters + string.digits
SAMPLES = {}

_DOCTEST_TIME_MS = 1 * 1000


def with_root(function):
    """helper function for docstrings"""
    def wrapper(*args, **kwargs):
        timeout = kwargs.pop('timeout', _DOCTEST_TIME_MS)
        root = tk.Tk()
        function(root, *args, **kwargs)
        root.after(timeout, root.destroy)
        root.mainloop()
    return wrapper


class TkHelperBaseError(Exception):
    """Base for this module"""


class InvalidChoice(TkHelperBaseError):
    """Raise when given choice is not valid"""

    def __init__(self, option: Any, options_enum: Any):
        message = ""\
            "Given option[{0}] is not a valid option. " \
            "Valid options: {1}" \
            "".format(option, ', '.join(map(str, options_enum)))

        super().__init__(message)


class TkRecursionError(TkHelperBaseError, RecursionError):
    """Protection for recursion in resize"""


class Objectless(type):
    """A metaclass to disable instantiation"""

    def __call__(cls):
        raise RuntimeError('{0} should not be instantiated'.format(cls))


class WidgetTheme:
    """Theme for a widget. Define configurations to apply.
        >>> WidgetTheme(bg='black').to_dict()
        {'bg': 'black'}

        >>> WidgetTheme(bg='black').keys()
        dict_keys(['bg'])
    """

    def __init__(self, **kwargs):
        self.__kwargs = kwargs

    def to_dict(self) -> dict:
        """Return the dict representation"""
        return dict(self)

    def keys(self) -> Iterable:
        """Return the keys of the WidgetTheme"""
        return self.__kwargs.keys()

    def __getitem__(self, key: str) -> str:
        """Return the value of the key in the WidgetTheme"""
        return self.__kwargs.get(key)

    def __str__(self) -> str:
        return str(self.__kwargs)


EMPTY_THEME = WidgetTheme()


class Theme(metaclass=Objectless):
    """Base for all themes"""
    # For all
    __default__ = EMPTY_THEME

    # for root
    ROOT = EMPTY_THEME

    # for tk
    BUTTON = EMPTY_THEME
    CANVAS = EMPTY_THEME
    CHECKBUTTON = EMPTY_THEME
    ENTRY = EMPTY_THEME
    FRAME = EMPTY_THEME
    LABEL = EMPTY_THEME
    LABELFRAME = EMPTY_THEME
    LISTBOX = EMPTY_THEME
    MENU = EMPTY_THEME
    MENUBUTTON = EMPTY_THEME
    MESSAGE = EMPTY_THEME
    PANEDWINDOW = EMPTY_THEME
    RADIOBUTTON = EMPTY_THEME
    SCALE = EMPTY_THEME
    SCROLLBAR = EMPTY_THEME
    SPINBOX = EMPTY_THEME
    TEXT = EMPTY_THEME

    # for ttk
    TTK_BUTTON = EMPTY_THEME
    TTK_CHECKBUTTON = EMPTY_THEME
    TTK_COMBOBOX = EMPTY_THEME
    TTK_ENTRY = EMPTY_THEME
    TTK_FRAME = EMPTY_THEME
    TTK_LABEL = EMPTY_THEME
    TTK_LABELFRAME = EMPTY_THEME
    TTK_MENUBUTTON = EMPTY_THEME
    TTK_NOTEBOOK = EMPTY_THEME
    TTK_PANEDWINDOW = EMPTY_THEME
    TTK_PROGRESSBAR = EMPTY_THEME
    TTK_RADIOBUTTON = EMPTY_THEME
    TTK_SCALE = EMPTY_THEME
    TTK_SCROLLBAR = EMPTY_THEME
    TTK_SEPARATOR = EMPTY_THEME
    TTK_SIZEGRIP = EMPTY_THEME
    TTK_SPINBOX = EMPTY_THEME
    TTK_TREEVIEW = EMPTY_THEME

    @classmethod
    def get_theme(cls, widget_name: str) -> WidgetTheme:
        """return the value of the key"""
        name = widget_name.lower().replace('::', '_')
        for key in dir(cls):
            value = getattr(cls, key)
            if key.lower() == name:
                return value
        raise AttributeError(
            "'{0!r}' object has no attribute '{1}'"
            "".format(cls, widget_name)
        )

    @classmethod
    def set_theme(cls, key: str, value: WidgetTheme) -> None:
        """set the value of the key"""
        setattr(cls, key.upper(), value)


class DarkTheme(Theme):
    """A dark theme"""
    __default__ = WidgetTheme(background="#616161")

    ROOT = WidgetTheme(background="#616161")
    FRAME = WidgetTheme(background="#616161")
    BUTTON = WidgetTheme(background="#cccccc")
    TEXT = WidgetTheme(background="#757575")
    LABEL = WidgetTheme(background="#757575")
    ENTRY = WidgetTheme()


def _configure(widget: Union[tk.Tk, tk.Widget], theme: Type[Theme]) -> None:
    if isinstance(widget, tk.Tk):
        root_theme = theme.get_theme('root')
        if root_theme is EMPTY_THEME:
            widget.configure(**theme.__default__.to_dict())
        else:
            widget.configure(**root_theme.to_dict())
    elif isinstance(widget, tk.Widget):
        theme_name = widget.widgetName
        widget_theme = theme.get_theme(theme_name)
        if widget_theme is EMPTY_THEME:
            widget_theme = theme.get_theme('__default__')

        if widget.widgetName.startswith('ttk::'):
            style = ttk.Style(widget)
            style.configure(widget.winfo_class(), **widget_theme.to_dict())
        else:
            widget.configure(**widget_theme.to_dict())


def configure(widget: Union[tk.Tk, tk.Widget], theme: [Theme] = Theme) -> None:
    """Set some configurations for given widget and its children
        Args:
            widget: A widget to configure
            theme:  Apply given theme to the widget.
    """
    _configure(widget, theme)
    for child in widget.winfo_children():
        configure(child, theme)


class AddToolTip:
    """Create a tooltip window to display help message
        Args:
            widget: A widget to add tooltip
            text:   Help message to display.
    """

    def __init__(self, widget: Union[tk.Tk, tk.Widget], text: str):
        self.text = text
        self.widget = widget
        self.tip_window = None

        self.widget.bind('<Enter>', lambda event: self.showtip())
        self.widget.bind('<Leave>', lambda event: self.hidetip())

    def showtip(self) -> None:
        """Display text in tooltip window"""
        x_offset = y_offset = 30

        if self.tip_window or not self.text:
            return
        coord_x, coord_y, _, coord_y2 = self.widget.bbox("insert")
        coord_x = coord_x + self.widget.winfo_rootx() + x_offset
        coord_y = coord_y + coord_y2 + self.widget.winfo_rooty() + y_offset
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry("+%d+%d" % (coord_x, coord_y))
        label = tk.Label(self.tip_window, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self) -> None:
        """Hide the tooltip"""
        if self.tip_window:
            self.tip_window.destroy()

        self.tip_window = None


def create_widget(widget_class: Callable, *args, **kwargs) -> Union[tk.Tk, tk.Widget]:
    """Create a widget with custom properties"""

    tooltip = kwargs.pop('tooltip', None)

    widget = widget_class(*args, **kwargs)
    if tooltip:
        AddToolTip(widget, tooltip)

    return widget


class EntryWithPlaceholder(tk.Entry):
    """Entry widget which allows displaying simple text with a placeholder
        Args:
            *args, **kw: Parameters for Entry
            placeholder: Placeholder for the entry
            color:       Placeholder background color

        >>> root = tk.Tk()
        >>> EntryWithPlaceholder(
        ...     root, placeholder="This is a placeholder"
        ... ).grid()
        >>> root.after(_DOCTEST_TIME_MS, root.destroy) # doctest: +ELLIPSIS
        'after#...'
        >>> root.mainloop()
    """

    def __init__(self, *args, placeholder: str = "", color: str = 'grey', **kw):
        super().__init__(*args, **kw)

        self._is_empty = True

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.__bind("<FocusIn>", self.focus_in)
        self.__bind("<FocusOut>", self.focus_out)

        self.put_placeholder()

    def get(self) -> None:
        """Return the text of the entry."""
        if self._is_empty:
            return None
        return super().get()

    def put_placeholder(self) -> None:
        """Put the place holder"""
        self._is_empty = True
        self.insert(0, self.placeholder, placeholder=True)
        self['fg'] = self.placeholder_color

    def focus_in(self, *_) -> None:
        """Clear placeholder and allow typing"""
        self._is_empty = False

        if self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self['fg'] = self.default_fg_color

    def focus_out(self, *_) -> None:
        """Add placeholder if empty"""
        if not self.get():
            self.put_placeholder()

    def insert(self, *args, **kwargs) -> None:
        """Insert the text"""
        placeholder = kwargs.pop('placeholder', False)
        if not placeholder and self['fg'] == self.placeholder_color:
            self._is_empty = False
            self['fg'] = self.default_fg_color
        super().insert(*args, **kwargs)

    def __bind(self, sequence: str = None, func: Callable = None,
               add: Union[bool, None] = None) -> None:
        super().bind(sequence, func, add)

    def bind(self, sequence: str = None, func: Callable = None,
             add: Union[bool, None] = None) -> None:
        """Bind to this widget at event SEQUENCE a call to function FUNC."""
        # Don't allow to override "<FocusIn>" and "<FocusOut>"
        if sequence in ("<FocusIn>", "<FocusOut>"):
            return
        self.__bind(sequence, func, add)

    def unbind(self, sequence: str, funcid: int = None):
        """Unbind for this widget for event SEQUENCE  the
        function identified with FUNC_ID."""
        # Don't allow to delete "<FocusIn>" and "<FocusOut>"
        if sequence in ("<FocusIn>", "<FocusOut>"):
            return
        super().unbind(sequence, funcid)


class TargetType(enum.Enum):
    """possible targets"""
    FILE = enum.auto()
    FOLDER = enum.auto()


class SelectionWidget(tk.Frame):
    """render Entry and Button to enter or select a path
        Args:
            master:              Root for the widget.
            *args
            **kwargs:            Configurations for base class.
            placeholder:         Placeholder for entry.
            entry_options:       Options for the enrty.
            entry_grid_options:  Grid options for the entry.
            button_options:      Options for the button.
            button_grid_options: Grid options for the button.
            kind:                Type of the selection widget.
                                 You shall choose a file path or
                                 folder path.
            ratio:               Ratio of the entry width over button width
        >>> # noinspection PyUnresolvedReferences
        >>> @with_root
        ... def test_selection_widget(root):
        ...     SelectionWidget(root, placeholder="1 to 1 ratio.",
        ...         kind=TargetType.FILE, ratio=(1, 1)).grid()
        ...     SelectionWidget(root, placeholder="1 to 2 ratio.",
        ...         kind=TargetType.FILE, ratio=(1, 2)).grid()
        ...     SelectionWidget(root, placeholder="10 to 1 ratio.",
        ...         kind=TargetType.FILE, ratio=(10, 1)).grid()
        ...     SelectionWidget(root, placeholder="10 to 3 ratio.",
        ...         kind=TargetType.FILE, ratio=(10, 3)).grid()
        ...     SelectionWidget(root, placeholder="10 to 2 ratio.",
        ...         kind=TargetType.FILE, ratio=(10, 2)).grid()
        ...     SelectionWidget(root, placeholder="5 to 1 ratio.",
        ...         kind=TargetType.FILE, ratio=(5, 1)).grid()
        >>> test_selection_widget()
    """

    def __init__(self, master: Union[tk.Tk, tk.Widget], *args,
                 placeholder: str = '',
                 entry_options: dict = None, entry_grid_options: dict = None,
                 button_options: dict = None, button_grid_options: dict = None,
                 kind: TargetType = TargetType.FILE,
                 ratio: Tuple[float, float] = (5, 1),
                 **kwargs):
        super().__init__(master, *args, **kwargs)

        if entry_options is None:
            entry_options = {}

        if entry_grid_options is None:
            entry_grid_options = {}

        if button_options is None:
            button_options = {}

        if button_grid_options is None:
            button_grid_options = {}

        self._entry = None
        self._button = None

        self._kind = kind
        self._placeholder = placeholder

        # pop items to not override
        for key in ['row', 'column', 'rowspan', 'columnspan']:
            entry_grid_options.pop(key, None)
            button_grid_options.pop(key, None)

        self._place_entry(entry_options, entry_grid_options)
        self._place_button(button_options, button_grid_options)

        self.columnconfigure(0, weight=ratio[0], uniform="foo")
        self.columnconfigure(1, weight=ratio[1], uniform="foo")

    @property
    def kind(self) -> TargetType:
        """return the kind of the select button

        >>> # noinspection PyUnresolvedReferences
        >>> @with_root
        ... def kind_test(root):
        ...     selection = SelectionWidget(root, placeholder="test placeholder")
        ...     selection.grid()
        ...     print(selection.kind)
        >>> kind_test()
        TargetType.FILE
        """
        return self._kind

    @property
    def placeholder(self) -> str:
        """return the placeholder text

        >>> # noinspection PyUnresolvedReferences
        >>> @with_root
        ... def placeholder_test(root):
        ...     selection = SelectionWidget(root, placeholder="placeholder test")
        ...     selection.grid()
        ...     print(selection.placeholder)
        >>> placeholder_test()
        placeholder test
        """
        return self._placeholder

    @property
    def text(self) -> str:
        """return the text of the entry

        >>> # noinspection PyUnresolvedReferences
        >>> @with_root
        ... def text_test(root):
        ...     selection = SelectionWidget(root)
        ...     selection.grid()
        ...     selection.text = "this is the text"
        ...     print(selection.text)
        >>> text_test()
        this is the text
        """
        return self.entry.get()

    @text.setter
    def text(self, value: str) -> None:
        """set the text of the entry"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, str(value))

    def command_handler(self) -> None:
        """Handle the button click event"""
        if self.kind == TargetType.FILE:
            location = filedialog.askopenfilename()
        elif self.kind == TargetType.FOLDER:
            location = filedialog.askdirectory()
        else:
            raise InvalidChoice(self.kind, TargetType)

        if location:
            self.text = location

    def _place_entry(self, options: dict, grid_options: dict) -> None:
        default_options = {
            'placeholder': self._placeholder
        }
        default_options.update(**options)
        self.entry = create_widget(
            EntryWithPlaceholder, self, **default_options)

        default_grid_options = {
            'row': 0, 'column': 0,
            'padx': (0, 5),
            'sticky': tk.NSEW
        }
        default_grid_options.update(grid_options)
        self.entry.grid(**default_grid_options)

    def _place_button(self, options: dict, grid_options: dict) -> None:
        if 'callback' in options:
            callback = options.pop('callback')

            def command():
                return callback(self)
        else:
            command = self.command_handler

        default_options = {
            'text': '...', 'command': command
        }
        default_options.update(**options)
        self.button = create_widget(tk.Button, self, **default_options)

        default_grid_options = {
            'row': 0, 'column': 1,
            'sticky': tk.NSEW
        }
        default_grid_options.update(grid_options)
        self.button.grid(**default_grid_options)


class _ResizableBase(tk.Widget):

    def __init__(self, *args, **kwargs):
        self._font = None
        self._width = None
        self.weight_width = None
        self.weight_height = None
        self._dummy_text = None
        super().__init__(*args, **kwargs)

    def _init(
            self,
            weight: Union[float, Tuple[float, float]],
            base_font: font.Font, resize: bool = True, fix_text_len=None):
        """
        A base for resizable widgets.
        """
        self.font = base_font
        try:
            self.weight_width = float(weight[0])
            self.weight_height = float(weight[1])
        except TypeError:
            self.weight_width = self.weight_height = float(weight)

        if resize:
            self.winfo_toplevel().bind("<Configure>", self._resize, add="+")

        self._dummy_text = ""
        self.fix_text_len = fix_text_len
        self._width = self.winfo_toplevel().winfo_width()

    @property
    def font(self) -> font.Font:
        """return the font information"""
        return self._font

    @font.setter
    def font(self, base_font: Any) -> None:
        """set given font as label font"""
        if isinstance(base_font, font.Font):
            self._font = base_font
        else:
            # string fonts are not allowed at this widget
            raise ValueError("font must be instance of {!r}".format(font.Font))

    @property
    def fix_text_len(self) -> Union[None, int]:
        """Return the length of the text which set before is possible"""
        try:
            return len(self._dummy_text)
        except TypeError:
            return None

    @fix_text_len.setter
    def fix_text_len(self, value: Union[None, int]) -> None:
        if value is None:
            self._dummy_text = None
            return
        value = int(value)
        try:
            random_sample = SAMPLES[str(value)]
        except KeyError:
            random_sample = ''.join(random.sample(
                LETTERS_AND_DIGITS, int(value)))
            SAMPLES[str(value)] = random_sample
        self._dummy_text = random_sample

    def _resize(self, _) -> None:
        text = self._dummy_text or self.cget("text")
        if not text:
            return

        if self.fix_text_len and len(text) < self.fix_text_len:
            text += ' ' * (len(text) < self.fix_text_len)

        top_level_width = self.winfo_toplevel().winfo_width()
        if top_level_width == 1:
            # If width equals to 1 means that
            # the main window is in initial step.
            return

        expected_width = top_level_width * self.weight_width
        dummy_font = self.font.copy()

        while True:
            current_width = dummy_font.measure(text)
            font_size = dummy_font.actual('size')

            if current_width < expected_width:
                # if current width smaller than expected
                # increase the dummy font size by one
                dummy_font['size'] = font_size + 1
                if dummy_font.measure(text) > expected_width:
                    # if increasing size exceeds the expected,
                    # undo increasing and exit the loop
                    dummy_font['size'] = font_size
                    break
                # still have spaces, so continue
            else:
                # if current width grater than expected
                # decrease the dummy font size by one
                dummy_font['size'] = font_size - 1
                if dummy_font.measure(text) < expected_width:
                    # if it is fit, break the loop
                    break
                # if it is not fit, means we have spaces
                # so, continue

        self.font = dummy_font
        self.configure(font=self.font)


class ResizableLabel(tk.Label, _ResizableBase):
    """Create a label which resize with outer window
        Args:
            master:         Root of the widget.
            *args
            **kwargs:     Configurations for base class.
            weight:       The ratio of the label width over top level width.
                          The calculation will be based on the text of the label.
            resize:       If True, the widget wile be resized with top level window.
            fix_text_len: If passed, the label ignores its actual text and uses a dummy
                          text with length of this value. This feature allows you to
                          keep fixed size the label. Basically, whatever the text size is,
                          the label size will not change.

        >>> timeout = 1
        >>> # noinspection PyUnresolvedReferences
        >>> @with_root
        ... def resizable_label_test(root):
        ...     root.geometry("500x500")
        ...     tk.Label(root,
        ...         text="Default tk.Label - Click X to close. Timeout is {0} secs."
        ...         "".format(timeout)
        ...     ).grid()
        ...     ResizableLabel(root, weight=0.5,
        ...         text="This text covers 50% of the total width.").grid()
        ...     ResizableLabel(root, weight=1,
        ...         text="This text covers 100% of the total width.").grid()
        ...     ResizableLabel(root, weight=1, resize=False,
        ...         text="This text covers 100% of the total width. Non resizable!"
        ...     ).grid()
        ...     ResizableLabel(root, weight=.3, fix_text_len=20,
        ...         text="This text covers 50% of the total width. fix_text_len is 20"
        ...     ).grid()
        >>> resizable_label_test(timeout=timeout * 1000)

    """

    def __init__(self,
                 master: Union[tk.Tk, tk.Widget],
                 *args, weight: float = 1.0, resize: bool = True,
                 fix_text_len: Union[int, None] = None, **kwargs):
        base_font = kwargs.pop('font', font.Font())

        super().__init__(master, *args, **kwargs)
        self._init(weight, base_font, resize, fix_text_len)

    def configure(self, cnf: Any = None, **kwargs) -> None:
        """override the configure method to capture font"""
        self.font = kwargs.get('font', font.Font())
        super().configure(cnf, **kwargs)


class ResizableLabelImage(ResizableLabel):
    """A label which can resize
        Args:
            *args
            **kwargs:   Configurations for base class.
            image:      The image to display on the screen.
            image_path: The path of the image.
    """

    def __init__(self, *args,
                 image: Image.Image = None,
                 image_path: str = None, **kwargs):
        if image is not None and image_path is not None:
            raise ValueError(
                "you are allowed to pass only image or image_path"
            )

        if image:
            self._original = image
        if image_path:
            self._original = Image.open(image_path)
        self._resized = None

        super().__init__(*args, **kwargs, image=self._resized)

    def _resize(self, _) -> None:
        min_size = 10
        width = self.winfo_toplevel().winfo_width()
        height = self.winfo_toplevel().winfo_height()
        size = min(
            max(int(width * self.weight_width), min_size),
            max(int(height * self.weight_height), min_size)
        )

        self.set_image(self._original, (size, size))

    def set_image(self, image: Image.Image,
                  image_size: Tuple[int, int] = None,
                  resample: int = Image.ANTIALIAS):
        """Set the given image"""
        self._original = image

        if image_size is None:
            resized = image
        else:
            resized = image.resize(image_size, resample)
        self._resized = ImageTk.PhotoImage(resized)

        self.configure(image=self._resized)


class ResizableButton(tk.Button, _ResizableBase):
    """Create a button which resize with outer window
        Args:
            master:         Root of the widget.
            *args
            **kwargs:       Configurations for base class.
            weight:         The ratio of the button width over top level width.
                            The calculation will be based on the text of the button.
            resize:         If True, the widget wile be resized with top level window.
            fixed_text_len: If passed, the button ignores its actual text and uses a dummy
                            text with length of this value. This feature allows you to
                            keep fixed size the button. Basically, whatever the text size is,
                            the button size will not change.

        >>> timeout = 1
        >>> # noinspection PyUnresolvedReferences
        >>> @with_root
        ... def resizable_button_test(root):
        ...     root.geometry("500x500")
        ...     tk.Button(root,
        ...         text="Default tk.Button - Click X to close. Timeout is {0} secs."
        ...         "".format(timeout)
        ...     ).grid()
        ...     ResizableButton(root, weight=0.5,
        ...         text="This text covers 50% of the total width.").grid()
        ...     ResizableButton(root, weight=1,
        ...         text="This text covers 100% of the total width.").grid()
        ...     ResizableButton(root, weight=1, resize=False,
        ...         text="This text covers 100% of the total width. Non resizable!"
        ...     ).grid()
        ...     ResizableButton(root, weight=.3, fix_text_len=20,
        ...         text="This text covers 50% of the total width. fix_text_len is 20"
        ...     ).grid()
        >>> resizable_button_test(timeout=timeout * 1000)
    """

    def __init__(self,
                 master: Union[tk.Tk, tk.Widget],
                 *args, weight: float = 1.0,
                 resize: bool = True,
                 fix_text_len: int = None, **kwargs):
        self._font = None
        base_font = kwargs.pop('font', font.Font())

        super().__init__(master, *args, **kwargs)
        self._init(weight, base_font, resize, fix_text_len)

    def configure(self, cnf: Any = None, **kwargs) -> None:
        """override the configure method to capture font"""
        self.font = kwargs.get('font', font.Font())
        super().configure(cnf, **kwargs)


class FixedSizedOptionMenu(ttk.OptionMenu):
    """A fix-sized option menu, calculates the width from options and placeholder
        Args:
            master:      Root of the widget.
            variable:    Tkinter variable for dropdown menu.
            *values:     Options for dropdown menu.
            placeholder: Help-like option. Cannot be selected as a value.
            **kwargs:    Configurations for base class.

        >>> timeout = 1
        >>> # noinspection PyUnresolvedReferences
        >>> @with_root
        ... def fixed_sized_option_menu(root):
        ...     variable = tk.StringVar()
        ...     options = ["option1", "option2", "option3 with a long name"]
        ...     FixedSizedOptionMenu(
        ...         root, variable, *options,
        ...         placeholder="This is the placeholder"
        ...     ).grid()
        >>> fixed_sized_option_menu(timeout=timeout * 1000)
    """

    def __init__(self,
                 master: Union[tk.Tk, tk.Widget],
                 variable: tk.Variable, *values,
                 placeholder: str = None, **kwargs):

        self._placeholder = placeholder
        if placeholder is None:
            placeholder = values[0]
        super().__init__(master, variable, placeholder, *values, **kwargs)
        self.configure(**self._get_option_menu_style(placeholder, values))

    def get(self) -> Union[str, None]:
        """Return the value of drop down menu. None will be returned
        if no option is selected and placeholder exist.
        """
        value = self._variable.get()
        if value == self._placeholder:
            return None
        return value

    @staticmethod
    def _get_option_menu_style(placeholder: str, option_list: Iterable) -> dict:
        style = {}
        width = max([len(i) for i in option_list])
        width = max(len(placeholder), width)

        style["width"] = int(width) + 2  # add some offset

        return style


def test_selection(root: Union[tk.Tk, tk.Widget]) -> None:
    """test for SelectionWidget"""
    counter = 0

    def callback(self):
        nonlocal counter
        counter += 1
        self.text = "You click {0} times".format(counter)

    selection = SelectionWidget(
        root, placeholder='put the placeholder here',
        entry_options={'tooltip': 'You may add a help here'},
        entry_grid_options={'padx': 5, 'pady': 5},
        button_options={
            'callback': callback, 'text': u'\u25A9',
            'tooltip': 'Click the button to increase counter'
        },
        button_grid_options={'padx': 5, 'pady': 5},
    )
    selection.grid()

    SelectionWidget(root, placeholder='Default settings').grid()


def test_resizable_label(root: Union[tk.Tk, tk.Widget]) -> None:
    """test for ResizableLabel"""
    label_frame = tk.Frame(root)
    label_frame.grid()

    ResizableLabel(
        label_frame, text='initial', weight=0.2,
    ).grid(row=0, column=0)

    ResizableLabel(
        label_frame, weight=0.6,
        text="This is expandable label",
    ).grid(row=0, column=1)

    ResizableLabel(
        label_frame, text='end', weight=0.2,
    ).grid(row=0, column=2)


def test_resizable_label_image(root: Union[tk.Tk, tk.Widget]) -> None:
    """Resizable image test"""
    default_image_path = os.path.join(os.getcwd(), "test.png")
    if not os.path.isfile(default_image_path):
        # If no image found, skip the test
        return
    image_frame = tk.Frame(root)
    image_frame.grid()

    ResizableLabelImage(
        image_frame, weight=(0.4, 0.4),
        image_path=default_image_path
    ).grid(row=0, column=0, sticky=tk.NSEW)

    ResizableLabelImage(
        image_frame, weight=(0.4, 0.4),
        image=Image.open(default_image_path)
    ).grid(row=0, column=1, sticky=tk.NSEW)


def test_resizable_button(root: Union[tk.Tk, tk.Widget]) -> None:
    """Resizable button test"""
    button_frame = tk.Frame(root)
    button_frame.grid()

    ResizableButton(
        button_frame, text='test', weight=0.1,
    ).grid(row=0, column=0, sticky=tk.NSEW)


def test() -> None:
    """the module test"""
    root = tk.Tk()

    test_selection(root)
    test_resizable_label(root)
    test_resizable_label_image(root)
    test_resizable_button(root)

    configure(root, DarkTheme)
    root.mainloop()


if __name__ == "__main__":
    test()
