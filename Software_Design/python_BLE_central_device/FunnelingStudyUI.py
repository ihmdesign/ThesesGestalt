import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QAction, QFileDialog, QToolBar
from PyQt5.QtGui import QPainter, QPen, QColor, QImage
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize
import json
import numpy as np
import re
import asyncio
from BluetoothCommandThread import BluetoothCommandThread

class DrawingWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.drawing = False
        self.render_paths = []
        self.render_times = []
        self.count = 0

        self.background_image = QImage("data/Picture2.png")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.background_image)
        pen = QPen()
        pen.setWidth(2)
        pen.setColor(QColor(0, 0, 0))
        painter.setPen(pen)
        
        for i in range(self.count):
            # print(self.render_paths[i][0], self.render_paths[i][-1])
            for j in range(1, len(self.render_paths[i])):
                painter.drawEllipse(self.render_paths[i][j - 1], 5, 5)
                painter.drawLine(self.render_paths[i][j - 1], self.render_paths[i][j])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.count += 1
            self.render_paths.append([])
            self.render_paths[self.count-1].append(event.pos())
            self.render_times.append([])
            self.render_times[self.count-1].append(event.timestamp())

    def mouseMoveEvent(self, event):
        if self.drawing and event.buttons() == Qt.LeftButton:
            self.render_paths[self.count-1].append(event.pos())
            self.render_times[self.count-1].append(event.timestamp())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            self.update()

    def clearDrawing(self):
        self.count = 0
        self.render_paths.clear()
        self.render_times.clear()
        self.update()
    

class MainWindow(QMainWindow):
    bluetooth_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drawing Application")

        # initialization
        self.drawing_widget = DrawingWidget()
        self.setCentralWidget(self.drawing_widget)
        self.resize(1600, 900)  # Set the window size
        self.createMenu()
        self.createToolbar()

        # state tracker
        self.current_round = 0
        self.isStart = False
        self.experiment_round_total = 0
        self.experiment_commands = []
        self.drawing_paths = []
        self.drawing_times = []


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
    
    '''
    save drawings to a local file
    '''
    def saveDataToFile(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Save Data to File", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, "w") as file:
                for i in range(self.experiment_round_total):
                    # print(self.drawing_times[i])
                    # print(self.drawing_paths[i])
                    for x_time, x_path in zip(self.drawing_times[i], self.drawing_paths[i]):
                        x_path_tuples = [(point.x(), point.y()) for point in x_path]
                        data = {"time": x_time, "path": x_path_tuples}
                        json.dump(data, file)
                        file.write(' ')
                    file.write("\n")
            print("save data to file", file_path)

    def createMenu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        import_action = QAction("Import Experiment File", self)
        import_action.triggered.connect(self.importSetupFile)
        file_menu.addAction(import_action)

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

        

        self.message_line = QLabel("message", self)
        toolbar.addWidget(self.message_line)

    def startButtonClicked(self):
        print("Start button clicked")
        if not self.isStart:
            if self.current_round < self.experiment_round_total:
                print("send command for ", self.current_round)
                self.message_line.setText('trial #'+str(self.current_round))
                self.isStart = True
                ### Trigger Bluetooth command
                # print(self.experiment_commands[self.current_round])
                # commands = '\n'.join(self.experiment_commands[self.current_round])
                # self.bluetooth_signal.emit(commands)
                # self.start_button.setText("Play Again")
            else:
                print("test finished!")
        else:
            print("play again")
            # Only Trigger Bluetooth command

    def confirmButtonClicked(self):
        print("Confirm button clicked")
        # save the drawing to results
        if self.isStart:
            print("Data saved")
            self.drawing_paths.append(self.drawing_widget.render_paths.copy())
            self.drawing_times.append(self.drawing_widget.render_times.copy())
            # print(self.drawing_paths)
            self.drawing_widget.clearDrawing()
            # print(self.drawing_paths)
            self.isStart = False
            self.current_round += 1
            self.start_button.setText("Start")

    def clearButtonClicked(self):
        print("Clear button clicked")
        # call the function to clean current drawings
        self.drawing_widget.clearDrawing()

# Main function
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    ### Create and start the Bluetooth thread
    # loop = asyncio.get_event_loop()
    # bluetooth_thread = BluetoothCommandThread(loop)
    # window.bluetooth_signal.connect(bluetooth_thread.bluetooth_callback)
    # bluetooth_thread.start()

    sys.exit(app.exec_())

# Run the main function
if __name__ == "__main__":
    main()
