from PyQt6 import QtWidgets

def add_items_list(widget: QtWidgets.QListWidget, items: list[object]) -> None:
    widget.clear()
    for i in items:
        item_to_add = QtWidgets.QListWidgetItem()
        item_to_add.setText(str(i))
        item_to_add.setData(1, i)
        widget.addItem(item_to_add)

def add_items_list_dict(widget: QtWidgets.QListWidget, items: dict[object]) -> None:
    widget.clear()
    for i in items:
        item_to_add = QtWidgets.QListWidgetItem()
        item_to_add.setText(i)
        item_to_add.setData(1, items[i])
        widget.addItem(item_to_add)

def add_items_combo(widget: QtWidgets.QComboBox, items: list[object]) -> None:
    widget.clear()
    for i in items:
        widget.addItem(str(i), userData=i)

def add_items_combo_dict(widget: QtWidgets.QComboBox, items: dict[object]) -> None:
    widget.clear()
    for i in items:
        widget.addItem(i, items[i])
