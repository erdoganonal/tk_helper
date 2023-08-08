"""Includes common used tkinter based widgets

Author: Erdogan Onal
mailto: erdoganonal@windowslive.com
"""
import enum
import os
import random
import string
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.font import Font
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    NoReturn,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeAlias,
    TypeVar,
    Union,
    overload,
)

from PIL import Image, ImageTk

# pylint: disable=too-many-ancestors
# pylint: disable=too-many-lines

LETTERS_AND_DIGITS = string.ascii_letters + string.digits
SAMPLES: Dict[str, str] = {}

_DOCTEST_TIME_MS = 1 * 1000
_MAX_WEIGHT = 10000

_T = TypeVar("_T", bound=tk.Widget)
_GridOptionType: TypeAlias = Dict[str, Union[int, str, Tuple[Union[str, float], Union[str, float]], tk.Misc]]


def with_root(function: Callable[..., Any]) -> Callable[..., None]:
    """helper function for docstrings"""

    def wrapper(*args: Any, **kwargs: Any) -> None:
        timeout = kwargs.pop("timeout", _DOCTEST_TIME_MS)
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
        message = f"Given option[{option}] is not a valid option. Valid options: {', '.join(map(str, options_enum))}"

        super().__init__(message)


class TkRecursionError(TkHelperBaseError, RecursionError):
    """Protection for recursion in resize"""


class Objectless(type):
    """A metaclass to disable instantiation"""

    def __call__(cls) -> NoReturn:
        raise RuntimeError(f"{cls} should not be instantiated")


class WidgetTheme:
    """Theme for a widget. Define configurations to apply.
    >>> WidgetTheme(bg='black').to_dict()
    {'bg': 'black'}

    >>> WidgetTheme(bg='black').keys()
    dict_keys(['bg'])
    """

    def __init__(self, **kwargs: Any) -> None:
        self.__kwargs = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Return the dict representation"""
        return dict(self)

    def keys(self) -> Iterable[str]:
        """Return the keys of the WidgetTheme"""
        return self.__kwargs.keys()

    def __getitem__(self, key: str) -> Any:
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
        name = widget_name.lower().replace("::", "_")
        for key in dir(cls):
            value: WidgetTheme = getattr(cls, key)
            if key.lower() == name:
                return value
        raise AttributeError(f"'{cls!r}' object has no attribute '{widget_name}'")

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
        root_theme = theme.get_theme("root")
        if root_theme is EMPTY_THEME:
            widget.configure(**theme.__default__.to_dict())
        else:
            widget.configure(**root_theme.to_dict())
    elif isinstance(widget, tk.Widget):
        theme_name = widget.widgetName
        widget_theme = theme.get_theme(theme_name)
        if widget_theme is EMPTY_THEME:
            widget_theme = theme.get_theme("__default__")

        if widget.widgetName.startswith("ttk::"):
            style = ttk.Style(widget)
            style.configure(widget.winfo_class(), **widget_theme.to_dict())
        else:
            widget.configure(**widget_theme.to_dict())


def configure(widget: Union[tk.Tk, tk.Widget], theme: Type[Theme] = Theme) -> None:
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
        self.tip_window: Optional[tk.Toplevel] = None

        self.widget.bind("<Enter>", lambda event: self.showtip())
        self.widget.bind("<Leave>", lambda event: self.hidetip())

    def showtip(self) -> None:
        """Display text in tooltip window"""
        x_offset = y_offset = 30

        if self.tip_window or not self.text:
            return

        bbox_result: Tuple[int, int, int, int] = self.widget.bbox("insert")  # type: ignore[call-overload]
        coord_x, coord_y, _, coord_y2 = bbox_result
        coord_x = coord_x + self.widget.winfo_rootx() + x_offset
        coord_y = coord_y + coord_y2 + self.widget.winfo_rooty() + y_offset
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{coord_x}+{coord_y}")
        label = tk.Label(
            self.tip_window,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", "8", "normal"),
        )
        label.pack(ipadx=1)

    def hidetip(self) -> None:
        """Hide the tooltip"""
        if self.tip_window:
            self.tip_window.destroy()

        self.tip_window = None


def create_widget(widget_class: Type[_T], *args: Any, **kwargs: Any) -> _T:
    """Create a widget with custom properties"""

    tooltip = kwargs.pop("tooltip", None)

    widget = widget_class(*args, **kwargs)
    if tooltip:
        AddToolTip(widget, tooltip)

    return widget


def update_and_center(
    root: tk.Tk | tk.Toplevel, other: tk.Misc | None = None, vertical_taskbar_offset: int = 0, horizontal_taskbar_offset: int = 0
) -> None:
    """Update the window and center in the screen"""

    root.update()

    if other:
        x_pos = other.winfo_rootx() + (other.winfo_width() - root.winfo_width()) // 2
        y_pos = other.winfo_rooty() + (other.winfo_height() - root.winfo_height()) // 2
    else:
        x_pos = (root.winfo_screenwidth() - root.winfo_width() - vertical_taskbar_offset) // 2
        y_pos = (root.winfo_screenheight() - root.winfo_height() - horizontal_taskbar_offset) // 2

    root.geometry(f"+{x_pos}" f"+{y_pos}")


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

    def __init__(self, *args: Any, placeholder: str = "", color: str = "grey", **kw: Any):
        super().__init__(*args, **kw)

        self._is_empty = True

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self["fg"]

        self.__bind("<FocusIn>", self.focus_in)
        self.__bind("<FocusOut>", self.focus_out)

        self.put_placeholder()

    def get(self) -> str:
        """Return the text of the entry."""
        if self._is_empty:
            return ""
        return super().get()

    def put_placeholder(self) -> None:
        """Put the place holder"""
        self._is_empty = True
        self.insert(0, self.placeholder, placeholder=True)
        self["fg"] = self.placeholder_color

    def focus_in(self, *_: Any) -> None:
        """Clear placeholder and allow typing"""
        self._is_empty = False

        if self["fg"] == self.placeholder_color:
            self.delete(0, tk.END)
            self["fg"] = self.default_fg_color

    def focus_out(self, *_: Any) -> None:
        """Add placeholder if empty"""
        if not self.get():
            self.put_placeholder()

    def insert(self, *args: Any, **kwargs: Any) -> None:
        """Insert the text"""
        placeholder = kwargs.pop("placeholder", False)
        if not placeholder and self["fg"] == self.placeholder_color:
            self._is_empty = False
            self["fg"] = self.default_fg_color
        super().insert(*args, **kwargs)

    def __bind(
        self,
        sequence: Optional[str] = None,
        func: Optional[Callable[["tk.Event[tk.Misc]"], Any]] = None,
        add: Optional[Union[bool, Literal["", "+"]]] = None,
    ) -> str:
        return super().bind(sequence, func, add)

    def bind(  # type: ignore[override]
        self,
        sequence: Optional[str] = None,
        func: Optional[Callable[["tk.Event[tk.Misc]"], Any]] = None,
        add: Optional[Union[bool, Literal["", "+"]]] = None,
    ) -> str:
        """Bind to this widget at event SEQUENCE a call to function FUNC."""
        # Don't allow to override "<FocusIn>" and "<FocusOut>"
        if sequence in ("<FocusIn>", "<FocusOut>"):
            return sequence
        return self.__bind(sequence, func, add)

    def unbind(self, sequence: str, funcid: Optional[str] = None) -> None:
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
        entry_options:       Options for the entry.
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

    def __init__(
        self,
        master: Union[tk.Tk, tk.Widget],
        *args: Any,
        placeholder: str = "",
        entry_options: Optional[Dict[str, Any]] = None,
        entry_grid_options: Optional[_GridOptionType] = None,
        button_options: Optional[Dict[str, Any]] = None,
        button_grid_options: Optional[_GridOptionType] = None,
        kind: TargetType = TargetType.FILE,
        ratio: Tuple[int, int] = (5, 1),
        **kwargs: Any,
    ):
        super().__init__(master, *args, **kwargs)

        if entry_options is None:
            entry_options = {}

        if entry_grid_options is None:
            entry_grid_options = {}

        if button_options is None:
            button_options = {}

        if button_grid_options is None:
            button_grid_options = {}

        self.entry: tk.Entry
        self.button: tk.Button

        self._kind = kind
        self._placeholder = placeholder

        # pop items to not override
        for key in ["row", "column", "rowspan", "columnspan"]:
            entry_grid_options.pop(key, None)
            button_grid_options.pop(key, None)

        self._place_entry(entry_options, entry_grid_options)
        self._place_button(button_options, button_grid_options)

        self.grid_columnconfigure(0, weight=ratio[0], uniform="foo")
        self.grid_columnconfigure(1, weight=ratio[1], uniform="foo")

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

    def _place_entry(self, options: Dict[str, Any], grid_options: _GridOptionType) -> None:
        default_options = {"placeholder": self._placeholder}
        default_options.update(**options)
        self.entry = create_widget(EntryWithPlaceholder, self, **default_options)

        default_grid_options: _GridOptionType = {
            "row": 0,
            "column": 0,
            "padx": (0, 5),
            "sticky": tk.NSEW,
        }
        default_grid_options.update(grid_options)
        self.entry.grid(None, **default_grid_options)  # type: ignore

    def _place_button(self, options: Dict[str, Any], grid_options: _GridOptionType) -> None:
        if "callback" in options:
            callback = options.pop("callback")

            def command() -> Any:
                return callback(self)

        else:
            command = self.command_handler

        default_options = {"text": "...", "command": command}
        default_options.update(**options)
        self.button = create_widget(tk.Button, self, **default_options)

        default_grid_options: _GridOptionType = {
            "row": 0,
            "column": 1,
            "sticky": tk.NSEW,
        }
        default_grid_options.update(grid_options)
        self.button.grid_configure(**default_grid_options)  # type:ignore


class MultiColumnListbox:
    """use a ttk.TreeView as a multicolumn ListBox"""

    def __init__(
        self,
        master: tk.Misc,
        headers: Sequence[str],
        sort: List[Callable[[Tuple[Any, str]], Any]] | List[bool] | bool | None = None,
    ) -> None:
        self.master = master
        self._headers = list(headers)
        self._columns: Dict[str, List[str]] = {}

        self._setup_widgets(sort=sort)

    def _setup_widgets(self, sort: List[Callable[[Tuple[Any, str]], Any]] | List[bool] | bool | None = None) -> None:
        container = ttk.Frame(self.master)
        container.grid(sticky=tk.NSEW)

        # create a treeview with dual scrollbar
        self.tree = ttk.Treeview(container, columns=self._headers, show="headings", selectmode=tk.BROWSE)
        vsb = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        # hsb = ttk.Scrollbar(orient=tk.HORIZONTAL, command=self.tree.xview)

        self.tree.grid(column=0, row=0, sticky=tk.NSEW, padx=5)
        vsb.grid(column=1, row=0, sticky=tk.NS)

        self.tree.configure(yscrollcommand=vsb.set)
        # self.tree.configure(yscrollcommand=hsb.set)
        # hsb.grid(column=0, row=1, sticky=tk.EW, in_=container)
        container.grid_columnconfigure(0, weight=_MAX_WEIGHT)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        for idx, col in enumerate(self._headers):
            # adjust the column's width to the header string
            self.tree.column(col, width=Font().measure(col.title()))

            if (isinstance(sort, bool) and sort) or (isinstance(sort, list) and isinstance(sort[idx], bool) and sort[idx]):
                self.tree.heading(col, text=col.title(), command=lambda c=col: sortby(self.tree, c, False))  # type: ignore[misc]
            elif sort is not None and isinstance(sort, list) and callable(sort[idx]):
                self.tree.heading(
                    col,
                    text=col.title(),
                    command=lambda c=col, sorter=sort[idx]: sortby(self.tree, c, False, sorter=sorter),  # type: ignore[misc]
                )
            else:
                self.tree.heading(col, text=col.title())

    def add_rows(self, columns_list: Sequence[Sequence[str]], smart_width: bool = True) -> List[str]:
        """Add new rows at the end of the list"""
        item_ids = []
        for columns in columns_list:
            item_id = self.add_row(columns, smart_width=smart_width)
            item_ids.append(item_id)
        return item_ids

    def add_row(self, columns: Sequence[str], smart_width: bool = True) -> str:
        """Add a new row at the end of the list"""
        return self.insert_row(columns, row=-1, smart_width=smart_width)

    def insert_row(self, columns: Sequence[str], row: int, smart_width: bool = True) -> str:
        """Add a new row at the end of the list"""

        if len(columns) != len(self._headers):
            raise ValueError("The length of the columns do not match the length of the headers.")

        item_id = self.tree.insert("", row if row >= 0 else tk.END, values=list(columns))

        if smart_width:
            for idx, val in enumerate(columns):
                col_w = Font().measure(val)
                if self.tree.column(self._headers[idx], width=None) < col_w:  # type: ignore[call-overload]
                    self.tree.column(self._headers[idx], width=col_w)

        self._columns[item_id] = list(columns)
        return item_id

    @overload
    def get_selected(self) -> Optional[Sequence[str]]:
        pass

    @overload
    def get_selected(self, key: str) -> Optional[str]:
        pass

    def get_selected(self, key: Optional[str] = None) -> Sequence[str] | str | None:
        """return the currently selected item"""
        selected = self.tree.selection()
        if len(selected) == 0:
            return None

        items = self.tree.item(selected[0])["values"]
        if key is None:
            return items

        return items[self._headers.index(key)]

    def select_by_column_value(self, column_name: str, column_value: str) -> Optional[str]:
        """Select the treeview item by column.
        Selects the first one if multiple values exists.
        """
        column_idx = self._headers.index(column_name)
        item_id: Optional[str] = None

        for key, column_values in self._columns.items():
            if column_value == column_values[column_idx]:
                item_id = key
                break

        if item_id:
            self.tree.selection_set(item_id)
            self.tree.focus()

        return item_id

    def select_by_column(self, column: Sequence[str]) -> Optional[str]:
        """Select the treeview item by column.
        Selects the first one if multiple values exists.
        """
        item_id: Optional[str] = None

        for key, column_values in self._columns.items():
            if len(column) == len(column_values) and all(l1 == l2 for l1, l2 in zip(column_values, column)):
                item_id = key
                break

        if item_id:
            self.tree.selection_set(item_id)
            self.tree.focus()

        return item_id

    def clear(self) -> None:
        """Clear the list"""
        for item in self._columns:
            self.tree.delete(item)

        self._columns.clear()

    def destroy(self) -> None:
        """Clear the list and destroy the widget"""

        self.clear()
        self._headers.clear()
        self.tree.master.destroy()


def _sorter(item: Tuple[Any, str]) -> Any:
    try:
        return int(item[0])
    except ValueError:
        return item[0]


def sortby(tree: ttk.Treeview, col: int | str, descending: bool, sorter: Callable[[Tuple[Any, str]], Any] = _sorter) -> None:
    """sort tree contents when a column header is clicked on"""
    # grab values to sort
    data = [(tree.set(child, col), child) for child in tree.get_children("")]
    data.sort(reverse=descending, key=sorter)

    for idx, item in enumerate(data):
        tree.move(item[1], "", idx)
    # switch the heading so it will sort in the opposite direction
    tree.heading(col, command=lambda col=col: sortby(tree, col, not descending))


class _ResizableBase(tk.Widget):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._font: Font
        self._width: int = 0
        self.weight_width: float = 0.0
        self.weight_height: float = 0.0
        self._dummy_text: Optional[str] = None
        super().__init__(*args, **kwargs)

    def _init(
        self,
        weight: Union[float, Tuple[float, float]],
        base_font: Font,
        resize: bool = True,
        fix_text_len: int = 0,
    ) -> None:
        """
        A base for resizable widgets.
        """
        self.font = base_font
        try:
            self.weight_width = float(weight[0])  # type: ignore[index]
            self.weight_height = float(weight[1])  # type: ignore[index]
        except (TypeError, IndexError):
            self.weight_width = self.weight_height = float(weight)  # type: ignore[arg-type]

        if resize:
            self.winfo_toplevel().bind("<Configure>", self._resize, add="+")

        self._dummy_text = ""
        self.fix_text_len = fix_text_len
        self._width = self.winfo_toplevel().winfo_width()

    @property
    def font(self) -> Font:
        """return the font information"""
        return self._font

    @font.setter
    def font(self, base_font: Any) -> None:
        """set given font as label font"""
        if isinstance(base_font, Font):
            self._font = base_font
        else:
            # string fonts are not allowed at this widget
            raise ValueError(f"font must be instance of {Font!r}")

    @property
    def fix_text_len(self) -> Optional[int]:
        """Return the length of the text which set before is possible"""
        if self._dummy_text is None:
            return None

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
            random_sample = "".join(random.sample(LETTERS_AND_DIGITS, int(value)))
            SAMPLES[str(value)] = random_sample
        self._dummy_text = random_sample

    def _resize(self, _: Any) -> None:
        text = self._dummy_text or self.cget("text")
        if not text:
            return

        if self.fix_text_len and len(text) < self.fix_text_len:
            text += " " * (len(text) < self.fix_text_len)

        top_level_width = self.winfo_toplevel().winfo_width()
        if top_level_width == 1:
            # If width equals to 1 means that
            # the main window is in initial step.
            return

        expected_width = top_level_width * self.weight_width
        dummy_font = self.font.copy()

        while True:
            current_width = dummy_font.measure(text)
            font_size = dummy_font.actual("size")

            if current_width < expected_width:
                # if current width smaller than expected
                # increase the dummy font size by one
                dummy_font["size"] = font_size + 1
                if dummy_font.measure(text) > expected_width:
                    # if increasing size exceeds the expected,
                    # undo increasing and exit the loop
                    dummy_font["size"] = font_size
                    break
                # still have spaces, so continue
            else:
                # if current width grater than expected
                # decrease the dummy font size by one
                dummy_font["size"] = font_size - 1
                if dummy_font.measure(text) < expected_width:
                    # if it is fit, break the loop
                    break
                # if it is not fit, means we have spaces
                # so, continue

        self.font = dummy_font
        self.configure(font=self.font)  # type: ignore[call-arg]


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

    def __init__(
        self,
        master: Union[tk.Tk, tk.Widget],
        *args: Any,
        weight: float = 1.0,
        resize: bool = True,
        fix_text_len: int = 0,
        **kwargs: Any,
    ):
        base_font = kwargs.pop("font", Font())

        super().__init__(master, *args, **kwargs)
        self._init(weight, base_font, resize, fix_text_len)

    def configure(self, cnf: Any = None, **kwargs: Any) -> None:  # type: ignore[override]
        """override the configure method to capture font"""
        self.font = kwargs.get("font", Font())
        super().configure(cnf, **kwargs)


class ResizableLabelImage(ResizableLabel):
    """A label which can resize
    Args:
        *args
        **kwargs:   Configurations for base class.
        image:      The image to display on the screen.
        image_path: The path of the image.
    """

    @overload
    def __init__(self, *args: Any, image: Image.Image, **kwargs: Any) -> None:
        pass

    @overload
    def __init__(self, *args: Any, image_path: str, **kwargs: Any) -> None:
        pass

    def __init__(
        self,
        *args: Any,
        image: Optional[Image.Image] = None,
        image_path: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if image is not None and image_path is not None:
            raise ValueError("you are allowed to pass only image or image_path")

        self._original: Image.Image

        if image:
            self._original = image
        elif image_path:
            self._original = Image.open(image_path)
        self._resized: Optional[ImageTk.PhotoImage] = None

        super().__init__(*args, **kwargs, image=self._resized)

    def _resize(self, _: Any) -> None:
        min_size = 10
        width = self.winfo_toplevel().winfo_width()
        height = self.winfo_toplevel().winfo_height()
        size = min(
            max(int(width * self.weight_width), min_size),
            max(int(height * self.weight_height), min_size),
        )

        self.set_image(self._original, (size, size))

    def set_image(
        self,
        image: Image.Image,
        image_size: Optional[Tuple[int, int]] = None,
        resample: Literal[0, 1, 2, 3, 4, 5] = Image.Resampling.LANCZOS,  # type: ignore[assignment]
    ) -> None:
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

    def __init__(
        self,
        master: Union[tk.Tk, tk.Widget],
        *args: Any,
        weight: float = 1.0,
        resize: bool = True,
        fix_text_len: int = 0,
        **kwargs: Any,
    ):
        self._font: Font
        base_font = kwargs.pop("font", Font())

        super().__init__(master, *args, **kwargs)
        self._init(weight, base_font, resize, fix_text_len)

    def configure(  # type: ignore[override]
        self, cnf: Dict[str, Any] | None = None, **kwargs: Any
    ) -> Optional[Dict[str, Tuple[str, str, str, Any, Any]]]:
        """override the configure method to capture font"""
        self.font = kwargs.get("font", Font())
        return super().configure(cnf, **kwargs)


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

    def __init__(
        self,
        master: Union[tk.Tk, tk.Widget],
        variable: tk.StringVar,
        *values: str,
        placeholder: Optional[str] = None,
        **kwargs: Any,
    ):
        self._placeholder = placeholder
        if placeholder is None:
            placeholder = values[0]
        super().__init__(master, variable, placeholder, *values, **kwargs)
        self._variable = variable
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
    def _get_option_menu_style(placeholder: str, option_list: Iterable[str]) -> Dict[str, Any]:
        style = {}
        width = max((len(i) for i in option_list))
        width = max(len(placeholder), width)

        style["width"] = int(width) + 2  # add some offset

        return style


# pylint: disable=too-many-arguments
class VerticalScrollFrame(ttk.Frame):
    """A widget container with a vertical scrollbar."""

    def __init__(
        self,
        master: tk.Misc,
        padding: int = 2,
        autohide: bool = False,
        height: int = 200,
        width: int = 300,
        scrollheight: float = None,  # type: ignore[assignment]
        **kwargs: Any,
    ):
        # content frame container
        self.container = ttk.Frame(master=master, relief=tk.FLAT, borderwidth=0, width=width, height=height)
        self.container.bind("<Configure>", lambda _: self.yview())
        self.container.propagate(False)

        # content frame
        super().__init__(master=self.container, padding=padding, **kwargs)
        self.place(rely=0.0, relwidth=1.0, height=scrollheight)

        # vertical scrollbar
        self.vscroll = ttk.Scrollbar(master=self.container, command=self.yview, orient=tk.VERTICAL)
        self.show_scrollbars()

        self.winsys: str = self.tk.call("tk", "windowingsystem")

        # setup autohide scrollbar
        self.autohide = autohide
        if self.autohide:
            self.hide_scrollbars()

        # widget event binding
        self.container.bind("<Enter>", self._on_enter, "+")
        self.container.bind("<Leave>", self._on_leave, "+")
        self.container.bind("<Map>", self._on_map, "+")
        self.bind("<<MapChild>>", self._on_map_child, "+")

        self.bind_all("<MouseWheel>", self.scroll_event, add=True)

        # delegate content geometry methods to container frame
        _methods = vars(tk.Pack).keys() | vars(tk.Grid).keys() | vars(tk.Place).keys()
        for method in _methods:
            if any(["pack" in method, "grid" in method, "place" in method]):
                # prefix content frame methods with 'content_'
                setattr(self, f"content_{method}", getattr(self, method))
                # overwrite content frame methods from container frame
                setattr(self, method, getattr(self.container, method))

    def yview(self, *args: Any) -> None:
        """Update the vertical position of the content frame within the container."""

        if not args:
            first, _ = self.vscroll.get()  # type: ignore[misc]
            self.yview_moveto(fraction=first)
        elif args[0] == "moveto":
            self.yview_moveto(fraction=float(args[1]))
        elif args[0] == "scroll":
            self.yview_scroll(number=int(args[1]), what=args[2])
        else:
            return

    def yview_moveto(self, fraction: float) -> None:
        """Update the vertical position of the content frame within the container.

        fraction (float):
                The relative position of the content frame within the container.
        """
        base, thumb = self._measures()
        if fraction < 0:
            first = 0.0
        elif (fraction + thumb) > 1:
            first = 1 - thumb
        else:
            first = fraction
        self.vscroll.set(first, first + thumb)
        self.content_place(rely=-first * base)  # type: ignore[attr-defined]  # pylint: disable=no-member

    def yview_scroll(self, number: int, what: str) -> None:  # pylint: disable=unused-argument
        """Update the vertical position of the content frame within the container.

        number (int):
            The amount by which the content frame will be moved within the container frame by 'what' units.
        what (str):
            The type of units by which the number is to be interpreted. This parameter is currently not used and is assumed to be 'units'.
        """
        first, _ = self.vscroll.get()  # type: ignore[misc]
        fraction = (number / 100) + first
        self.yview_moveto(fraction)

    def scroll_top(self) -> None:
        """Go to the top of the widget"""
        self.yview_moveto(0.0)

    def scroll_bottom(self) -> None:
        """Go to the bottom of the widget"""
        self.yview_moveto(1.0)

    @staticmethod
    def _get_parent(widget: tk.Misc) -> Optional[ttk.Frame]:
        while widget.master:
            widget = widget.master
            if isinstance(widget, ttk.Frame):
                return widget

        return None

    def _has_same_widget(self, widget: tk.Misc) -> bool:
        try:
            if widget.winfo_toplevel() is not self.winfo_toplevel():
                raise tk.TclError
        except tk.TclError:
            return False

        while widget:
            if self is widget:
                return True
            widget = self._get_parent(widget)  # type: ignore[assignment]

        return widget is not None

    def scroll_event(self, event: "tk.Event[tk.Misc]") -> None:
        """Allow to scroll with mouse"""
        if not self._has_same_widget(event.widget):
            return
        number = -1 * (event.delta // 120)
        self.yview_scroll(number, tk.UNITS)

    def enable_scrolling(self) -> None:
        """Enable mousewheel scrolling on the frame and all of its children."""
        widgets: Iterable[tk.Widget] = [self, *self.winfo_children()]
        for widget in widgets:
            bindings = widget.bind()
            if self.winsys.lower() == "x11":
                if "<Button-4>" in bindings or "<Button-5>" in bindings:
                    continue
                widget.bind("<Button-4>", self._on_mousewheel, "+")
                widget.bind("<Button-5>", self._on_mousewheel, "+")
            else:
                if "<MouseWheel>" not in bindings:
                    widget.bind("<MouseWheel>", self._on_mousewheel, "+")

    def disable_scrolling(self) -> None:
        """Disable mousewheel scrolling on the frame and all of its children."""
        widgets: Iterable[tk.Widget] = [self, *self.winfo_children()]
        for widget in widgets:
            if self.winsys.lower() == "x11":
                widget.unbind("<Button-4>")
                widget.unbind("<Button-5>")
            else:
                widget.unbind("<MouseWheel>")

    def hide_scrollbars(self) -> None:
        """Hide the scrollbars."""
        self.vscroll.pack_forget()

    def show_scrollbars(self) -> None:
        """Show the scrollbars."""
        self.vscroll.pack(side=tk.RIGHT, fill=tk.Y)

    def autohide_scrollbar(self) -> None:
        """Toggle the autohide functionality. Show the scrollbars when
        the mouse enters the widget frame, and hide when it leaves the
        frame."""
        self.autohide = not self.autohide

    def _measures(self) -> Tuple[float, float]:
        """Measure the base size of the container and the thumb size
        for use in the yview methods"""
        outer = self.container.winfo_height()
        inner = max([self.winfo_height(), outer])
        base = inner / outer
        if inner == outer:
            thumb = 1.0
        else:
            thumb = outer / inner
        return base, thumb

    def _on_map_child(self, _: "tk.Event[Any]") -> None:
        """Callback for when a widget is mapped to the content frame."""
        if self.container.winfo_ismapped():
            self.yview()

    def _on_enter(self, _: "tk.Event[Any]") -> None:
        """Callback for when the mouse enters the widget."""
        self.enable_scrolling()
        if self.autohide:
            self.show_scrollbars()

    def _on_leave(self, _: "tk.Event[Any]") -> None:
        """Callback for when the mouse leaves the widget."""
        self.disable_scrolling()
        if self.autohide:
            self.hide_scrollbars()

    def _on_configure(self, _: "tk.Event[Any]") -> None:
        """Callback for when the widget is configured"""
        self.yview()

    def _on_map(self, _: "tk.Event[Any]") -> None:
        self.yview()

    def _on_mousewheel(self, event: "tk.Event[Any]") -> None:
        """Callback for when the mouse wheel is scrolled."""
        if self.winsys.lower() == "win32":
            delta = -int(event.delta / 120)
        elif self.winsys.lower() == "aqua":
            delta = -event.delta
        elif event.num == 4:
            delta = -10
        elif event.num == 5:
            delta = 10
        self.yview_scroll(delta, tk.UNITS)


def test_selection(root: Union[tk.Tk, tk.Widget]) -> None:
    """test for SelectionWidget"""
    counter = 0

    def callback(self: SelectionWidget) -> None:
        nonlocal counter
        counter += 1
        self.text = f"You click {counter} times"

    selection = SelectionWidget(
        root,
        placeholder="put the placeholder here",
        entry_options={"tooltip": "You may add a help here"},
        entry_grid_options={"padx": 5, "pady": 5},
        button_options={
            "callback": callback,
            "text": "\u25A9",
            "tooltip": "Click the button to increase counter",
        },
        button_grid_options={"padx": 5, "pady": 5},
    )
    selection.grid()

    SelectionWidget(root, placeholder="Default settings").grid()


def test_resizable_label(root: Union[tk.Tk, tk.Widget]) -> None:
    """test for ResizableLabel"""
    label_frame = tk.Frame(root)
    label_frame.grid()

    ResizableLabel(
        label_frame,
        text="initial",
        weight=0.2,
    ).grid(row=0, column=0)

    ResizableLabel(
        label_frame,
        weight=0.6,
        text="This is expandable label",
    ).grid(row=0, column=1)

    ResizableLabel(
        label_frame,
        text="end",
        weight=0.2,
    ).grid(row=0, column=2)


def test_resizable_label_image(root: Union[tk.Tk, tk.Widget]) -> None:
    """Resizable image test"""
    default_image_path = os.path.join(os.getcwd(), "test.png")
    if not os.path.isfile(default_image_path):
        # If no image found, skip the test
        return
    image_frame = tk.Frame(root)
    image_frame.grid()

    ResizableLabelImage(image_frame, weight=(0.4, 0.4), image_path=default_image_path).grid(row=0, column=0, sticky=tk.NSEW)

    ResizableLabelImage(image_frame, weight=(0.4, 0.4), image=Image.open(default_image_path)).grid(row=0, column=1, sticky=tk.NSEW)


def test_resizable_button(root: Union[tk.Tk, tk.Widget]) -> None:
    """Resizable button test"""
    button_frame = tk.Frame(root)
    button_frame.grid()

    ResizableButton(
        button_frame,
        text="test",
        weight=0.1,
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
