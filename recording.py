#!/usr/bin/env python
# coding: utf-8

# In[2]:


import sys
import tempfile
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QUrl, QStringListModel, QSize  # Include QSize here
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout, QHBoxLayout, QCompleter, QLabel, QPushButton, QSlider, QStyle, QStackedLayout
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QStringListModel
from PyQt5.QtGui import QPalette, QColor, QFont  # Import QFont here
import mysql.connector

class VideoSearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Search App")
        self.setGeometry(100, 100, 800, 600)

        # Set the background color of the window to black
        self.setStyleSheet("background-color: black; color: white;")

        # Initialize duration attribute to avoid AttributeError
        self.duration = 0
        
        # Initialize the MySQL connection
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="viz_optilytics"
        )
        self.cursor = self.db.cursor()

        self.title = QtWidgets.QLabel("Viz Optilytics")
        self.title.setFont(QtGui.QFont("Arial", 28, QtGui.QFont.Bold))
        self.title.setStyleSheet("color: #FFD700;")  # Title color remains gold
        self.title.setAlignment(QtCore.Qt.AlignLeft)
        
        # Set up search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Enter date (YYYY-MM-DD) or datetime (YYYY-MM-DD_HH-MM-SS)")
        self.search_bar.setStyleSheet("color: white; background-color: green;")  # White text on a green background
        self.search_bar.setFixedHeight(40)  # Increase the height of the search bar
        self.search_bar.textChanged.connect(self.update_completer)

        # Set up video player and video widget
        self.video_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.video_widget = QVideoWidget(self)
        self.video_widget.setStyleSheet("background-color: white;")  # Set video widget background to white
        self.video_widget.setMinimumSize(640, 360)  # Increase the minimum size of the video widget
        self.video_player.setVideoOutput(self.video_widget)

        # Set up message label for video name and duration
        self.message_label = QLabel("", self)

        # Set up video controls: Play, Pause, Stop buttons
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        
        # Set button styles for default yellow background and green on hover
        button_style = """
            QPushButton {
                background-color: green;
                color: black;
                border-radius: 8px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: red;
                color: white;
            }
        """
        self.play_button.setStyleSheet(button_style)
        self.pause_button.setStyleSheet(button_style)
        self.stop_button.setStyleSheet(button_style)
        
        # Set a fixed size for buttons (adjust the width and height as needed)
        button_size = QSize(200, 30)  # Width: 80px, Height: 30px
        self.play_button.setFixedSize(button_size)
        self.pause_button.setFixedSize(button_size)
        self.stop_button.setFixedSize(button_size)
        
        self.play_button.clicked.connect(self.video_player.play)
        self.pause_button.clicked.connect(self.video_player.pause)
        self.stop_button.clicked.connect(self.video_player.stop)

        # Set up slider to control video position
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFixedHeight(20)  # Optionally set a fixed height for the slider
        self.slider.sliderMoved.connect(self.set_video_position)

        # Connect signals to update slider and message label
        self.video_player.positionChanged.connect(self.update_slider)
        self.video_player.durationChanged.connect(self.update_duration)

        # Set up the completer for suggestions
        self.completer = QCompleter(self)
        self.search_bar.setCompleter(self.completer)
        self.completer.activated.connect(self.play_selected_video)

        # Arrange widgets in layout
        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addSpacing(40)  # Add space after the slider
        layout.addWidget(self.search_bar)
        layout.addSpacing(35)  # Add space after the slider
        layout.addWidget(self.video_widget)
        layout.addWidget(self.slider)  # Move the slider directly below the video widget
        # Overlay for video controls (Play, Pause, Stop buttons)
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)

        # Styling for slider color gradient (yellow-green-red)
        self.slider.setStyleSheet(""" 
            QSlider::groove:horizontal {
                height: 8px;
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 yellow, stop:0.5 green, stop:1 red
                );
            }
            QSlider::handle:horizontal {
                background: #555;
                border: 1px solid #444;
                width: 12px;
                margin: -2px 0;
                border-radius: 6px;
            }
        """)
        
        
        # Add control layout to the main layout
        layout.addLayout(controls_layout)
        layout.addSpacing(20)  # Add space after the slide
        layout.addWidget(self.message_label)
        self.setLayout(layout)

    def update_completer(self):
        # Fetch matching video names based on search text
        search_text = self.search_bar.text()
        query = """
        SELECT video_name FROM video_storage 
        WHERE video_name LIKE %s
        """
        self.cursor.execute(query, (f"%{search_text}%",))
        video_names = [row[0] for row in self.cursor.fetchall()]

        # Convert list to QStringListModel for QCompleter
        model = QStringListModel(video_names)
        self.completer.setModel(model)

    def play_selected_video(self, selected_video):
        # Retrieve the binary data for the selected video
        query = """
        SELECT video_file FROM video_storage 
        WHERE video_name = %s
        """
        self.cursor.execute(query, (selected_video,))
        result = self.cursor.fetchone()
        
        if result:
            video_data = result[0]
            
            # Save the video data to a temporary file
            temp_video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            with open(temp_video_file.name, 'wb') as f:
                f.write(video_data)
            
            # Play the video from the temporary file
            video_url = QUrl.fromLocalFile(temp_video_file.name)
            self.video_player.setMedia(QMediaContent(video_url))
            self.video_player.play()
            self.message_label.setText(f"Playing video: {selected_video}")
        else:
            self.message_label.setText("Video not found")

    def update_duration(self, duration):
        # Update the slider range to the video duration
        self.slider.setRange(0, duration)
        self.duration = duration
        self.update_message_label()

    def update_slider(self, position):
        # Update the slider position as the video plays
        self.slider.setValue(position)
        self.update_message_label()

    def set_video_position(self, position):
        # Set the video position when the slider is moved
        self.video_player.setPosition(position)

    def update_message_label(self):
        # Update the message label with current position and total duration
        current_position = self.video_player.position()
        total_duration = self.duration
        self.message_label.setText(
            f"Playing video | Current Time: {self.format_time(current_position)} / Total Duration: {self.format_time(total_duration)}"
        )

    @staticmethod
    def format_time(ms):
        # Format milliseconds to mm:ss
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoSearchApp()
    window.show()
    sys.exit(app.exec_())

