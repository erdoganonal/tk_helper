# Tkinter Helper

A module to display some customized tkinter modules.

## Getting Started

You may download this project directly from GitHub, or you may use Python's package manager(pip).

### Prerequisites

Please see [requirements.txt](requirements.txt) for prerequisites.

### Installing

Use pip to install this library.

```cmd, bash
pip install tkhelper
```

## Running the tests

Doctests and unit tests can be run.

### Running doctests

Use python doctest.

```cmd, bash
python -m doctest tkhelper\widgets.py tkhelper\progressbars\circular.py
```

### Running unit tests

Unit tests still in development.

## Example Usage

```python
import tkinter as tk
from tkhelper.widgets import ResizableLabel, ResizableButton
from tkhelper.progressbars.circular import TransparentSpinnerBar, SpinnerLoadingBar

root = tk.Tk()

circular_bar = TransparentSpinnerBar(root, kind=SpinnerLoadingBar)
def start_bar():
    circular_bar.start()
    resizable_button.config(
        command=stop_bar,
        text="Click the button to stop the circular loading bar"
    )

def stop_bar():
    circular_bar.stop()
    resizable_button.config(
        command=start_bar,
        text="Click the button to run the circular loading bar"
    )


resizable_label = ResizableLabel(
    root, text="Example resizable label",
    weight=0.9, resize=True
)
resizable_label.grid()

resizable_button = ResizableButton(
    root, text="Click the button to run the circular loading bar",
    weight=0.5, resize=True, command=start_bar
)
resizable_button.grid()

root.geometry("500x500")
root.mainloop()
```

## Version Info

Version 1.0.0.

## Authors

* **Erdogan Onal** - *Owner* - [Erdogan Onal](https://github.com/erdoganonal)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
