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
        self.show_data = False
        self.show_single_motor = False
        self.category_num = 10
        self.data_category = None
        self.data = None
        
        
        self.background_image = QImage("data/Picture2.png")

        self.motor_positions = [QPoint(1240-i*200, 420) for i in range(9)]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.background_image)
        pen = QPen()
        pen.setWidth(2)
        pen.setColor(QColor(0, 0, 0))
        painter.setPen(pen)
        color_palette = self.generate_color_palette(self.category_num)

        # draw motor positions
        for motor_position in self.motor_positions:
            painter.drawEllipse(motor_position, 20, 20)

        # draw user study data
        if self.show_data:
            print("draw paths", len(self.data))
            for i in range(self.category_num):
                pen.setColor(color_palette[i])
                painter.setPen(pen)
                painter.drawEllipse(QPoint(40*i+40, 40), 20, 20)
            for i in range(len(self.data)):
                if (self.data_category[i]  < 7 and self.show_single_motor) or (self.data_category[i] >=7 and not self.show_single_motor):
                    pen.setColor(color_palette[self.data_category[i]])
                    painter.setPen(pen)
                    paths = self.data[i]
                    for path in paths:
                        for j in range(1, len(path['path'])):
                            painter.drawLine(QPoint(path['path'][j - 1][0], path['path'][j - 1][1]), QPoint(path['path'][j][0], path['path'][j][1]))

        # draw user input
        pen.setColor(QColor(0, 0, 0))
        painter.setPen(pen)
        for i in range(self.count):
            print(self.render_paths[i][0], self.render_paths[i][-1])
            for j in range(1, len(self.render_paths[i])):
                painter.drawEllipse(self.render_paths[i][j - 1], 5, 5)
                painter.drawLine(self.render_paths[i][j - 1], self.render_paths[i][j])
                # print(self.render_paths[i])

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

    def show_data_paths(self, round_total, experiment, data, category_num, category):
        self.data = data
        self.show_single_motor = not self.show_single_motor
        self.category_num = category_num
        self.data_category = []
        for i in range(round_total):
            # get the category of this data
            self.data_category.append(category.index(experiment[i]))
        # print(self.data_category)
        self.show_data = True
        self.update()

    def generate_color_palette(self, num_colors):
        palette = []
        hsv_step = 360 / num_colors
        hsv_value = 255

        for i in range(num_colors):
            color = QColor.fromHsv(i * hsv_step, 255, hsv_value)
            palette.append(color)

        return palette

    

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
        self.data_round_total = 0
        self.experiment_data = []
        self.category_num = 0
        self.experiment_category = []

    def createMenu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        import_action = QAction("Import Experiment File", self)
        import_action.triggered.connect(self.importSetupFile)
        file_menu.addAction(import_action)

        save_action = QAction("Import Data File", self)
        save_action.triggered.connect(self.importDataFile)
        file_menu.addAction(save_action)

        category_action = QAction("Import Category File", self)
        category_action.triggered.connect(self.importCategoryFile)
        file_menu.addAction(category_action)

    '''
    Load motor positions from setup file
    {"time": 0, "addr": 0, "mode": 1, "duty": 15, "freq": 3, "wave": 1}
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
                    self.experiment_commands.append(line.strip())
            print("new experiment file loaded, round num = ", self.experiment_round_total)
    
    '''
    import data file
    {'time':[t1, t2, t3], 'path':[[x1,y1], [x2,y2], [x3,y3]]}
    '''
    def importDataFile(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Import Data File", "", "JSON Files (*.json)")
        if file_path:
            # Parse the setup file to extract data
            self.data_round_total = 0
            self.experiment_data.clear()
            with open(file_path, "r") as file:
                lines = file.readlines()
                self.data_round_total = len(lines)
                for line in lines:
                    command_strs = re.findall(r'{[^{}]*}', line)
                    commands = []
                    for command_str in command_strs:
                        commands.append(json.loads(command_str))
                    self.experiment_data.append(commands)
            print("new data file loaded, data num = ", self.data_round_total)
    
    '''
    import category file
    same as experiment file
    '''
    def importCategoryFile(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Import Category File", "", "JSON Files (*.json)")
        if file_path:
            # Parse the setup file to extract motor positions
            self.category_num = 0
            self.experiment_category.clear()
            with open(file_path, "r") as file:
                lines = file.readlines()
                self.category_num = len(lines)
                for line in lines:
                    self.experiment_category.append(line.strip())
            print("new category file loaded, category num = ", self.category_num)

    def createToolbar(self):
        toolbar = QToolBar()
        toolbar.setFixedHeight(50)  # Set the desired height for the toolbar
        toolbar.setStyleSheet("QToolButton { min-width: 120px; min-height: 50px}")
        self.addToolBar(toolbar)

        self.start_button = QAction("Start", self)
        self.start_button.triggered.connect(self.startButtonClicked)
        toolbar.addAction(self.start_button)

    def startButtonClicked(self):
        print("Start button clicked")
        # show the drawing paths
        self.drawing_widget.show_data_paths(self.experiment_round_total, self.experiment_commands, self.experiment_data, self.category_num, self.experiment_category)
        

# Main function
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

# Run the main function
if __name__ == "__main__":
    main()
