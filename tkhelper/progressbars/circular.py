"""Renders a widget using tk.Canvas module to
busy the screen for a while
"""
import abc
import math
import enum
from typing import Any, Union, Iterable, Tuple, Optional, Generator, Type
from collections import deque
import string

import tkinter as tk
from colour import Color

from ..package_info import __version__, __author__, __mail__


FULL_CIRCLE_DEGREE = 360


# pylint: disable=too-many-ancestors


def _change_text(root, label: tk.Label, *p_bars, remaining_time: int = 2):
    """helper function for docstrings"""
    for p_bar in p_bars:
        if not p_bar.is_active:
            p_bar.start()
    label.config(
        text="Bar will be stopped in {0} seconds".format(remaining_time)
    )
    if remaining_time <= 0:
        for p_bar in p_bars:
            p_bar.stop()
        label.config(
            text="The window will be destroyed in a second"
        )
        root.after(1000, root.destroy)
    else:
        root.after(1000, lambda: _change_text(
            root, label, *p_bars, remaining_time=remaining_time - 1
        ))


class InconsistentLengths(Exception):
    """Raise when MaskItem lengths are not match"""

    def __init__(self, expected_length: int, actual_length: int):
        super().__init__(
            "Expected length of {0}, got {1}"
            "".format(expected_length, actual_length)
        )


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
        values = [repr(item) for item in cls.__dict__['_member_map_'].values()]

        other_value = ''
        if len(values) > 1:
            values, other_value = values[:-1], values[-1]
            other_value = ' or {0}'.format(other_value)
        raise ValueError(
            "bad value \"{0!r}\": expected {1}{2}"
            "".format(value, ', '.join(values), other_value)
        )


class ResizeActions(_EnumBase):
    """Actions for resize"""

    ADD = 'add'
    SET = 'set'
    SUB = 'subtract'


class AngleType(_EnumBase):
    """Angle types"""

    DEGREE = 'degree'
    RADIAN = 'radian'


class Converter:
    """Math calculations between circles"""

    @staticmethod
    def centered_circle_to_circle(center_x, center_y, radius):
        """Converts centered_circle to circle"""
        return center_x - radius, center_y - radius, radius

    @classmethod
    def centered_circle_to_oval(cls, center_x, center_y, radius):
        """Converts centered circle to oval"""
        return cls.circle_to_oval(
            *cls.centered_circle_to_circle(center_x, center_y, radius)
        )

    @staticmethod
    def circle_to_oval(start_x, start_y, radius):
        """Converts circle to oval"""
        diameter = 2 * radius
        end_x = start_x + diameter
        end_y = start_y + diameter
        return start_x, start_y, end_x, end_y

    @staticmethod
    def oval_to_circle(start_x, start_y, end_x, end_y):
        """Converts oval to circle"""
        assert end_x == end_y, "Oval must be circle"
        return start_x, start_y, (end_x - start_x) / 2

    @staticmethod
    def circle_to_centered_circle(start_x, start_y, radius):
        """Converts circle to centered circle"""
        return start_x + radius, start_y + radius, radius

    @classmethod
    def oval_to_centered_circle(cls, start_x, start_y, end_x, end_y):
        """Converts oval to centered circle"""
        return cls.circle_to_centered_circle(
            *cls.oval_to_circle(start_x, start_y, end_x, end_y)
        )


_MaskItemTest = type("_MaskItemTest", (), {})
_MaskItemTest.test_method = staticmethod(
    lambda test_param: print(test_param.copy())
)


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

    def __init__(self, method_name: str, **kwargs: Iterable):
        self._method_name = method_name
        self._kwargs = {}

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
        for key in self._kwargs:
            self._kwargs[key].rotate(rotate_by)

    def __len__(self) -> int:
        for value in self._kwargs.values():
            return len(value)
        return 0

    def __iter__(self) -> Tuple[str, Any]:
        for key, value in self._kwargs.items():
            yield key, value

    def __str__(self) -> str:
        string_result = "Method name: {0}\n".format(self.name)
        for param, value in self._kwargs.items():
            string_result += "\t{0}: {1}\n".format(param, value)
        return string_result


class Mask(list):
    """
    A list that includes masks.
        Args:
            *args: List of MaskItems
    """

    def __init__(self, *args: MaskItem, rotate_by: int = 1):
        super().__init__(args)
        self.rotate_by = rotate_by

    def apply(self, obj: Any) -> None:
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

    def __len__(self) -> None:
        length = None
        for mask_item in self:
            if length is None:
                length = len(mask_item)
            elif length != len(mask_item):
                raise InconsistentLengths(length, len(mask_item))
        return length or 0

    def __str__(self) -> str:
        return "\n".join(str(i) for i in self)


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
            self, *args, mask: Mask,
            size: Optional[int] = None,
            shift: int = 0, **kwargs):
        if size is not None:
            kwargs['width'] = kwargs['height'] = size
        super().__init__(*args, **kwargs)

        self.shift = shift
        self._is_active = None
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
            raise ValueError(
                "mask should be instance of"
                "{0!r}".format(Mask)
            )

    @property
    @abc.abstractmethod
    def items(self):
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
        precision = 10 ** precision
        return int(num * precision) / precision

    @classmethod
    def polar_to_cartesian(
            cls, radius: float, angle: float,
            kind: AngleType = AngleType.DEGREE) -> Tuple[float, float]:
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
    def size(self) -> int:
        """return the size to fit the widget"""
        return min(self.winfo_width(), self.winfo_height())

    @abc.abstractmethod
    def update_bar(self) -> None:
        """updates the loading bar attributes"""

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

        self._is_active = True
        self._start(interval_ms=interval_ms)

    def stop(self) -> None:
        """stop the bar"""
        self._is_active = False

    def create_centered_circle(
            self, center_x: float, center_y: float,
            radius: float, **kwargs) -> int:
        """Create a circle with given radius and coordinates
            that pointing the center of the circle

            Args:
                center_x: x coordinate of the circle in cartesian system
                center_y: y coordinate of the circle in cartesian system
                radius:   Radius of the circle
            Returns:
                id of the created circle
        """
        return self.create_oval(
            Converter.centered_circle_to_oval(
                center_x, center_y, radius
            ), **kwargs
        )

    def create_circle(self, start_x: float, start_y: float, radius: float, **kwargs) -> int:
        """Create a circle with given radius and place to given coordinates
            Args:
                start_x: x origin point of the square which includes the circle
                start_y: y origin point of the square which includes the circle
                radius:  Radius of the circle
            Returns:
                id of the created circle
        """
        return self.create_oval(
            Converter.circle_to_oval(
                start_x, start_y, radius
            ), **kwargs
        )

    def resize(
            self, item_id: int, radius: float,
            action: ResizeActions = ResizeActions.SET) -> None:
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

    def __del__(self):
        try:
            self.stop()
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

    def __init__(self, *args, offset: Optional[Iterable] = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.circles = []
        self.offset = offset

    @property
    def items(self):
        return self.circles

    def update_bar(self) -> None:
        width = self.size / 2
        radius = width / 8
        offset = self.offset or 20

        for item_id in self.circles:
            self.delete(item_id)
        self.circles = []

        for angle in self.get_sequence(0, FULL_CIRCLE_DEGREE, len(self.mask)):
            coordinate_x, coordinate_y = self.polar_to_cartesian(
                width - radius - offset, angle)
            self.circles.append(self.create_centered_circle(
                coordinate_x + self.shift + radius + offset, coordinate_y +
                self.shift + radius + offset, radius
            ))


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
        >>> bar1 = SpinnerLoadingBar(root, size=200, colors=SpinnerLoadingBar.GRAYED)
        >>> bar1.grid()
        >>> bar2 = SpinnerLoadingBar(root, size=200)
        >>> bar2.grid()
        >>> _change_text(root, label, bar1, bar2)

        >>> root.mainloop()
    """

    GRAYED = (
        "#fafafa", "#f5f5f5", "#e0e0e0", "#bdbdbd",
        "#9e9e9e", "#757575", "#616161", "#424242"
    )
    RAINBOW = (
        "#fff100", "#ff8c00", "#e81123", "#4b0082",
        "#000080", "#00188f", "#00b294", "#bad80a"
    )

    def __init__(self, *args, colors=None, **kwargs):
        if colors is None:
            colors = self.RAINBOW

        kwargs['mask'] = kwargs.get('mask', Mask(
            MaskItem('itemconfig', fill=colors)
        ))

        super().__init__(*args, **kwargs)


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

    def __init__(self, *args, **kwargs):
        min_radius = 5
        circles = 8
        resize_mask = range(min_radius, min_radius + circles)
        default_mask = Mask(
            MaskItem('resize', radius=resize_mask),
            MaskItem('itemconfig', fill=['black'] * len(resize_mask))
        )

        kwargs['mask'] = kwargs.get('mask', default_mask)
        super().__init__(*args, **kwargs)


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
            self, *args, width: int = 10,
            color1: Optional[str] = None, color2: Optional[str] = None,
            steps: int = 180, color_range: Optional[Iterable] = None,
            symmetric=True, **kwargs):
        if color_range and (color1 or color2):
            raise ValueError(
                "You are not allowed to pass color_range "
                "and colors at the same time"
            )

        if color1 is None:
            color1 = self.DTF_COLOR1

        if color2 is None:
            color2 = self.DTF_COLOR2

        self.arcs = []
        if color_range is None:
            if symmetric:
                colors = list(self.get_range(color1, color2, int(steps / 2)))
                color_range = colors + colors[-2::-1]
            else:
                color_range = self.get_range(color1, color2, steps)
        kwargs['mask'] = Mask(
            MaskItem('itemconfig', outline=color_range,),
            rotate_by=-1
        )

        self.width = width
        self.oval1_id = None
        self.oval2_id = None

        super().__init__(*args, **kwargs)

    @property
    def items(self):
        return self.arcs

    def update_bar(self):
        outer_circle_offset = self.width
        inner_circle_offset = self.width * 2
        if self.oval1_id:
            self.delete(self.oval1_id)
        if self.oval2_id:
            self.delete(self.oval2_id)

        self.oval1_id = self.create_oval(
            outer_circle_offset - self.width / 2,
            outer_circle_offset - self.width / 2,
            self.size - outer_circle_offset + self.width / 2,
            self.size - outer_circle_offset + self.width / 2
        )

        self.oval2_id = self.create_oval(
            inner_circle_offset - self.width / 2, inner_circle_offset - self.width / 2,
            self.size - inner_circle_offset + self.width /
            2, self.size - inner_circle_offset + self.width / 2,
        )

        self._create_loading_arc(
            outer_circle_offset, outer_circle_offset,
            self.size - outer_circle_offset, self.size - outer_circle_offset,
            width=self.width
        )

    @staticmethod
    def get_range(color1: str, color2: str, steps: int) -> Generator:
        """range of color"""
        for color in Color(color1).range_to(color2, steps):
            yield color.get_hex()

    def _create_loading_arc(self, *bbox, width: float, **kwargs) -> None:
        color_range = len(self._mask)

        start = 0
        extent = FULL_CIRCLE_DEGREE / color_range

        for arc_id in self.arcs:
            self.delete(arc_id)

        self.arcs = []
        for _ in range(len(self.mask)):
            self.arcs.append(
                self.create_arc(
                    *bbox,
                    start=start, width=width,
                    extent=extent, style='arc',
                    **kwargs
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

    _TRANSPARENT_COLOR = 'white'

    class Location(_EnumBase):
        """An enum for positioning the transparent loading bar"""

        LEFT_TOP = 'lt'
        LEFT_CENTER = 'lc'
        LEFT_BOTTOM = 'lb'

        MIDDLE_TOP = 'mt'
        MIDDLE_CENTER = 'mc'
        MIDDLE_BOTTOM = 'mb'

        RIGHT_TOP = 'rt'
        RIGHT_CENTER = 'rc'
        RIGHT_BOTTOM = 'rb'

        @classmethod
        def is_top(cls, value: Any):
            """Returns True if given value places at the top, False otherwise"""
            return value in (cls.LEFT_TOP, cls.MIDDLE_TOP, cls.RIGHT_TOP)

        @classmethod
        def is_middle(cls, value: Any):
            """Returns True if given value places at the middle, False otherwise"""
            return value in (cls.MIDDLE_TOP, cls.MIDDLE_CENTER, cls.MIDDLE_BOTTOM)

        @classmethod
        def is_bottom(cls, value: Any):
            """Returns True if given value places at the bottom, False otherwise"""
            return value in (cls.LEFT_BOTTOM, cls.MIDDLE_BOTTOM, cls.RIGHT_BOTTOM)

        @classmethod
        def is_left(cls, value: Any):
            """Returns True if given value places at the left, False otherwise"""
            return value in (cls.LEFT_TOP, cls.LEFT_CENTER, cls.LEFT_BOTTOM)

        @classmethod
        def is_center(cls, value: Any):
            """Returns True if given value places at the center, False otherwise"""
            return value in (cls.LEFT_CENTER, cls.MIDDLE_CENTER, cls.RIGHT_CENTER)

        @classmethod
        def is_right(cls, value: Any):
            """Returns True if given value places at the right, False otherwise"""
            return value in (cls.RIGHT_TOP, cls.RIGHT_CENTER, cls.RIGHT_BOTTOM)

    def __init__(
            self, root: Union[tk.Widget, tk.Tk], kind: Type[CircularLoadingBarBase],
            location: Optional[Union[Location, Tuple[int, int]]] = Location.MIDDLE_CENTER,
            **kwargs):
        self._root = root
        self.location = location
        self._main_window = self._loading_bar = None
        self.kind = kind

        # Override background color
        kwargs['background'] = kwargs['bg'] = \
            kwargs['highlightbackground'] = self._TRANSPARENT_COLOR
        self.kwargs = kwargs

        self._root.winfo_toplevel().protocol(
            "WM_DELETE_WINDOW",
            self._handle_destroy
        )

    def _init(self) -> None:
        if self.is_active:
            raise RuntimeError("The bar is already running")

        self._main_window = tk.Toplevel(self._root.winfo_toplevel())
        self._loading_bar = self.kind(
            self._main_window, **self.kwargs
        )
        self._loading_bar.grid()

        # TODO: Check for platform dependency
        self._main_window.overrideredirect(True)  # Remove the title and border
        self._main_window.wm_attributes(
            "-transparentcolor",
            self._TRANSPARENT_COLOR
        )

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
            return self.location

        left_x = self._root.winfo_rootx()
        middle_x = int(self._root.winfo_rootx() +
                       self._root.winfo_width() / 2 - self._loading_bar.size / 2)
        right_x = int(self._root.winfo_rootx() +
                      self._root.winfo_width() - self._loading_bar.size)

        top_y = self._root.winfo_rooty()
        center_y = int(self._root.winfo_rooty() +
                       self._root.winfo_height() / 2 - self._loading_bar.size / 2)
        bottom_y = int(self._root.winfo_rooty() +
                       self._root.winfo_height() - self._loading_bar.size)

        x_coord = y_coord = None

        if self.Location.is_left(self.location):
            x_coord = left_x
        if self.Location.is_middle(self.location):
            x_coord = middle_x
        if self.Location.is_right(self.location):
            x_coord = right_x

        if self.Location.is_top(self.location):
            y_coord = top_y
        if self.Location.is_center(self.location):
            y_coord = center_y
        if self.Location.is_bottom(self.location):
            y_coord = bottom_y

        return x_coord, y_coord

    def _locate(self) -> None:
        try:
            coord_x, coord_y = self._get_coordinates()
        except tk.TclError:
            return

        self._main_window.geometry('+{}+{}'.format(
            coord_x, coord_y
        ))
        if self.is_active:
            self._main_window.after(1, self._locate)

    def _to_top(self):
        self._main_window.update_idletasks()
        # put the root window behind the bar
        self._main_window.lift(self._root.winfo_toplevel())
        self._main_window.after(100, self._to_top)

    def _handle_destroy(self):
        self.stop()
        self._main_window.destroy()
        self._root.winfo_toplevel().destroy()

    @property
    def is_active(self):
        """return the information if bar is active or not"""
        return self._loading_bar and self._loading_bar.is_active

    def start(self, interval_ms: Optional[int] = None):
        """start the bar"""
        self._init()
        if interval_ms is None:
            self._loading_bar.start()
        else:
            self._loading_bar.start(interval_ms)
        self._locate()
        self._to_top()

    def stop(self):
        """stop the bar"""
        self._loading_bar.stop()
        self._main_window.destroy()


def test_spinner_loading_bar(root: Union[tk.Tk, tk.Widget]) -> None:
    """Render a rainbow colored circle spinner bar"""
    loading = SpinnerLoadingBar(
        root, colors=SpinnerLoadingBar.RAINBOW,
    )
    loading.grid(row=0, column=0)
    loading.start()


def test_spinner_sized_loading_bar(root: Union[tk.Tk, tk.Widget]) -> None:
    """Render a spinner bar that the circles resize"""

    loading = SpinnerSizedLoadingBar(root)
    loading.grid(row=0, column=1)
    loading.start()


def test_circular_loading_bar(root: Union[tk.Tk, tk.Widget]) -> None:
    """Render a circular loading bar"""
    circle_loading_bar = CircleLoadingBar(root, symmetric=True)
    circle_loading_bar.grid(row=0, column=2)
    circle_loading_bar.start(interval_ms=8)


def test_a_working_app() -> None:
    """create an application"""
    root = tk.Tk()

    button_frame = tk.Frame(root)
    button_frame.grid()

    def change_bar(kind):
        nonlocal spinner
        spinner.kind = kind

        spinner.stop()
        if kind == CircleLoadingBar:
            spinner.start(interval_ms=8)
        else:
            spinner.start(interval_ms=100)

    tk.Button(
        button_frame, text='SpinnerLoadingBar',
        command=lambda: change_bar(SpinnerLoadingBar)
    ).grid(row=0, column=0, padx=10, pady=10)
    tk.Button(
        button_frame, text='SpinnerSizedLoadingBar',
        command=lambda: change_bar(SpinnerSizedLoadingBar)
    ).grid(row=0, column=1, padx=10, pady=10)
    tk.Button(
        button_frame, text='CircleLoadingBar',
        command=lambda: change_bar(CircleLoadingBar)
    ).grid(row=0, column=2, padx=10, pady=10)

    # pylint:disable=unnecessary-lambda
    tk.Button(
        button_frame, text='Stop',
        command=lambda: spinner.stop()
    ).grid(row=0, column=3, padx=10, pady=10)

    text = tk.Text(root)
    text.insert("1.0", string.ascii_letters * 50)
    text.grid()

    spinner = TransparentSpinnerBar(
        text, SpinnerSizedLoadingBar
    )
    spinner.start()

    root.mainloop()


def main() -> None:
    """show cases and examples"""
    root = tk.Tk()

    test_spinner_loading_bar(root)

    test_spinner_sized_loading_bar(root)

    test_circular_loading_bar(root)

    test_a_working_app()

    root.mainloop()


if __name__ == '__main__':
    main()
