from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QComboBox, QSpinBox, QDoubleSpinBox
from superqt import QRangeSlider

def add_items_list(widget: QListWidget, items: list[object]) -> None:
    widget.clear()
    for i in items:
        item_to_add = QListWidgetItem()
        item_to_add.setText(str(i))
        item_to_add.setData(1, i)
        widget.addItem(item_to_add)

def add_items_list_dict(widget: QListWidget, items: dict[object]) -> None:
    widget.clear()
    for i in items:
        item_to_add = QListWidgetItem()
        item_to_add.setText(i)
        item_to_add.setData(1, items[i])
        widget.addItem(item_to_add)

def add_items_combo(widget: QComboBox, items: list[object]) -> None:
    widget.clear()
    for i in items:
        widget.addItem(str(i), userData=i)

def add_items_combo_dict(widget: QComboBox, items: dict[object]) -> None:
    widget.clear()
    for i in items:
        widget.addItem(i, items[i])

def setup_QRangeSlider(slider: QRangeSlider, minVal: int, maxVal: int, values: tuple[int, int] = None, interval: int = 1,
                       output: tuple[QSpinBox | QDoubleSpinBox, QSpinBox | QDoubleSpinBox] = None,
                       outscale: float = 0.0) -> None:
    slider.setMinimum(minVal)
    slider.setMaximum(maxVal)
    slider.setSingleStep(interval)
    if values != None:
        slider.setValue(values)
    else:
        slider.setValue((minVal, maxVal))
    if output != None:
        if outscale == 0.0:
            slider.sliderReleased.connect(lambda: output[0].setValue(slider.value()[0]))
            slider.sliderReleased.connect(lambda: output[1].setValue(slider.value()[1]))
            output[0].valueChanged.connect(lambda: slider.setValue((output[0].value(), slider.value()[1])))
            output[1].valueChanged.connect(lambda: slider.setValue((slider.value()[0], output[1].value())))
        else:
            slider.sliderReleased.connect(lambda: output[0].setValue(slider.value()[0]*outscale))
            slider.sliderReleased.connect(lambda: output[1].setValue(slider.value()[1]*outscale))
            output[0].valueChanged.connect(lambda: slider.setValue((output[0].value()/outscale, slider.value()[1])))
            output[1].valueChanged.connect(lambda: slider.setValue((slider.value()[0], output[1].value()/outscale)))
