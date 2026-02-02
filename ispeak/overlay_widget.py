# ispeak/overlay_widget.py

import math
from PyQt6.QtWidgets import QWidget, QApplication, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath, QFont, QFontMetrics


class OverlayWidget(QWidget):
    """Animated overlay that appears at the bottom of the screen during voice recording.

    Supports three modes:
    - Listening: Shows animated waveform
    - Processing: Shows bouncing dots
    - Streaming: Shows live transcription text with waveform
    """

    # States
    STATE_HIDDEN = 0
    STATE_LISTENING = 1
    STATE_PROCESSING = 2
    STATE_STREAMING = 3  # New state for live transcription

    def __init__(self):
        super().__init__()

        # State
        self._state = self.STATE_HIDDEN
        self._animation_frame = 0.0
        self._interim_text = ""  # Live transcription text
        self._final_text = ""    # Final confirmed text

        # Window setup - frameless, transparent, always on top, NO FOCUS
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)

        # Ensure we never become the active window
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Size (dynamic for streaming mode)
        self._base_width = 200
        self._base_height = 80
        self._max_width = 600  # Maximum width for text display
        self._text_height = 100  # Height when showing text
        self._width = self._base_width
        self._height = self._base_height
        self.setFixedSize(self._width, self._height)

        # Animation timer (60fps)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.setInterval(16)  # ~60fps

        # Waveform bar settings
        self._num_bars = 7
        self._bar_width = 8
        self._bar_gap = 6
        self._bar_max_height = 50
        self._bar_min_height = 10

        # Processing dots settings
        self._num_dots = 3
        self._dot_radius = 8
        self._dot_gap = 20

        # Colors
        self._bg_color = QColor(30, 30, 30, 220)
        self._bar_color = QColor(0, 200, 255)  # Cyan
        self._dot_color = QColor(255, 255, 255)  # White
        self._text_color = QColor(255, 255, 255)  # White
        self._interim_text_color = QColor(180, 180, 180)  # Gray for interim

        # Font for text display
        self._font = QFont("SF Pro", 14)
        self._font.setWeight(QFont.Weight.Medium)

    def show_listening(self):
        """Show the overlay with listening animation."""
        if self._state == self.STATE_LISTENING:
            return

        self._state = self.STATE_LISTENING
        self._animation_frame = 0.0
        self._interim_text = ""
        self._resize_for_state()
        self._position_on_screen()
        self._timer.start()
        self.show()

    def show_streaming(self):
        """Show the overlay in streaming mode with text display."""
        self._state = self.STATE_STREAMING
        self._animation_frame = 0.0
        self._resize_for_state()
        self._position_on_screen()

        if not self._timer.isActive():
            self._timer.start()

        self.show()
        self.update()

    def update_interim_text(self, text: str):
        """Update the interim (live) transcription text."""
        self._interim_text = text
        self._resize_for_state()
        self._position_on_screen()
        self.update()

    def show_processing(self):
        """Transition to processing animation."""
        if self._state == self.STATE_PROCESSING:
            return

        self._state = self.STATE_PROCESSING
        self._animation_frame = 0.0
        self._resize_for_state()

        if not self.isVisible():
            self._position_on_screen()
            self.show()

        if not self._timer.isActive():
            self._timer.start()

        self.update()

    def hide_overlay(self):
        """Hide the overlay."""
        self._state = self.STATE_HIDDEN
        self._timer.stop()
        self._interim_text = ""
        self.hide()

    def _resize_for_state(self):
        """Resize the widget based on current state."""
        if self._state == self.STATE_STREAMING and self._interim_text:
            # Calculate width based on text
            metrics = QFontMetrics(self._font)
            text_width = metrics.horizontalAdvance(self._interim_text) + 40  # Padding
            self._width = min(self._max_width, max(self._base_width, text_width))
            self._height = self._text_height
        else:
            self._width = self._base_width
            self._height = self._base_height

        self.setFixedSize(self._width, self._height)

    def _position_on_screen(self):
        """Position the overlay at the bottom center of the screen."""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            x = geometry.x() + (geometry.width() - self._width) // 2
            y = geometry.y() + geometry.height() - self._height - 50
            self.move(x, y)

    def _animate(self):
        """Animation tick - called every 16ms."""
        self._animation_frame += 0.1
        self.update()

    def paintEvent(self, event):
        """Draw the overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Draw background
        self._draw_background(painter)

        # Draw content based on state
        if self._state == self.STATE_LISTENING:
            self._draw_waveform(painter)
        elif self._state == self.STATE_PROCESSING:
            self._draw_processing_dots(painter)
        elif self._state == self.STATE_STREAMING:
            self._draw_streaming_content(painter)

        painter.end()

    def _draw_background(self, painter: QPainter):
        """Draw rounded rectangle background."""
        path = QPainterPath()
        path.addRoundedRect(0, 0, self._width, self._height, 15, 15)
        painter.fillPath(path, QBrush(self._bg_color))

    def _draw_waveform(self, painter: QPainter):
        """Draw animated waveform bars."""
        total_width = self._num_bars * self._bar_width + (self._num_bars - 1) * self._bar_gap
        start_x = (self._width - total_width) // 2
        center_y = self._height // 2

        painter.setPen(Qt.PenStyle.NoPen)

        for i in range(self._num_bars):
            # Each bar oscillates at a different phase
            phase_offset = i * 0.5
            height_factor = 0.5 + 0.5 * math.sin(self._animation_frame + phase_offset)
            bar_height = self._bar_min_height + height_factor * (self._bar_max_height - self._bar_min_height)

            x = start_x + i * (self._bar_width + self._bar_gap)
            y = center_y - bar_height / 2

            # Gradient-like effect: center bars brighter
            distance_from_center = abs(i - (self._num_bars - 1) / 2) / ((self._num_bars - 1) / 2)
            alpha = int(255 * (1 - 0.3 * distance_from_center))
            color = QColor(self._bar_color)
            color.setAlpha(alpha)

            painter.setBrush(QBrush(color))

            # Draw rounded bar
            path = QPainterPath()
            path.addRoundedRect(x, y, self._bar_width, bar_height, self._bar_width / 2, self._bar_width / 2)
            painter.fillPath(path, QBrush(color))

    def _draw_processing_dots(self, painter: QPainter):
        """Draw animated processing dots."""
        total_width = self._num_dots * (self._dot_radius * 2) + (self._num_dots - 1) * self._dot_gap
        start_x = (self._width - total_width) // 2 + self._dot_radius
        center_y = self._height // 2

        painter.setPen(Qt.PenStyle.NoPen)

        for i in range(self._num_dots):
            # Each dot bounces sequentially
            phase_offset = i * 0.8
            bounce = max(0, math.sin(self._animation_frame * 1.5 + phase_offset))

            x = start_x + i * (self._dot_radius * 2 + self._dot_gap)
            y = center_y - bounce * 15  # Bounce up to 15px

            # Fade based on bounce
            alpha = int(150 + 105 * bounce)
            color = QColor(self._dot_color)
            color.setAlpha(alpha)

            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(x - self._dot_radius), int(y - self._dot_radius),
                              self._dot_radius * 2, self._dot_radius * 2)

    def _draw_streaming_content(self, painter: QPainter):
        """Draw streaming mode with text and mini waveform."""
        # Draw mini waveform at the top
        mini_bar_height_max = 20
        mini_bar_height_min = 5
        mini_bar_width = 4
        mini_bar_gap = 3
        num_mini_bars = 5

        total_mini_width = num_mini_bars * mini_bar_width + (num_mini_bars - 1) * mini_bar_gap
        start_x = (self._width - total_mini_width) // 2
        bar_center_y = 25

        painter.setPen(Qt.PenStyle.NoPen)

        for i in range(num_mini_bars):
            phase_offset = i * 0.6
            height_factor = 0.5 + 0.5 * math.sin(self._animation_frame * 1.5 + phase_offset)
            bar_height = mini_bar_height_min + height_factor * (mini_bar_height_max - mini_bar_height_min)

            x = start_x + i * (mini_bar_width + mini_bar_gap)
            y = bar_center_y - bar_height / 2

            color = QColor(self._bar_color)
            color.setAlpha(200)

            path = QPainterPath()
            path.addRoundedRect(x, y, mini_bar_width, bar_height, mini_bar_width / 2, mini_bar_width / 2)
            painter.fillPath(path, QBrush(color))

        # Draw text
        if self._interim_text:
            painter.setFont(self._font)

            # Draw interim text (what's being transcribed)
            painter.setPen(self._interim_text_color)
            text_rect = self.rect().adjusted(20, 45, -20, -15)

            # Elide text if too long
            metrics = QFontMetrics(self._font)
            elided_text = metrics.elidedText(self._interim_text, Qt.TextElideMode.ElideRight, text_rect.width())

            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop, elided_text)

        # Draw "Listening..." label if no text yet
        if not self._interim_text:
            painter.setFont(self._font)
            painter.setPen(self._interim_text_color)
            painter.drawText(self.rect().adjusted(0, 40, 0, 0),
                           Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                           "Listening...")
