import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QAction, QFileDialog, QToolBar, QPushButton, QMessageBox
from PyQt5.QtGui import QPainter, QPen, QColor, QImage
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize
import json
import numpy as np
import re
import asyncio
from BluetoothCommandThread import BluetoothCommandThread
from functools import partial
import random

class MainWindow(QMainWindow):
    bluetooth_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Two Category Application")

        # initialization
        self.resize(1600, 900)  # Set the window size
        # Create the type buttons
        button_type_one = QPushButton('Type A', self)
        button_type_one.setGeometry(200, 200, 200, 200)  # (x, y, width, height)
        button_type_one.clicked.connect(partial(self.on_button_clicked, button_number=1))
        button_type_two = QPushButton('Type B', self)
        button_type_two.setGeometry(500, 200, 200, 200)  # (x, y, width, height)
        button_type_two.clicked.connect(partial(self.on_button_clicked, button_number=2))
        self.createMenu()
        self.createToolbar()

        # state tracker
        self.current_round = 0
        self.isStart = False
        self.isPracticeMode = True
        self.chooseType = -1
        self.experiment_round_total = 0
        self.experiment_commands = []
        self.template_commands_type_one = []
        self.template_commands_type_two = []
        self.experiment_data = []


    '''
    Load motor positions from setup file
    '''
    def importSetupFile(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Import Experiment File", "", "JSON Files (*.json)")
        if file_path:
            # Parse the setup file to extract motor positions
            self.experiment_round_total = 0
            self.experiment_commands.clear()
            with open(file_path, "r") as file:
                lines = file.readlines()
                self.experiment_round_total = len(lines)
                for line in lines:
                    command_strs = re.findall(r'{[^{}]*}', line)
                    commands = []
                    for command_str in command_strs:
                        print(command_str)
                        commands.append(command_str)
                    self.experiment_commands.append(commands)
            print("new experiment file loaded, data num = ", self.experiment_round_total)

    def importTemplateFile(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Import Experiment File", "", "JSON Files (*.json)")
        if file_path:
            # Parse the setup file to extract motor positions
            self.experiment_commands.clear()
            with open(file_path, "r") as file:
                lines = file.readlines()
                for line in lines:
                    command_strs = re.findall(r'{[^{}]*}', line)
                    commands = []
                    for command_str in command_strs:
                        print(command_str)
                        commands.append(command_str)
                    if len(command_strs) == 4: # type one
                        self.template_commands_type_one.append(commands)
                    else:
                        self.template_commands_type_two.append(commands)
            print("new template file loaded, type one num = ", len(self.template_commands_type_one), ", type two num = ", len(self.template_commands_type_two))
    
    '''
    save drawings to a local file
    '''
    def saveDataToFile(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Save Data to File", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, "w") as file:
                for i in range(len(self.experiment_data)):
                    file.write(str(self.experiment_data[i]))
                    file.write("\n")
            print("save data to file", file_path)

    def createMenu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        import_action = QAction("Import Experiment File", self)
        import_action.triggered.connect(self.importSetupFile)
        file_menu.addAction(import_action)

        import_template_action = QAction("Import Template File", self)
        import_template_action.triggered.connect(self.importTemplateFile)
        file_menu.addAction(import_template_action)

        save_action = QAction("Save Data to File", self)
        save_action.triggered.connect(self.saveDataToFile)
        file_menu.addAction(save_action)

    def createToolbar(self):
        toolbar = QToolBar()
        toolbar.setFixedHeight(50)  # Set the desired height for the toolbar
        toolbar.setStyleSheet("QToolButton { min-width: 120px; min-height: 50px}")
        self.addToolBar(toolbar)

        self.start_button = QAction("Start", self)
        self.start_button.triggered.connect(self.startButtonClicked)
        toolbar.addAction(self.start_button)

        self.confirm_button = QAction("Confirm", self)
        self.confirm_button.triggered.connect(self.confirmButtonClicked)
        toolbar.addAction(self.confirm_button)

        self.clear_button = QAction("Clear", self)
        self.clear_button.triggered.connect(self.clearButtonClicked)
        toolbar.addAction(self.clear_button)

        self.toggle_button = QAction("Mode = Practice", self)
        self.toggle_button.triggered.connect(self.toggleButtonClicked)
        toolbar.addAction(self.toggle_button)

        self.message_line = QLabel("message", self)
        toolbar.addWidget(self.message_line)

    def startButtonClicked(self):
        print("Start button clicked")
        if not self.isPracticeMode:
            if not self.isStart:
                if self.current_round < self.experiment_round_total:
                    print("send command for ", self.current_round)
                    self.message_line.setText('trial #'+str(self.current_round))
                    self.isStart = True
                    ### Trigger Bluetooth command
                    print(self.experiment_commands[self.current_round])
                    commands = '\n'.join(self.experiment_commands[self.current_round])
                    self.bluetooth_signal.emit(commands)
                    self.start_button.setText("Play Again")
                else:
                    print("test finished!")
            else:
                print("play again")
                # Only Trigger Bluetooth command
                print(self.experiment_commands[self.current_round])
                commands = '\n'.join(self.experiment_commands[self.current_round])
                self.bluetooth_signal.emit(commands)
        else:
            print("practice mode! cannot trigger!")

    def confirmButtonClicked(self):
        print("Confirm button clicked")
        # save the drawing to results
        if self.isStart:
            print("Data saved")
            self.experiment_data.append(self.chooseType)
            self.chooseType = -1
            self.isStart = False
            self.current_round += 1
            self.start_button.setText("Start")
        else:
            print("not started!")

    def clearButtonClicked(self):
        print("Clear button clicked")
        # clear the choice
        self.chooseType = -1

    def toggleButtonClicked(self):
        if not self.isStart:
        # if a test already starts, it is not allowed to change the mode
            self.isPracticeMode = not self.isPracticeMode
            if self.isPracticeMode:
                self.toggle_button.setText("Mode = Practice")
            else:
                self.toggle_button.setText("Mode = Test")
    
    def on_button_clicked(self, button_number):
        # QMessageBox.information(self, f'Button {button_number}', f'You clicked Button {button_number}!')
        if self.isPracticeMode:
            # randomly choose one vibration from the group to trigger
            if button_number == 1:
                i = random.randint(0, len(self.template_commands_type_one)-1)
                commands = '\n'.join(self.template_commands_type_one[i])
                print(f"trigger button = {button_number}, index = {i}")
                self.bluetooth_signal.emit(commands)
            elif button_number == 2:
                i = random.randint(0, len(self.template_commands_type_two)-1)
                commands = '\n'.join(self.template_commands_type_two[i])
                print(f"trigger button = {button_number}, index = {i}")
                self.bluetooth_signal.emit(commands)
        else:
            # test mode, record user input
            if button_number == 1:
                self.chooseType = 1
                print("choose type 1")
            elif button_number == 2:
                self.chooseType = 2
                print("choose type 2")
            else:
                self.chooseType = -1

# Main function
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    ### Create and start the Bluetooth thread
    loop = asyncio.get_event_loop()
    bluetooth_thread = BluetoothCommandThread(loop)
    window.bluetooth_signal.connect(bluetooth_thread.bluetooth_callback)
    bluetooth_thread.start()

    sys.exit(app.exec_())

# Run the main function
if __name__ == "__main__":
    main()
