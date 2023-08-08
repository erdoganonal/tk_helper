"""Renders a widget using tk.Canvas module to
busy the screen for a while
"""
import abc
import enum
import math
import string
import tkinter as tk
from collections import deque
from dataclasses import dataclass
from tkinter.font import Font
from typing import Any, Callable, Deque, Dict, Generator, Iterable, List, Optional, Tuple, Type, TypeAlias, Union

from colour import Color  # type:ignore[import]

FULL_CIRCLE_DEGREE = 360

_ColorType: TypeAlias = Tuple[str, str, str, str, str, str, str, str]

# pylint: disable=too-many-ancestors
# pylint: disable=too-many-lines


def _change_text(root: tk.Misc, label: tk.Label, *p_bars: "CircularLoadingBarBase", remaining_time: int = 2) -> None:
    """helper function for docstrings"""
    for p_bar in p_bars:
        if not p_bar.is_active:
            p_bar.start()
    label.config(text=f"Bar will be stopped in {remaining_time} seconds")
    if remaining_time <= 0:
        for p_bar in p_bars:
            p_bar.stop()
        label.config(text="The window will be destroyed in a second")
        root.after(1000, root.destroy)
    else:
        root.after(1000, lambda: _change_text(root, label, *p_bars, remaining_time=remaining_time - 1))


class InconsistentLengths(Exception):
    """Raise when MaskItem lengths are not match"""

    def __init__(self, expected_length: int, actual_length: int):
        super().__init__(f"Expected length of {expected_length}, got {actual_length}")


class _EnumBase(enum.Enum):
    @classmethod
    def raise_bad_value(cls, value: Any, safe: bool = False) -> None:
        """raises ValueError when given value is not valid"""
        if safe:
            try:
                if value in cls:
                    return
            except TypeError:
                pass
        values = [repr(item) for item in cls]

        other_value = ""
        if len(values) > 1:
            values, other_value = values[:-1], values[-1]
            other_value = f" or {other_value}"
        raise ValueError(f'bad value "{value!r}": expected {", ".join(values)}{other_value}')


class ResizeActions(_EnumBase):
    """Actions for resize"""

    ADD = "add"
    SET = "set"
    SUB = "subtract"


class AngleType(_EnumBase):
    """Angle types"""

    DEGREE = "degree"
    RADIAN = "radian"


# pylint: disable=too-few-public-methods
class Colors:
    """Holds pre-defined 8 length color range"""

    GRAYED = ("#fafafa", "#f5f5f5", "#e0e0e0", "#bdbdbd", "#9e9e9e", "#757575", "#616161", "#424242")
    RAINBOW = ("#fff100", "#ff8c00", "#e81123", "#4b0082", "#000080", "#00188f", "#00b294", "#bad80a")
    BLACK = ("black", "black", "black", "black", "black", "black", "black", "black")


class Converter:
    """Math calculations between circles"""

    @staticmethod
    def centered_circle_to_circle(center_x: int, center_y: int, radius: float) -> Tuple[int, int, float]:
        """Converts centered_circle to circle"""
        return int(center_x - radius), int(center_y - radius), radius

    @classmethod
    def centered_circle_to_oval(cls, center_x: int, center_y: int, radius: float) -> Tuple[int, int, int, int]:
        """Converts centered circle to oval"""
        return cls.circle_to_oval(*cls.centered_circle_to_circle(center_x, center_y, radius))

    @staticmethod
    def circle_to_oval(start_x: int, start_y: int, radius: float) -> Tuple[int, int, int, int]:
        """Converts circle to oval"""
        diameter = int(2 * radius)
        end_x = start_x + diameter
        end_y = start_y + diameter
        return start_x, start_y, end_x, end_y

    @staticmethod
    def oval_to_circle(start_x: int, start_y: int, end_x: int, end_y: int) -> Tuple[int, int, float]:
        """Converts oval to circle"""
        assert end_x == end_y, "Oval must be circle"
        return start_x, start_y, (end_x - start_x) / 2

    @staticmethod
    def circle_to_centered_circle(start_x: int, start_y: int, radius: float) -> Tuple[int, int, float]:
        """Converts circle to centered circle"""
        return int(start_x + radius), int(start_y + radius), radius

    @classmethod
    def oval_to_centered_circle(cls, start_x: int, start_y: int, end_x: int, end_y: int) -> Tuple[int, int, float]:
        """Converts oval to centered circle"""
        return cls.circle_to_centered_circle(*cls.oval_to_circle(start_x, start_y, end_x, end_y))


_MaskItemTest = type("_MaskItemTest", (), {})
_MaskItemTest.test_method = staticmethod(lambda test_param: print(test_param.copy()))  # type: ignore[attr-defined]


class MaskItem:
    """An item for the mask. This is actually a mask to apply
    on the items for every loop.
        Args:
            method_name: The function name of the target class
            **kwargs:    Key-value pair. Key is the parameter name
                         of the target function which passed with
                         first parameter. Value is an iterable. Will
                         be applied by index.
        >>> mask = MaskItem(
        ...     method_name='test_method', test_param=range(10)
        ... )
        >>> method = getattr(_MaskItemTest(), mask.name)
        >>> method(**getattr(mask, '_kwargs'))
        deque([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    """

    def __init__(self, method_name: str, **kwargs: Any):
        self._method_name = method_name
        self._kwargs: Dict[str, Deque[Any]] = {}

        length = None
        for key, value in kwargs.items():
            value = deque(value)
            if length is None:
                length = len(value)
            elif length != len(value):
                raise InconsistentLengths(length, len(value))
            self._kwargs[key] = value

    @property
    def name(self) -> str:
        """Returns the method name which will be called from given object"""
        return self._method_name

    def rotate(self, rotate_by: int = 1) -> None:
        """Shift entire mask items by one"""
        for value in self._kwargs.values():
            value.rotate(rotate_by)

    def __len__(self) -> int:
        for value in self._kwargs.values():
            return len(value)
        return 0

    def __iter__(self) -> Generator[Tuple[str, Any], None, None]:
        for key, value in self._kwargs.items():
            yield key, value

    def __str__(self) -> str:
        string_result = f"Method name: {self.name}\n"
        for param, value in self._kwargs.items():
            string_result += f"\t{param}: {value}\n"
        return string_result


class Mask(list[MaskItem]):
    """
    A list that includes masks.
        Args:
            *args: List of MaskItems
    """

    def __init__(self, *args: MaskItem, rotate_by: int = 1):
        super().__init__(args)
        self.rotate_by = rotate_by

    def apply(self, obj: "CircularLoadingBarBase") -> None:
        """Apply the mask on given items"""
        for idx, item_id in enumerate(obj.items):
            for mask_item in self:
                method = getattr(obj, mask_item.name)
                for param, value in mask_item:
                    method(item_id, **{param: value[idx]})

        self.rotate(self.rotate_by)

    def rotate(self, rotate_by: int = 1) -> None:
        """Shift the mask by one"""
        for mask_item in self:
            mask_item.rotate(rotate_by)

    def __len__(self) -> int:
        length = None
        for mask_item in self:
            if length is None:
                length = len(mask_item)
            elif length != len(mask_item):
                raise InconsistentLengths(length, len(mask_item))
        return length or 0

    def __str__(self) -> str:
        return "\n".join(str(i) for i in self)


@dataclass(frozen=True)
class ProgressOptions:
    """Options for progress"""

    stop_bar_when_max: bool = False
    stop_callback: Optional[Callable[[], Any]] = None
    destroy_when_max: bool = False
    destroy_callback: Optional[Callable[[], Any]] = None
    color: str = "black"
    font: Union[str, Font] = "Helvetica 15 bold"


class CircularLoadingBarBase(tk.Canvas, metaclass=abc.ABCMeta):
    """Base for loading bar

        Args:
            *args
            **kwargs: Parameters for tk.Canvas module
            size:     If passed, the width and height of canvas will be
                      set the this value.
            shift:    Shift the position by this.

        >>> CircularLoadingBarBase()
        Traceback (most recent call last):
            ...
        TypeError: Can't instantiate abstract class \
CircularLoadingBarBase with abstract methods items, update_bar
    """

    def __init__(
        self,
        *canvas_args: Any,
        mask: Mask,
        size: Optional[int] = None,
        shift: int = 0,
        progress_options: Optional[ProgressOptions] = None,
        **canvas_kwargs: Any,
    ) -> None:
        if size is None:
            size = 250

        canvas_kwargs["width"] = canvas_kwargs["height"] = size

        super().__init__(*canvas_args, **canvas_kwargs)

        self.shift = shift
        self._is_active = False
        self._text_id: Optional[int] = None
        self._progress = 0.0
        self._progress_options = progress_options
        self.mask = mask

    @property
    def mask(self) -> Mask:
        """Return the mask"""
        return self._mask

    @mask.setter
    def mask(self, mask: Mask) -> None:
        """Set the mask"""
        if isinstance(mask, Mask):
            self._mask = mask
        else:
            raise ValueError(f"mask should be instance of {Mask!r}")

    @property
    @abc.abstractmethod
    def items(self) -> List[int]:
        """Returns the items that the mask will be applied to."""

    @staticmethod
    def get_sequence(start: float, stop: float, count: float) -> Generator[float, None, None]:
        """Returns a generator that yields points between start and stop.
        The start point is included and the stop point is not. [start, stop)
        Step will be calculated based on count.

        Args:
            start: Start point of the process. Will be yielded first.
            stop: End point of the process. Will not be yielded.
            count: How many point you need.

        >>> list(CircularLoadingBarBase.get_sequence(0, 10, 10))
        [0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]

        # Divide circle to 8 equal pieces
        >>> list(CircularLoadingBarBase.get_sequence(0, 360, 8))
        [0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]
        """
        step = (stop - start) / count
        counter = 0
        next_number = start
        while counter < count:
            counter += 1
            yield next_number
            next_number += step

    @staticmethod
    def to_float(num: float, precision: int = 10) -> float:
        """Since π cannot be represented exactly as a floating-point number,
        some math operations like math.cos(math.pi/2) gives you
        something like 6.123233995736766e-17 instead 0. This function deals
        with that kind of operations
        >>> math.cos(math.pi/2)
        6.123233995736766e-17

        >>> CircularLoadingBarBase.to_float(math.cos(math.pi/2))
        0.0
        """
        precision = 10**precision
        return int(num * precision) / precision

    @classmethod
    def polar_to_cartesian(cls, radius: float, angle: float, kind: AngleType = AngleType.DEGREE) -> Tuple[float, float]:
        """Calculates the cartesian coordinates from polar coordinates.
        Args:
            radius: The radius of the polar coordinates
            angle:  The angle of the polar coordinates
            kind:   Could be degree or radian.
        Formula:
            x = radius + radius * sin(alpha)
            y = radius - radius * cos(alpha)

        >>> CircularLoadingBarBase.polar_to_cartesian(10, 90)
        (20.0, 10.0)

        >>> CircularLoadingBarBase.polar_to_cartesian(
        ...     10, math.pi/2, AngleType.RADIAN
        ... )
        (20.0, 10.0)

        >>> CircularLoadingBarBase.polar_to_cartesian(
        ...     10, math.pi/4, AngleType.RADIAN
        ... )
        (17.071067811, 2.9289321889999997)

        >>> CircularLoadingBarBase.polar_to_cartesian(10, 45)
        (17.071067811, 2.9289321889999997)
        """
        if kind == AngleType.DEGREE:
            angle = math.radians(angle)
        elif kind == AngleType.RADIAN:
            pass
        else:
            AngleType.raise_bad_value(kind)

        cartesian_x = radius * (1 + cls.to_float(math.sin(angle)))
        cartesian_y = radius * (1 - cls.to_float(math.cos(angle)))

        return cartesian_x, cartesian_y

    @property
    def is_active(self) -> bool:
        """return True if bar is active, False otherwise"""
        return self._is_active

    @property
    def fit_size(self) -> int:
        """return the size to fit the widget"""
        return min(self.winfo_width(), self.winfo_height())

    @abc.abstractmethod
    def update_bar(self) -> None:
        """updates the loading bar attributes"""

    def _add_progress_text(self) -> None:
        if self._text_id is not None:
            raise RuntimeError("Progress text already created")

        if self._progress_options is None:
            return

        self._text_id = self.create_text(
            int(self.cget("width")) / 2,
            int(self.cget("width")) / 2,
            text="00.00",
            fill=self._progress_options.color,
            font=self._progress_options.font,
            anchor=tk.CENTER,
        )

    def update_progress(self, update_by: float = 1.0) -> float:
        """updates the loading progress"""
        if self._progress_options is None or self._text_id is None:
            return -1

        self._progress += update_by
        if self._progress > 100:
            if self._progress_options.stop_bar_when_max:
                self.stop()
                if self._progress_options.stop_callback:
                    self._progress_options.stop_callback()
            if self._progress_options.destroy_when_max:
                self.destroy()
                if self._progress_options.destroy_callback:
                    self._progress_options.destroy_callback()
        else:
            self.itemconfigure(self._text_id, text=f"{self._progress:.2f}")

        return self._progress

    def _start(self, interval_ms: int) -> None:
        if not self.is_active:
            return

        self.update_bar()
        self.mask.apply(self)
        self.after(interval_ms, self._start, interval_ms)

    def start(self, interval_ms: int = 100) -> None:
        """starts the circle loading bar"""
        if self.is_active:
            return

        if self._progress_options is not None:
            self._add_progress_text()

        self._is_active = True
        self._start(interval_ms=interval_ms)

    def stop(self) -> None:
        """stop the bar"""
        self._progress = 0.0
        self._text_id = None
        self._is_active = False

    def create_centered_circle(self, center_x: int, center_y: int, radius: float, **kwargs: Any) -> int:
        """Create a circle with given radius and coordinates
        that pointing the center of the circle

        Args:
            center_x: x coordinate of the circle in cartesian system
            center_y: y coordinate of the circle in cartesian system
            radius:   Radius of the circle
        Returns:
            id of the created circle
        """
        return self.create_oval(Converter.centered_circle_to_oval(center_x, center_y, radius), **kwargs)

    def create_circle(self, start_x: int, start_y: int, radius: float, **kwargs: Any) -> int:
        """Create a circle with given radius and place to given coordinates
        Args:
            start_x: x origin point of the square which includes the circle
            start_y: y origin point of the square which includes the circle
            radius:  Radius of the circle
        Returns:
            id of the created circle
        """
        return self.create_oval(Converter.circle_to_oval(start_x, start_y, radius), **kwargs)

    def resize(self, item_id: int, radius: float, action: ResizeActions = ResizeActions.SET) -> None:
        """Resize given circle. New radius will be applied based on the action
        Args:
            item_id: Id of the circle
            radius:  New value to apply on the radius
            action:  The action to apply on the old radius
        """
        start_x, start_y, end_x, end_y = self.coords(item_id)

        old_radius = self.to_float((end_x - start_x) / 2, 1)

        if action == ResizeActions.SET:
            # set new radius
            pass
        elif action == ResizeActions.ADD:
            radius += old_radius
        elif action == ResizeActions.SUB:
            radius = old_radius - radius
        else:
            ResizeActions.raise_bad_value(action)

        end_x = start_x + 2 * radius
        end_y = start_y + 2 * radius

        self.coords(item_id, start_x, start_y, end_x, end_y)

    def __del__(self) -> None:
        try:
            self.stop()
            self.update()
        except AttributeError:
            pass


class SpinningCirclesLoadingBarBase(CircularLoadingBarBase):
    """Creates an circular loading bar which consisting circles

    Args:
        *args
        **kwargs: Parameters for SpinningCirclesLoadingBarBase module
        mask:     The list will be applied and rotated every loop.
        offset:   The offset value to avoid inner circle overflow.
    """

    def __init__(
        self,
        *canvas_args: Any,
        offset: Optional[int] = None,
        mask: Mask,
        size: Optional[int] = None,
        shift: int = 0,
        progress_options: Optional[ProgressOptions] = None,
        **canvas_kwargs: Any,
    ) -> None:
        super().__init__(*canvas_args, mask=mask, size=size, shift=shift, progress_options=progress_options, **canvas_kwargs)

        self.circles: List[int] = []
        self.offset = offset

    @property
    def items(self) -> List[int]:
        return self.circles

    def update_bar(self) -> None:
        width = self.fit_size / 2
        radius = width / 8
        offset = self.offset or 20

        for item_id in self.circles:
            self.delete(item_id)
        self.circles = []

        for angle in self.get_sequence(0, FULL_CIRCLE_DEGREE, len(self.mask)):
            coordinate_x, coordinate_y = self.polar_to_cartesian(width - radius - offset, angle)
            self.circles.append(
                self.create_centered_circle(
                    int(coordinate_x + self.shift + radius + offset),
                    int(coordinate_y + self.shift + radius + offset),
                    radius,
                )
            )


class SpinnerLoadingBar(SpinningCirclesLoadingBarBase):
    """Renders a widget using tk.Canvas module to
    busy the screen for a while. This will give you
    a circle loading bar.

    Usage:
        >>> root = tk.Tk()
        >>> root.title("SpinnerLoadingBar")
        ''
        >>> label = tk.Label()
        >>> label.grid()
        >>> bar1 = SpinnerLoadingBar(root, size=200, colors=Colors.GRAYED)
        >>> bar1.grid()
        >>> bar2 = SpinnerLoadingBar(root, size=200)
        >>> bar2.grid()
        >>> _change_text(root, label, bar1, bar2)

        >>> root.mainloop()
    """

    def __init__(
        self,
        *canvas_args: Any,
        colors: _ColorType = Colors.RAINBOW,
        size: Optional[int] = None,
        mask: Optional[Mask] = None,
        shift: int = 0,
        progress_options: Optional[ProgressOptions] = None,
        **canvas_kwargs: Any,
    ) -> None:
        mask = mask or Mask(MaskItem("itemconfig", fill=colors))
        super().__init__(*canvas_args, size=size, shift=shift, mask=mask, progress_options=progress_options, **canvas_kwargs)


class SpinnerSizedLoadingBar(SpinningCirclesLoadingBarBase):
    """Renders a widget using tk.Canvas module to
    busy the screen for a while. This will give you
    a circular loading bar.

    Usage:
        >>> root = tk.Tk()
        >>> root.title("SpinnerSizedLoadingBar")
        ''
        >>> label = tk.Label()
        >>> label.grid()
        >>> bar = SpinnerSizedLoadingBar(root, size=200)
        >>> bar.grid()

        >>> _change_text(root, label, bar)
        >>> root.mainloop()
    """

    def __init__(
        self,
        *canvas_args: Any,
        size: Optional[int] = None,
        mask: Optional[Mask] = None,
        shift: int = 0,
        colors: _ColorType = Colors.BLACK,
        progress_options: Optional[ProgressOptions] = None,
        **canvas_kwargs: Any,
    ) -> None:
        min_radius = 5
        circles = 8
        resize_mask = range(min_radius, min_radius + circles)
        default_mask = Mask(
            MaskItem("resize", radius=resize_mask),
            MaskItem("itemconfig", fill=colors),
        )

        mask = mask or default_mask
        super().__init__(*canvas_args, size=size, mask=mask, shift=shift, progress_options=progress_options, **canvas_kwargs)


class CircleLoadingBar(CircularLoadingBarBase):
    """Creates a loading bar with color range

    >>> root = tk.Tk()
    >>> root.title("CircleLoadingBar")
    ''
    >>> label = tk.Label()
    >>> label.grid()
    >>> bar = CircleLoadingBar(
    ...     root, size=200, symmetric=True,
    ...     color1='blue', color2='red'
    ... )
    >>> bar.grid()
    >>> bar.start(interval_ms=8)
    >>> _change_text(root, label, bar)
    >>> root.mainloop()
    """

    DTF_COLOR1 = "#0091c7"
    DTF_COLOR2 = "red"

    def __init__(
        self,
        *canvas_args: Any,
        width: int = 10,
        color1: Optional[str] = None,
        color2: Optional[str] = None,
        steps: int = 180,
        color_range: Optional[Iterable[str]] = None,
        symmetric: bool = True,
        size: Optional[int] = None,
        shift: int = 0,
        progress_options: Optional[ProgressOptions] = None,
        **canvas_kwargs: Any,
    ) -> None:
        if color_range and (color1 or color2):
            raise ValueError("You are not allowed to pass color_range and colors at the same time")

        if color1 is None:
            color1 = self.DTF_COLOR1

        if color2 is None:
            color2 = self.DTF_COLOR2

        self.arcs: List[int] = []
        if color_range is None:
            if symmetric:
                colors = list(self.get_range(color1, color2, int(steps / 2)))
                color_range = colors + colors[-2::-1]
            else:
                color_range = self.get_range(color1, color2, steps)
        mask = Mask(MaskItem("itemconfig", outline=color_range), rotate_by=-1)

        self.width = width
        self.oval1_id = 0
        self.oval2_id = 0

        super().__init__(*canvas_args, size=size, mask=mask, shift=shift, progress_options=progress_options, **canvas_kwargs)

    @property
    def items(self) -> List[int]:
        return self.arcs

    def update_bar(self) -> None:
        outer_circle_offset = self.width
        inner_circle_offset = self.width * 2
        if self.oval1_id:
            self.delete(self.oval1_id)
        if self.oval2_id:
            self.delete(self.oval2_id)

        self.oval1_id = self.create_oval(
            outer_circle_offset - self.width / 2,
            outer_circle_offset - self.width / 2,
            self.fit_size - outer_circle_offset + self.width / 2,
            self.fit_size - outer_circle_offset + self.width / 2,
        )

        self.oval2_id = self.create_oval(
            inner_circle_offset - self.width / 2,
            inner_circle_offset - self.width / 2,
            self.fit_size - inner_circle_offset + self.width / 2,
            self.fit_size - inner_circle_offset + self.width / 2,
        )

        self._create_loading_arc(
            outer_circle_offset,
            outer_circle_offset,
            self.fit_size - outer_circle_offset,
            self.fit_size - outer_circle_offset,
            width=self.width,
        )

    @staticmethod
    def get_range(color1: str, color2: str, steps: int) -> Generator[str, None, None]:
        """range of color"""
        for color in Color(color1).range_to(color2, steps):
            yield color.get_hex()

    def _create_loading_arc(self, *bbox: int, width: float, **kwargs: Any) -> None:
        color_range = len(self._mask)

        start = 0.0
        extent = FULL_CIRCLE_DEGREE / color_range

        for arc_id in self.arcs:
            self.delete(arc_id)

        self.arcs = []
        for _ in range(len(self.mask)):
            self.arcs.append(
                self.create_arc(
                    *bbox,
                    start=start,
                    width=width,
                    extent=extent,
                    style="arc",
                    **kwargs,
                )
            )
            start += extent


class TransparentSpinnerBar:
    """
    Places a transparent loading bar

    Args:
        root[tk.Widget]: A widget to place the loading bar top of it
        kind[CircularLoadingBarBase]: Type of the loading bar. Should be
                                    instance of CircularLoadingBarBase.
        location[
            Location        : The Location enumeration. Places the loading bar given place.
            Tuple[int, int] : x and y coordinates. Places the loading bar given place.
        ]: Optional. Location of the loading bar. Could be Location or Tuple.
        kwargs: Keyword arguments for the loading bar.

    >>> root = tk.Tk()
    >>> root.title("TransparentSpinnerBar")
    ''
    >>> label = tk.Label()
    >>> label.grid()
    >>> text = tk.Text(root)
    >>> text.insert("1.0", string.ascii_letters * 50)
    >>> text.grid()
    >>> bar = TransparentSpinnerBar(text, kind=SpinnerSizedLoadingBar)
    >>> _change_text(root, label, bar)
    >>> root.mainloop()
    """

    _TRANSPARENT_COLOR = "white"

    class Location(_EnumBase):
        """An enum for positioning the transparent loading bar"""

        LEFT_TOP = "lt"
        LEFT_CENTER = "lc"
        LEFT_BOTTOM = "lb"

        MIDDLE_TOP = "mt"
        MIDDLE_CENTER = "mc"
        MIDDLE_BOTTOM = "mb"

        RIGHT_TOP = "rt"
        RIGHT_CENTER = "rc"
        RIGHT_BOTTOM = "rb"

        @classmethod
        def is_top(cls, value: Any) -> bool:
            """Returns True if given value places at the top, False otherwise"""
            return value in (cls.LEFT_TOP, cls.MIDDLE_TOP, cls.RIGHT_TOP)

        @classmethod
        def is_middle(cls, value: Any) -> bool:
            """Returns True if given value places at the middle, False otherwise"""
            return value in (cls.MIDDLE_TOP, cls.MIDDLE_CENTER, cls.MIDDLE_BOTTOM)

        @classmethod
        def is_bottom(cls, value: Any) -> bool:
            """Returns True if given value places at the bottom, False otherwise"""
            return value in (cls.LEFT_BOTTOM, cls.MIDDLE_BOTTOM, cls.RIGHT_BOTTOM)

        @classmethod
        def is_left(cls, value: Any) -> bool:
            """Returns True if given value places at the left, False otherwise"""
            return value in (cls.LEFT_TOP, cls.LEFT_CENTER, cls.LEFT_BOTTOM)

        @classmethod
        def is_center(cls, value: Any) -> bool:
            """Returns True if given value places at the center, False otherwise"""
            return value in (cls.LEFT_CENTER, cls.MIDDLE_CENTER, cls.RIGHT_CENTER)

        @classmethod
        def is_right(cls, value: Any) -> bool:
            """Returns True if given value places at the right, False otherwise"""
            return value in (cls.RIGHT_TOP, cls.RIGHT_CENTER, cls.RIGHT_BOTTOM)

    def __init__(
        self,
        root: Union[tk.Widget, tk.Tk],
        kind: Type[CircularLoadingBarBase],
        location: Optional[Union[Location, Tuple[int, int]]] = Location.MIDDLE_CENTER,
        **kwargs: Any,
    ) -> None:
        self._root = root
        self.location = location
        self._main_window: Optional[tk.Toplevel] = None
        self._loading_bar: Optional[CircularLoadingBarBase] = None
        self.kind = kind

        # Override background color
        kwargs["background"] = kwargs["bg"] = kwargs["highlightbackground"] = self._TRANSPARENT_COLOR
        self.kwargs = kwargs

        self._root.winfo_toplevel().protocol("WM_DELETE_WINDOW", self._handle_destroy)

    def _init(self) -> None:
        if self.is_active:
            raise RuntimeError("The bar is already running")

        self._main_window = tk.Toplevel(self._root.winfo_toplevel())
        self._loading_bar = self.kind(self._main_window, **self.kwargs)
        self._loading_bar.grid()

        # TODO: Check for platform dependency  # pylint: disable=fixme # It is not going to fix in a short term.
        self._main_window.overrideredirect(True)  # Remove the title and border
        self._main_window.wm_attributes("-transparentcolor", self._TRANSPARENT_COLOR)

    def _get_coordinates(self) -> Tuple[int, int]:
        """Please refer following schema for positioning"""
        # =============================================================== #
        # *        |      LEFT      #       MIDDLE      #      RIGHT      #
        # =============================================================== #
        #          |      left_x    #      middle_x     #      right_x    #
        # *   TOP  |                                                      #
        #          |      top_y     #      top_y        #      top_y      #
        # --------------------------------------------------------------- #
        #          |      left_x    #      middle_x     #      right_x    #
        # * CENTER |                                                      #
        #          |      center_y  #      center_y     #      center_y   #
        # ----------------------------------------------------------------#
        #          |      left_x    #      middle_x     #      right_x    #
        # * BOTTOM |                                                      #
        #          |      bottom_y  #      bottom_y     #      bottom_y   #
        # =============================================================== #

        try:
            self.Location.raise_bad_value(self.location, safe=True)
        except ValueError:
            # if exact location passed, no need to calculate
            return self.location  # type: ignore[return-value]

        if self._loading_bar is None:
            raise RuntimeError("Cannot get coordinates of uninitialized window")

        left_x = self._root.winfo_rootx()
        middle_x = int(self._root.winfo_rootx() + self._root.winfo_width() / 2 - self._loading_bar.fit_size / 2)
        right_x = int(self._root.winfo_rootx() + self._root.winfo_width() - self._loading_bar.fit_size)

        top_y = self._root.winfo_rooty()
        center_y = int(self._root.winfo_rooty() + self._root.winfo_height() / 2 - self._loading_bar.fit_size / 2)
        bottom_y = int(self._root.winfo_rooty() + self._root.winfo_height() - self._loading_bar.fit_size)

        x_coord = y_coord = 0

        if self.Location.is_left(self.location):
            x_coord = left_x
        elif self.Location.is_middle(self.location):
            x_coord = middle_x
        elif self.Location.is_right(self.location):
            x_coord = right_x

        if self.Location.is_top(self.location):
            y_coord = top_y
        elif self.Location.is_center(self.location):
            y_coord = center_y
        elif self.Location.is_bottom(self.location):
            y_coord = bottom_y

        return x_coord, y_coord

    def _locate(self) -> None:
        try:
            coord_x, coord_y = self._get_coordinates()
        except tk.TclError:
            return

        if self._main_window is None:
            raise RuntimeError("Cannot locate uninitialized window")

        self._main_window.geometry(f"+{coord_x}+{coord_y}")
        if self.is_active:
            self._main_window.after(1, self._locate)

    def _to_top(self) -> None:
        if self._main_window is None:
            raise RuntimeError("Cannot top uninitialized window")

        self._main_window.update_idletasks()
        # put the root window behind the bar
        self._main_window.lift(self._root.winfo_toplevel())
        self._main_window.after(100, self._to_top)

    def _handle_destroy(self) -> None:
        self.stop()
        if self._main_window:
            self._main_window.destroy()
        self._root.winfo_toplevel().destroy()

    @property
    def is_active(self) -> bool:
        """return the information if bar is active or not"""
        return self._loading_bar is not None and self._loading_bar.is_active

    def start(self, interval_ms: Optional[int] = None) -> None:
        """start the bar"""
        self._init()
        if self._loading_bar is None:
            raise RuntimeError("Cannot start uninitialized bar")

        if interval_ms is None:
            self._loading_bar.start()
        else:
            self._loading_bar.start(interval_ms)
        self._locate()
        self._to_top()

    def stop(self) -> None:
        """stop the bar"""
        if self._loading_bar:
            self._loading_bar.stop()

        if self._main_window:
            self._main_window.destroy()

    def update_progress(self, update_by: float = 1.0) -> float:
        """Same as CircularLoadingBarBase.update_progress"""
        if self._loading_bar is None:
            raise RuntimeError("Cannot update uninitialized bar")
        return self._loading_bar.update_progress(update_by)


def test_spinner_loading_bar(root: Union[tk.Tk, tk.Widget]) -> SpinnerLoadingBar:
    """Render a rainbow colored circle spinner bar"""
    loading = SpinnerLoadingBar(root, colors=Colors.RAINBOW)
    loading.grid(row=0, column=0)
    loading.start()

    return loading


def test_spinner_sized_loading_bar(root: Union[tk.Tk, tk.Widget]) -> SpinnerSizedLoadingBar:
    """Render a spinner bar that the circles resize"""

    loading = SpinnerSizedLoadingBar(root)
    loading.grid(row=0, column=1)
    loading.start()

    return loading


def test_circular_loading_bar(root: Union[tk.Tk, tk.Widget]) -> CircleLoadingBar:
    """Render a circular loading bar"""
    circle_loading_bar = CircleLoadingBar(root, symmetric=True)
    circle_loading_bar.grid(row=0, column=2)
    circle_loading_bar.start(interval_ms=8)

    return circle_loading_bar


def test_spinner_loading_bar_with_progress(root: Union[tk.Tk, tk.Widget]) -> SpinnerLoadingBar:
    """Render a rainbow colored circle spinner bar with a progress"""
    loading = SpinnerLoadingBar(root, colors=Colors.GRAYED, size=250, progress_options=ProgressOptions(stop_bar_when_max=True))
    loading.grid(row=1, column=0)

    def _update_progress() -> None:
        loading.update_progress()
        if loading.is_active:
            loading.after(100, _update_progress)

    loading.after(3000, _update_progress)
    loading.start()

    return loading


def test_spinner_sized_loading_bar_with_progress(root: Union[tk.Tk, tk.Widget]) -> SpinnerSizedLoadingBar:
    """Render a rainbow colored circle spinner bar with a progress"""
    loading = SpinnerSizedLoadingBar(root, size=250, progress_options=ProgressOptions(stop_bar_when_max=True), colors=Colors.RAINBOW)
    loading.grid(row=1, column=1)

    def _update_progress() -> None:
        loading.update_progress()
        loading.after(100, _update_progress)

    loading.after(3000, _update_progress)
    loading.start()

    return loading


def test_circular_loading_bar_with_progress(root: Union[tk.Tk, tk.Widget]) -> CircleLoadingBar:
    """Render a rainbow colored circle spinner bar with a progress"""
    loading = CircleLoadingBar(
        root, symmetric=True, size=250, progress_options=ProgressOptions(stop_bar_when_max=True), color1="yellow", color2="purple"
    )
    loading.grid(row=1, column=2)

    def _update_progress() -> None:
        loading.update_progress()
        loading.after(100, _update_progress)

    loading.after(3000, _update_progress)
    loading.start(interval_ms=8)

    return loading


def test_a_working_app() -> None:
    """create an application"""
    root = tk.Tk()

    button_frame = tk.Frame(root)
    button_frame.grid()

    text = tk.Text(root)
    text.insert("1.0", string.ascii_letters * 50)
    text.grid()
    spinner = TransparentSpinnerBar(text, SpinnerSizedLoadingBar, size=250)

    def _update_progress() -> None:
        nonlocal spinner

        spinner.update_progress()
        root.after(100, _update_progress)

    def change_bar(kind: Type[CircularLoadingBarBase], with_progress: bool = False) -> None:
        nonlocal spinner
        spinner.kind = kind
        if with_progress:
            spinner.kwargs["progress_options"] = ProgressOptions(
                stop_bar_when_max=True, destroy_when_max=True, destroy_callback=spinner.stop
            )
        else:
            try:
                del spinner.kwargs["progress_options"]
            except KeyError:
                pass

        spinner.stop()
        if kind == CircleLoadingBar:
            spinner.start(interval_ms=8)
        else:
            spinner.start(interval_ms=100)

        if with_progress:
            root.after(100, _update_progress)

    for idx, options in enumerate((SpinnerLoadingBar, SpinnerSizedLoadingBar, CircleLoadingBar)):
        tk.Button(
            button_frame,
            text=options.__name__,
            command=lambda opt=options: change_bar(opt),  # type: ignore[misc]
        ).grid(row=0, column=idx, padx=10, pady=10)

        tk.Button(
            button_frame,
            text=options.__name__ + "WithProgress",
            command=lambda opt=options: change_bar(opt, with_progress=True),  # type: ignore[misc]
        ).grid(row=1, column=idx, padx=10, pady=10)

    tk.Button(button_frame, text="Stop", command=spinner.stop).grid(row=2, column=1, padx=10, pady=10)

    spinner.start()

    def _exit(wait: bool = True) -> None:
        nonlocal spinner, root

        spinner.stop()
        if wait:
            root.after(1000, lambda: _exit(wait=False))
        else:
            root.destroy()
            root.quit()

    root.protocol("WM_DELETE_WINDOW", _exit)
    root.mainloop()


def main() -> None:
    """show cases and examples"""
    root = tk.Tk()

    test_spinner_loading_bar(root)
    test_spinner_sized_loading_bar(root)
    test_circular_loading_bar(root)

    test_spinner_loading_bar_with_progress(root)
    test_spinner_sized_loading_bar_with_progress(root)
    test_circular_loading_bar_with_progress(root)

    root.mainloop()

    test_a_working_app()


if __name__ == "__main__":
    main()
