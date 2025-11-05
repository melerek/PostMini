"""
Request Destination Dialog

Dialog for selecting request name and target collection when importing.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QPushButton, QLabel, QFormLayout
)
from PyQt6.QtCore import Qt


class RequestDestinationDialog(QDialog):
    """
    Dialog for choosing request name and target collection.
    """
    
    def __init__(self, parent=None, db_manager=None, default_name="", current_collection_id=None):
        super().__init__(parent)
        self.db = db_manager
        self.default_name = default_name
        self.current_collection_id = current_collection_id
        self.selected_collection_id = None
        self.request_name = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Import Request")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "<b>Choose a name and destination for the imported request:</b>"
        )
        layout.addWidget(instructions)
        layout.addSpacing(12)
        
        # Form layout for inputs
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)
        
        # Request name input
        self.name_input = QLineEdit()
        self.name_input.setText(self.default_name)
        self.name_input.setPlaceholderText("Enter request name...")
        self.name_input.selectAll()
        form_layout.addRow("<b>Request Name:</b>", self.name_input)
        
        # Collection selector
        self.collection_combo = QComboBox()
        self.collection_combo.setMinimumHeight(28)
        self._load_collections()
        form_layout.addRow("<b>Target Collection:</b>", self.collection_combo)
        
        layout.addLayout(form_layout)
        layout.addSpacing(12)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        import_btn = QPushButton("📥 Import")
        import_btn.setDefault(True)
        import_btn.clicked.connect(self._accept)
        button_layout.addWidget(import_btn)
        
        button_layout.addSpacing(8)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Focus on name input
        self.name_input.setFocus()
    
    def _load_collections(self):
        """Load collections into the combo box."""
        if not self.db:
            return
        
        collections = self.db.get_all_collections()
        
        if not collections:
            self.collection_combo.addItem("No collections available", None)
            self.collection_combo.setEnabled(False)
            return
        
        # Add collections to combo box
        for collection in collections:
            self.collection_combo.addItem(collection['name'], collection['id'])
        
        # Select the current collection if available
        if self.current_collection_id:
            for i in range(self.collection_combo.count()):
                if self.collection_combo.itemData(i) == self.current_collection_id:
                    self.collection_combo.setCurrentIndex(i)
                    break
    
    def _accept(self):
        """Validate and accept the dialog."""
        # Validate name
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            self.name_input.setStyleSheet("border: 1px solid red;")
            return
        
        # Validate collection
        collection_id = self.collection_combo.currentData()
        if collection_id is None:
            return
        
        self.request_name = name
        self.selected_collection_id = collection_id
        self.accept()
    
    def get_request_name(self):
        """Get the entered request name."""
        return self.request_name
    
    def get_collection_id(self):
        """Get the selected collection ID."""
        return self.selected_collection_id

