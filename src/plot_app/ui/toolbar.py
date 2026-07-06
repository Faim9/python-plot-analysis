from PySide6.QtWidgets import QToolBar, QPushButton, QWidget, QSizePolicy
from PySide6.QtCore import Signal

class ToolBarManager(QToolBar):

    #TOOLBAR_BUTTONS = { 'element_id' : {...}, ...}

    TOOLBAR_BUTTONS = {'view_data_folder' : {"type":"button", "text": "🗂", "tooltip": "Data Folder", "checkable":False,"cssClass":"icon-btn"},
                       'view_plot_options':{"type":"button","text": "⚙", "tooltip": "Plot Options", "checkable":False,"cssClass":"icon-btn"},


                        "spacer" : {"type": "stretch_spacer"},


                        "zoom":{"type":"button", "text": "⬚", "tooltip": "Zoom (select area)", "checkable":True,"cssClass":"icon-btn"},
                        "pan":{"type":"button", "text": "✥", "tooltip": "Pan mode (drag)", "checkable":True,"cssClass":"icon-btn"},
                        "reset_canvas_view" : {"type":"button", "text": "⤢", "tooltip": "Reset canvas view", "checkable":False,"cssClass":"icon-btn"},
                        "clear_canvas" : {"type":"button", "text": "↻", "tooltip": "Clear Canvas", "checkable":False,"cssClass":"icon-btn"}
                    }
    
    button_interacted = Signal(str,bool)


    def __init__(self,parent=None):
        super().__init__(parent)

        self.setMovable(False)
        self.setFixedHeight(30)

        #Build the Toolbar
        self.buttons,self.btn_actions = self._build_toolbar(self.TOOLBAR_BUTTONS)


    def _add_buttons_toolbar(self,buttons:dict):
        """Adds a variable number of buttons to toolbar"""
        actions = {}

        for btn_name,btn in buttons.items():
            
            action = self.addWidget(btn)
            actions[btn_name] = action
            last_separator = self.addSeparator()

        self.removeAction(last_separator)

        return actions

    def _build_toolbar(self, buttons_config) -> tuple[dict,dict]:
        """Creates all buttons, and stores them."""

        _buttons = {}
        _actions = {}

        for element_id, properties in buttons_config.items():
            element_type = properties.get("type")

            match element_type:
                case "stretch_spacer":
                    
                    spacer = QWidget()
                    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                    self.addWidget(spacer)

                case "button":
                
                    btn = self._create_button(
                        element_id,
                        text = properties["text"],
                        tooltip = properties["tooltip"],
                        checkable = properties["checkable"]
                    )
                    
                    _buttons[element_id] = btn

                    action = self.addWidget(btn)
                    self.addSeparator()

                    _actions[element_id] = action

        return _buttons, _actions


    def _create_button(self, button_id:str, text:str,tooltip:str, size=(20,20), checkable:bool=False) -> QPushButton:
        """Creates a Buttons for the toolbar"""

        btn = QPushButton(text)
        btn.setFixedSize(*size)
        btn.setProperty('cssClass',"icon-btn")
        btn.setToolTip(tooltip)

        if checkable:
            btn.setCheckable(True)
            btn.toggled.connect(lambda checked: self.button_interacted.emit(button_id,checked))

        else:
            btn.clicked.connect(lambda: self.button_interacted.emit(button_id,False))

        return btn

    def set_button_checked(self, button_id: str, checked: bool):
        """Safely toggle a button from the outside without exposing the dictionary."""
        if button_id in self.buttons:
            self.buttons[button_id].setChecked(checked)

    def set_button_enabled(self, button_id: str, enabled: bool):
        if button_id in self.btn_actions:
            self.btn_actions[button_id].setEnabled(enabled)
            
    def get_button(self, button_id: str) -> QPushButton:
        """If the Main Window absolutely must touch the button object, use a getter."""
        return self.buttons.get(button_id) #type: ignore