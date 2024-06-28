import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QAction, QFileDialog, QDialog, QLineEdit, QDialogButtonBox
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QPoint
import json
import numpy as np

class LineInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Line Input")
        layout = QVBoxLayout(self)

        self.start_time_edit = QLineEdit()
        self.stop_time_edit = QLineEdit()

        layout.addWidget(QLabel("Start Time:"))
        layout.addWidget(self.start_time_edit)

        layout.addWidget(QLabel("Stop Time:"))
        layout.addWidget(self.stop_time_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_times(self):
        start_time = self.start_time_edit.text()
        stop_time = self.stop_time_edit.text()
        return start_time, stop_time

class DrawingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.drawing = False
        self.render_paths = []
        self.render_times = []
        self.count = 0
        self.motor_positions = []

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen()
        pen.setWidth(2)
        pen.setColor(QColor(0, 0, 0))
        painter.setPen(pen)
        
        print(self.count)
        for i in range(self.count):
            print(self.render_paths[i][0], self.render_paths[i][-1])
            for j in range(1, len(self.render_paths[i])):
                painter.drawEllipse(self.render_paths[i][j - 1], 5, 5)
                painter.drawLine(self.render_paths[i][j - 1], self.render_paths[i][j])

        pen.setWidth(4)
        pen.setColor(Qt.blue)
        painter.setPen(pen)

        for i in range(len(self.motor_positions)):
            position = self.motor_positions[i]
            center = QPoint(*(position))
            radius = 10
            painter.drawEllipse(center, radius, radius)
            painter.drawText(center.x()+10, center.y()-10, str(i+1)) #start from 1

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.count += 1
            self.render_paths.append([])
            self.render_paths[self.count-1].append(event.pos())

    def mouseMoveEvent(self, event):
        if self.drawing and event.buttons() == Qt.LeftButton:
            self.render_paths[self.count-1].append(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            self.update()
            self.promptLineInput()

    def promptLineInput(self):
        dialog = LineInputDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            start_time, stop_time = dialog.get_times()
            start_time = round(float(start_time), 1)
            stop_time = round(float(stop_time), 1)
            print("Start Time:", start_time)
            print("Stop Time:", stop_time)
            self.render_times.append([start_time, stop_time])
        else:
            print("line is cancalled")
            self.render_paths.pop()
            self.count -= 1

    '''
    Load motor positions from setup file
    '''
    def importSetupFile(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Import Setup File", "", "Text Files (*.txt)")
        if file_path:
            # Parse the setup file to extract motor positions
            # Assuming the file contains one position per line as x, y coordinates
            with open(file_path, "r") as file:
                lines = file.readlines()
                self.motor_positions = []
                for line in lines:
                    parts = line.strip().split(",")
                    if len(parts) == 2:
                        x = int(parts[0])
                        y = int(parts[1])
                        self.motor_positions.append((x, y))
            self.update()
    
    '''
    save drawings to a local file
    '''
    def saveDataToFile(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Save Data", "", "Text Files (*.txt)")
        if file_path:
            with open(file_path, "w") as file:
                for render_time, render_path in zip(self.render_times, self.render_paths):
                    render_path_tuples = [(point.x(), point.y()) for point in render_path]
                    data = {"time": render_time, "path": render_path_tuples}
                    json.dump(data, file)
                    file.write("\n")
    
    '''
    it takes a point position, and finds the nearest motor.
    returns the index of the motor.
    '''
    def findNearestMotor(self, point):
        distances_to_motors = [np.linalg.norm([motor_position[0]-point.x(), motor_position[1]-point.y()]) for motor_position in self.motor_positions]
        return int(np.argmin(distances_to_motors))
    
    '''
    export drawings as commands for vibration units
    '''
    def exportCommands(self):
        commands = []
        for render_time, render_path in zip(self.render_times, self.render_paths):
            duration = render_time[1] - render_time[0]
            between_command_lapse = 0.1
            command_count = int(duration / between_command_lapse)+1
            time_lapses = np.linspace(render_time[0], render_time[1], num=command_count)
            print(time_lapses)
            point_count = len(render_path)
            point_indices, point_step = np.linspace(0, point_count-1, num=command_count, retstep=True)
            print(point_indices, point_step)
            # if point_step is too small, that means the duration is very long, points on the path are selected multiple times. to be fixed.
            for i in range(command_count):
                # can either be rounded to choose the closest point, or use linear interpolation.
                point = render_path[round(point_indices[i])]
                motor_idx = self.findNearestMotor(point)
                commands.append({"time":round(time_lapses[i], 1), "addr":motor_idx+1, "mode":1, "duty":15, "freq":2, "wave":0}) # motor starts from 1
        
        # remove redundant commands and add stop commands.
        commands.sort(key=lambda x: x['time'])
        new_commands = []

        for i in range(len(self.motor_positions)):
            isTriggered = False
            last_vib_time = -1.0
            for command in commands:
                if command['addr'] == i+1:
                    if not isTriggered: # new vibration
                        new_commands.append(command)
                        isTriggered = True
                        last_vib_time = command['time']
                    else: # redundant command
                        if (command['time']-last_vib_time) < between_command_lapse+1e-6:
                            last_vib_time = command['time']
                        else: # should add a stop command
                            stop_command = {"time":round(last_vib_time+between_command_lapse, 1), "addr":command['addr'], "mode":0, "duty":15, "freq":2, "wave":0}
                            new_commands.append(stop_command)
                            new_commands.append(command)
                            last_vib_time = command['time']
            if isTriggered:
                stop_command = {"time":round(last_vib_time+between_command_lapse, 1), "addr":i+1, "mode":0, "duty":15, "freq":2, "wave":0}
                new_commands.append(stop_command)
        
        # power converter start command
        new_commands.append({"time":0, "addr":0, "mode":1, "duty":15, "freq":3, "wave":1})

        new_commands.sort(key=lambda x: x['addr'])
        new_commands.sort(key=lambda x: x['time'])

        # power converter stop command
        last_vib_time = new_commands[-1]['time']
        new_commands.append({"time":last_vib_time+1, "addr":0, "mode":0, "duty":15, "freq":3, "wave":1})

        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Export Commands", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, "w") as file:
                for command in new_commands:
                    json.dump(command, file)
                    file.write("\n")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drawing Application")

        self.drawing_widget = DrawingWidget()
        self.setCentralWidget(self.drawing_widget)

        self.resize(1200, 600)  # Set the window size
        self.createMenu()

    def createMenu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        import_action = QAction("Import Setup", self)
        import_action.triggered.connect(self.drawing_widget.importSetupFile)
        file_menu.addAction(import_action)

        save_action = QAction("Save Drawing", self)
        save_action.triggered.connect(self.drawing_widget.saveDataToFile)
        file_menu.addAction(save_action)

        export_action = QAction("Export As Commands", self)
        export_action.triggered.connect(self.drawing_widget.exportCommands)
        file_menu.addAction(export_action)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
