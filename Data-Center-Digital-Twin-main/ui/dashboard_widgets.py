"""
Custom dashboard widgets for the datacenter digital twin UI.
Includes charts, gauges, and enhanced visualizations.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer, QObject, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QFont, QPainterPath, 
                         QLinearGradient, QPixmap, QImage, QRadialGradient) 
from collections import deque
import math
import copy # <-- Import copy for deepcopy

# --- Helper function for color interpolation ---
def interpolate_color(color1, color2, ratio):
    """Interpolates between two QColors."""
    if not isinstance(color1, QColor) or not isinstance(color2, QColor):
        return QColor(0,0,0) # Return black on error
    r = int(color1.red() * (1 - ratio) + color2.red() * ratio)
    g = int(color1.green() * (1 - ratio) + color2.green() * ratio)
    b = int(color1.blue() * (1 - ratio) + color2.blue() * ratio)
    a = int(color1.alpha() * (1 - ratio) + color2.alpha() * ratio)
    return QColor(r, g, b, a)

# --- Worker thread for generating the heatmap ---
class HeatmapWorker(QObject):
    """Runs the slow heatmap generation in a background thread."""
    finished = pyqtSignal(QPixmap)

    def __init__(self, rows, cols, get_color_func, img_width, img_height):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.get_color_for_temp = get_color_func
        self.img_width = img_width
        self.img_height = img_height
        self.is_busy = False

    # --- NEW: Function to pre-smooth the data ---
    def _create_smoothed_grid(self, temp_grid):
        """Averages each rack with its neighbors to create smooth zones."""
        smoothed_grid = copy.deepcopy(temp_grid) # Start with a copy
        
        for r in range(self.rows):
            for c in range(self.cols):
                total_temp = 0
                count = 0
                
                # Loop through 3x3 neighbors
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = r + dr, c + dc
                        # Check if neighbor is valid
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            total_temp += temp_grid[nr][nc]
                            count += 1
                
                # Set the new smoothed temperature
                if count > 0:
                    smoothed_grid[r][c] = total_temp / count
                    
        return smoothed_grid

    @pyqtSlot(list)
    def generate_map(self, temps):
        """Generates the heatmap pixmap."""
        if self.is_busy:
            return
        self.is_busy = True

        if not temps:
            self.is_busy = False
            return

        # Create a 2D grid of temperatures
        temp_grid = []
        idx = 0
        for r in range(self.rows):
            row_data = []
            for c in range(self.cols):
                if idx < len(temps):
                    row_data.append(temps[idx])
                    idx += 1
                else:
                    row_data.append(25.0) 
            temp_grid.append(row_data)

        # --- FIX: Run the smoothing pass FIRST ---
        smoothed_temp_grid = self._create_smoothed_grid(temp_grid)

        # Create a QImage for pixel-by-pixel drawing
        img = QImage(self.img_width, self.img_height, QImage.Format_ARGB32)
        img.fill(QColor("#1A1A2E")) 

        # Calculate cell dimensions
        cell_width = self.img_width / (self.cols - 1) if self.cols > 1 else 0
        cell_height = self.img_height / (self.rows - 1) if self.rows > 1 else 0
        
        if cell_width == 0 or cell_height == 0:
            self.is_busy = False
            return 

        # Iterate over each pixel in the QImage
        for y_pixel in range(self.img_height):
            for x_pixel in range(self.img_width):
                
                # --- FIX (GLITCH): Corrected range mapping math ---
                grid_x = x_pixel * (self.cols - 1) / (self.img_width - 1)
                grid_y = y_pixel * (self.rows - 1) / (self.img_height - 1)

                x0 = int(grid_x)
                y0 = int(grid_y)
                
                # Clamp to avoid edge cases
                x0 = max(0, min(self.cols - 2, x0))
                y0 = max(0, min(self.rows - 2, y0))
                
                x1 = x0 + 1
                y1 = y0 + 1

                fx = grid_x - x0
                fy = grid_y - y0
                # --- End of Glitch Fix ---
                
                try:
                    # --- Use the SMOOTHED grid for interpolation ---
                    temp00 = smoothed_temp_grid[y0][x0]
                    temp10 = smoothed_temp_grid[y0][x1]
                    temp01 = smoothed_temp_grid[y1][x0]
                    temp11 = smoothed_temp_grid[y1][x1]
                except IndexError:
                    continue 

                color00 = self.get_color_for_temp(temp00)
                color10 = self.get_color_for_temp(temp10)
                color01 = self.get_color_for_temp(temp01)
                color11 = self.get_color_for_temp(temp11)

                color_top = interpolate_color(color00, color10, fx)
                color_bottom = interpolate_color(color01, color11, fx)
                
                final_color = interpolate_color(color_top, color_bottom, fy)

                img.setPixelColor(x_pixel, y_pixel, final_color)

        self.is_busy = False
        self.finished.emit(QPixmap.fromImage(img))


class MetricGauge(QWidget):
    """Circular gauge widget for displaying metrics like PUE."""
    
    def __init__(self, title="Metric", min_val=0, max_val=100, unit="", 
                 good_threshold=None, warning_threshold=None, reverse_colors=False):
        super().__init__()
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.unit = unit
        self.current_value = min_val
        self.good_threshold = good_threshold
        self.warning_threshold = warning_threshold
        self.reverse_colors = reverse_colors
        self.setMinimumSize(160, 200)
        self.setMaximumSize(220, 240)
        
    def set_value(self, value):
        self.current_value = max(self.min_val, min(self.max_val, value))
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        center_x = rect.width() / 2
        center_y = rect.height() / 2 - 25
        radius = min(rect.width(), rect.height()) / 2 - 40
        
        # Draw title above gauge
        painter.setPen(QColor("#95A5A6"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(QRectF(0, 8, rect.width(), 25), Qt.AlignCenter, self.title)
        
        # Draw background arc
        painter.setPen(QPen(QColor("#3D3D5C"), 8, Qt.SolidLine, Qt.RoundCap))
        start_angle = 135 * 16
        span_angle = 270 * 16
        painter.drawArc(int(center_x - radius), int(center_y - radius), 
                        int(radius * 2), int(radius * 2), start_angle, span_angle)
        
        # Calculate value position
        value_ratio = (self.current_value - self.min_val) / (self.max_val - self.min_val)
        value_angle = 135 + (270 * value_ratio)
        
        # Determine color based on thresholds
        if self.reverse_colors:
            if self.good_threshold and self.current_value <= self.good_threshold:
                color = QColor("#2ECC71")
            elif self.warning_threshold and self.current_value <= self.warning_threshold:
                color = QColor("#F39C12")
            else:
                color = QColor("#E74C3C")
        else:
            if self.good_threshold and self.current_value >= self.good_threshold:
                color = QColor("#2ECC71")
            elif self.warning_threshold and self.current_value >= self.warning_threshold:
                color = QColor("#F39C12")
            else:
                color = QColor("#E74C3C")
        
        # Draw value arc with gradient
        gradient = QLinearGradient(center_x - radius, center_y, center_x + radius, center_y)
        gradient.setColorAt(0, color.darker(120))
        gradient.setColorAt(1, color)
        painter.setPen(QPen(QBrush(gradient), 8, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(int(center_x - radius), int(center_y - radius),
                        int(radius * 2), int(radius * 2), start_angle, int(270 * value_ratio * 16))
        
        # Draw icon in center of gauge (within the circle)
        icon_color = QColor("#4D4D6E")
        
        # Choose icon based on title with custom drawing
        if "PUE" in self.title:
            # Draw a lightning bolt for efficiency
            painter.setPen(Qt.NoPen)
            painter.setBrush(icon_color)
            
            bolt_path = QPainterPath()
            bolt_x = center_x
            bolt_y = center_y - 2
            
            # Lightning bolt shape
            bolt_path.moveTo(bolt_x + 2, bolt_y - 12)
            bolt_path.lineTo(bolt_x - 6, bolt_y)
            bolt_path.lineTo(bolt_x - 1, bolt_y)
            bolt_path.lineTo(bolt_x - 4, bolt_y + 12)
            bolt_path.lineTo(bolt_x + 6, bolt_y - 2)
            bolt_path.lineTo(bolt_x + 1, bolt_y - 2)
            bolt_path.closeSubpath()
            
            painter.drawPath(bolt_path)
            
        elif "Temp" in self.title:
            # Draw a simple thermometer shape
            painter.setPen(QPen(icon_color, 3))
            painter.setBrush(Qt.NoBrush)
            therm_x = center_x
            therm_y = center_y - 5
            # Thermometer bulb (circle at bottom)
            painter.drawEllipse(int(therm_x - 6), int(therm_y + 8), 12, 12)
            # Thermometer tube (rectangle)
            painter.drawRect(int(therm_x - 2), int(therm_y - 10), 4, 18)
            # Fill the bulb
            painter.setBrush(icon_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(therm_x - 4), int(therm_y + 10), 8, 8)
            
        elif "Power" in self.title:
            # Draw a power/gear icon
            painter.setPen(QPen(icon_color, 2))
            painter.setBrush(Qt.NoBrush)
            
            gear_x = center_x
            gear_y = center_y - 2
            gear_radius = 10
            
            # Draw outer gear circle
            painter.drawEllipse(int(gear_x - gear_radius), int(gear_y - gear_radius), 
                              gear_radius * 2, gear_radius * 2)
            
            # Draw gear teeth (8 teeth)
            for i in range(8):
                angle = (i * 45) * 3.14159 / 180
                x1 = gear_x + gear_radius * math.cos(angle)
                y1 = gear_y + gear_radius * math.sin(angle)
                x2 = gear_x + (gear_radius + 4) * math.cos(angle)
                y2 = gear_y + (gear_radius + 4) * math.sin(angle)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # Draw center circle
            painter.setBrush(icon_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(gear_x - 4), int(gear_y - 4), 8, 8)
            
        else:
            painter.setPen(icon_color)
            painter.setFont(QFont("Segoe UI", 26))
            icon = "●"
            painter.drawText(QRectF(0, center_y - 13, rect.width(), 35), Qt.AlignCenter, icon)
        
        # Draw value text with unit inline
        painter.setPen(color)
        painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
        value_text = f"{self.current_value:.2f}"
        
        # Calculate text width for centering
        metrics = painter.fontMetrics()
        value_width = metrics.horizontalAdvance(value_text)
        
        value_y_position = center_y + radius + 25
        
        if self.unit:
            # Calculate combined width to center both together
            painter.setFont(QFont("Segoe UI", 14))
            unit_metrics = painter.fontMetrics()
            unit_width = unit_metrics.horizontalAdvance(self.unit)
            total_width = value_width + unit_width + 8
            
            # Draw value
            painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
            painter.setPen(color)
            value_x = center_x - total_width / 2
            painter.drawText(QRectF(value_x, value_y_position, value_width + 15, 35), Qt.AlignLeft | Qt.AlignVCenter, value_text)
            
            # Draw unit next to value
            painter.setFont(QFont("Segoe UI", 14))
            painter.setPen(QColor("#95A5A6"))
            unit_x = value_x + value_width + 8
            painter.drawText(QRectF(unit_x, value_y_position + 5, unit_width + 15, 35), Qt.AlignLeft | Qt.AlignVCenter, self.unit)
        else:
            # Just draw value centered
            painter.drawText(QRectF(0, value_y_position, rect.width(), 35), Qt.AlignCenter, value_text)


class TrendChart(QWidget):
    """
    Line chart widget, with support for a second (forecast) series
    and gradient fill.
    """
    
    def __init__(self, title="Trend", max_points=50, y_label="Value", color="#4D96FF", 
                 forecast_steps=30, goal_text=None, y_min=None, y_max=None):
        super().__init__()
        self.title = title
        self.y_label = y_label
        self.color = QColor(color)
        self.max_points = max_points
        self.forecast_steps = forecast_steps
        self.data_points = deque(maxlen=max_points)
        self.forecast_points = []
        
        self.goal_text = goal_text
        self.y_min = y_min
        self.y_max = y_max
        
        self.setMinimumSize(400, 300) 
        
    def add_data_point(self, value):
        if self.y_min is not None and value < self.y_min:
            value = self.y_min
        if self.y_max is not None and value > self.y_max:
            value = self.y_max
            
        self.data_points.append(value)
        self.update()
    
    def update_forecast_data(self, forecast_data):
        self.forecast_points = forecast_data
        self.update()
        
    def clear_data(self):
        self.data_points.clear()
        self.forecast_points = []
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        margin = 50
        chart_rect = QRectF(margin, margin + 20, rect.width() - margin * 2, rect.height() - margin * 2 - 20)
        
        # Draw title
        painter.setPen(QColor("#BDC3C7"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(QRectF(0, 10, rect.width(), 30), Qt.AlignCenter, self.title)
        
        if self.goal_text:
            painter.setPen(QColor("#7F8C8D"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(QRectF(0, 30, rect.width(), 20), Qt.AlignCenter, self.goal_text)
        
        painter.fillRect(chart_rect, QColor("#1A1A2E"))
        painter.setPen(QPen(QColor("#3D3D5C"), 1))
        painter.drawRect(chart_rect)
        
        if len(self.data_points) < 2:
            painter.setPen(QColor("#95A5A6"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(chart_rect, Qt.AlignCenter, "Collecting data...")
            return
        
        all_points = list(self.data_points) + self.forecast_points
        
        if self.y_min is not None and self.y_max is not None:
            min_val = self.y_min
            max_val = self.y_max
        else:
            min_val = min(all_points) if all_points else 0
            max_val = max(all_points) if all_points else 1
            
        value_range = max_val - min_val if max_val != min_val else 1
        
        painter.setPen(QPen(QColor("#3D3D5C"), 1, Qt.DotLine))
        num_grid_lines = 5
        for i in range(num_grid_lines):
            y = chart_rect.top() + (chart_rect.height() / (num_grid_lines - 1)) * i
            painter.drawLine(int(chart_rect.left()), int(y), int(chart_rect.right()), int(y))
        
        
        points = list(self.data_points)
        
        total_x_points = (self.max_points - 1) + self.forecast_steps
        if total_x_points == 0: total_x_points = 1
        x_step = chart_rect.width() / total_x_points
        
        line_path = QPainterPath()
        fill_path = QPainterPath()
        
        current_x_offset = (self.max_points - len(points)) * x_step
        start_x = chart_rect.left() + current_x_offset
        
        fill_path.moveTo(start_x, chart_rect.bottom())

        first_value = points[0]
        first_y = chart_rect.bottom() - (((first_value - min_val) / value_range) * chart_rect.height())

        line_path.moveTo(start_x, first_y)
        fill_path.lineTo(start_x, first_y)

        last_x = start_x
        for i, value in enumerate(points[1:], 1):
            y_ratio = (value - min_val) / value_range
            x = chart_rect.left() + current_x_offset + (i * x_step)
            y = chart_rect.bottom() - (y_ratio * chart_rect.height())
            
            line_path.lineTo(x, y)
            fill_path.lineTo(x, y)
            last_x = x

        fill_path.lineTo(last_x, chart_rect.bottom())
        fill_path.lineTo(chart_rect.left() + current_x_offset, chart_rect.bottom())
        fill_path.closeSubpath()

        gradient = QLinearGradient(chart_rect.center().x(), chart_rect.top(), chart_rect.center().x(), chart_rect.bottom())
        gradient_color = QColor(self.color)
        gradient_color.setAlpha(90)
        gradient.setColorAt(0, gradient_color)
        gradient_color.setAlpha(0)
        gradient.setColorAt(1, gradient_color)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawPath(fill_path)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(self.color, 3))
        painter.drawPath(line_path)
        
        
        if self.forecast_points and len(self.data_points) > 0:
            forecast_path = QPainterPath()
            
            last_actual_value = points[-1]
            last_actual_x = last_x
            last_actual_y = chart_rect.bottom() - (((last_actual_value - min_val) / value_range) * chart_rect.height())
            forecast_path.moveTo(last_actual_x, last_actual_y)
            
            for i, value in enumerate(self.forecast_points):
                if self.y_min is not None and value < self.y_min: value = self.y_min
                if self.y_max is not None and value > self.y_max: value = self.y_max
                
                y_ratio = (value - min_val) / value_range
                x = last_actual_x + ((i + 1) * x_step)
                y = chart_rect.bottom() - (y_ratio * chart_rect.height())
                
                if x > chart_rect.right() + 5:
                    break
                    
                forecast_path.lineTo(x, y)

            forecast_pen = QPen(self.color.lighter(110), 3, Qt.DotLine)
            painter.setPen(forecast_pen)
            painter.drawPath(forecast_path)

        painter.setPen(QColor("#95A5A6"))
        painter.setFont(QFont("Segoe UI", 8))
        for i in range(num_grid_lines):
            y = chart_rect.top() + (chart_rect.height() / (num_grid_lines - 1)) * i
            value = max_val - (value_range / (num_grid_lines - 1)) * i
            painter.drawText(QRectF(5, y - 10, margin - 10, 20), Qt.AlignRight | Qt.AlignVCenter, f"{value:.1f}")


class AlertPanel(QFrame):
    """Panel for displaying system alerts and warnings."""
    
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #28284B;
                border-radius: 8px;
                border: 1px solid #3D3D5C;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("System Alerts")
        title.setStyleSheet("font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; color: #4D96FF; margin-bottom: 5px;")
        layout.addWidget(title)
        
        self.alerts_layout = QVBoxLayout()
        self.alerts_layout.setSpacing(5)
        layout.addLayout(self.alerts_layout)
        layout.addStretch()
        
        self.alerts = []
        
    def add_alert(self, message, severity="info"):
        """Add an alert message. Severity: info, warning, critical, good"""
        if len(self.alerts) > 0:
            last_alert_text = self.alerts[-1].text()
            if message in last_alert_text:
                return
        
        colors = {
            "info": "#4D96FF",
            "warning": "#F39C12",
            "critical": "#E74C3C",
            "good": "#2ECC71"
        }
        icons = {
            "info": "ℹ",
            "warning": "⚠",
            "critical": "✗",
            "good": "✓"
        }
        
        alert_widget = QLabel(f"{icons.get(severity, 'ℹ')} {message}")
        alert_widget.setStyleSheet(f"""
            font-family: 'Segoe UI';
            color: {colors.get(severity, '#4D96FF')};
            font-size: 10px;
            padding: 8px 10px;
            background-color: rgba(255, 255, 255, 0.03);
            border-left: 3px solid {colors.get(severity, '#4D96FF')};
            border-radius: 4px;
        """)
        alert_widget.setWordWrap(True)
        
        self.alerts_layout.addWidget(alert_widget)
        self.alerts.append(alert_widget)
        
        if len(self.alerts) > 8:
            old_alert = self.alerts.pop(0)
            self.alerts_layout.removeWidget(old_alert)
            old_alert.deleteLater()
    
    def clear_alerts(self):
        for alert in self.alerts:
            self.alerts_layout.removeWidget(alert)
            alert.deleteLater()
        self.alerts.clear()


class EnhancedHeatmap(QWidget):
    """Enhanced heatmap with hover tooltips and rack details."""
    
    # --- FIX (SMOOTHER): Drastically reduced internal heatmap resolution ---
    HEATMAP_IMG_WIDTH = 50  # Was 200
    HEATMAP_IMG_HEIGHT = 25 # Was 100

    request_new_map = pyqtSignal(list)

    def __init__(self, rows=20, cols=35):
        super().__init__()
        self.rows, self.cols = rows, cols
        self.rack_temps = [25.0] * (rows * cols)
        self.rack_workloads = [50.0] * (rows * cols)
        self.setMinimumHeight(300)
        self.setMouseTracking(True)
        self.hover_rack = -1
        
        # --- FIX (COLOR MAP): Adjusted thresholds for better shallow color perception ---
        self.color_map = [
            (20.0, QColor(0, 0, 139, 255)),    # Dark Blue (cool)
            (27.0, QColor(0, 128, 0, 255)),    # Green (starts 1 degree earlier)
            (32.0, QColor(255, 255, 0, 255)),  # Yellow (starts 1 degree earlier)
            (36.0, QColor(255, 165, 0, 255)),  # Orange (starts 1 degree earlier)
            (39.0, QColor(255, 0, 0, 255)),    # Red (starts 1 degree earlier)
            (45.0, QColor(139, 0, 0, 255))     # Dark Red (hot)
        ]
        # --- End of Color Fix ---
        
        self.color_map.sort(key=lambda x: x[0])

        self.heatmap_pixmap = QPixmap(self.HEATMAP_IMG_WIDTH, self.HEATMAP_IMG_HEIGHT)
        self.heatmap_pixmap.fill(QColor("#1A1A2E")) 

        self.heatmap_thread = QThread()
        self.heatmap_worker = HeatmapWorker(
            self.rows, self.cols, self.get_color_for_temp,
            self.HEATMAP_IMG_WIDTH, self.HEATMAP_IMG_HEIGHT
        )
        self.heatmap_worker.moveToThread(self.heatmap_thread)
        
        self.heatmap_worker.finished.connect(self.on_pixmap_ready)
        self.request_new_map.connect(self.heatmap_worker.generate_map)
        
        # --- Make sure thread quits when app closes ---
        self.heatmap_thread.finished.connect(self.heatmap_worker.deleteLater)
        self.heatmap_thread.start()
        print("Heatmap worker thread started.")
    
    # --- Add this function to properly shut down the thread ---
    def closeEvent(self, event):
        """Clean up the thread when the widget is closed."""
        self.heatmap_thread.quit()
        self.heatmap_thread.wait()
        super().closeEvent(event)

    @pyqtSlot(QPixmap)
    def on_pixmap_ready(self, pixmap):
        self.heatmap_pixmap = pixmap
        self.update() 

    def get_color_for_temp(self, temp):
        if not self.color_map:
            return QColor(0,0,0) 
            
        if temp <= self.color_map[0][0]:
            return self.color_map[0][1]
        if temp >= self.color_map[-1][0]:
            return self.color_map[-1][1]

        for i in range(len(self.color_map) - 1):
            temp1, color1 = self.color_map[i]
            temp2, color2 = self.color_map[i+1]
            
            if temp1 <= temp <= temp2:
                if (temp2 - temp1) == 0:
                    return color1
                ratio = (temp - temp1) / (temp2 - temp1)
                return interpolate_color(color1, color2, ratio)
                
        return self.color_map[0][1] 

    def update_data(self, temps, workloads=None):
        if not temps: 
             self.rack_temps = [25.0] * (self.rows * self.cols)
        else:
            self.rack_temps = temps
            
        if workloads:
            self.rack_workloads = workloads
        
        self.request_new_map.emit(self.rack_temps)
        
    def mouseMoveEvent(self, event):
        rect = self.rect()
        if not rect.isValid(): return

        cell_width = rect.width() / self.cols
        cell_height = rect.height() / self.rows

        if cell_width == 0 or cell_height == 0:
            return

        col = int(event.x() / cell_width)
        row = int(event.y() / cell_height)
        
        new_hover_rack = -1
        if 0 <= row < self.rows and 0 <= col < self.cols:
            new_hover_rack = row * self.cols + col
        
        if new_hover_rack != self.hover_rack:
            self.hover_rack = new_hover_rack
            self.update() 
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform) 
        
        rect = self.rect()
        if not rect.isValid():
            return
            
        if not self.heatmap_pixmap.isNull():
            painter.drawPixmap(rect, self.heatmap_pixmap)
        else:
            painter.fillRect(rect, QColor("#1A1A2E"))
            painter.setPen(Qt.white)
            painter.drawText(rect, Qt.AlignCenter, "Generating heatmap...")

        # --- FIX 3 (GRID): Make grid more visible ---
        painter.setPen(QColor(0, 0, 0, 90)) # BLACK grid
        cell_width = rect.width() / self.cols
        cell_height = rect.height() / self.rows
        
        if cell_width > 0 and cell_height > 0:
            # Draw vertical lines
            for i in range(1, self.cols):
                x = int(i * cell_width)
                painter.drawLine(x, 0, x, rect.height())
                
            # Draw horizontal lines
            for i in range(1, self.rows):
                y = int(i * cell_height)
                painter.drawLine(0, y, rect.width(), y)
        # --- End of Grid Fix ---

        # Draw tooltip
        if self.hover_rack >= 0 and self.hover_rack < len(self.rack_temps):
            temp = self.rack_temps[self.hover_rack]
            workload = self.rack_workloads[self.hover_rack] if self.rack_workloads and self.hover_rack < len(self.rack_workloads) else 0
            
            tooltip_text = f"Rack {self.hover_rack + 1}\nTemp: {temp:.1f}°C\nWorkload: {workload:.0f}%"
            
            painter.setFont(QFont("Segoe UI", 9))
            metrics = painter.fontMetrics()
            lines = tooltip_text.split('\n')
            max_width = max(metrics.horizontalAdvance(line) for line in lines)
            tooltip_height = len(lines) * metrics.height() + 10
            
            hover_col = self.hover_rack % self.cols
            hover_row = self.hover_rack // self.cols
            
            tooltip_x = int(hover_col * cell_width)
            tooltip_y = int(hover_row * cell_height)
            
            if tooltip_x + max_width + 20 > rect.width():
                tooltip_x = rect.width() - max_width - 20
            if tooltip_y - tooltip_height - 10 < 0:
                tooltip_y = int(hover_row * cell_height) + int(cell_height) + 10
            else:
                tooltip_y = tooltip_y - tooltip_height - 10

            painter.setBrush(QColor("#28284B"))
            painter.setPen(QPen(QColor("#4D96FF"), 2))
            painter.drawRoundedRect(tooltip_x, tooltip_y, max_width + 10, tooltip_height, 5, 5)
            
            painter.setPen(QColor("#ECF0F1"))
            y_offset = tooltip_y + metrics.height() 
            for line in lines:
                painter.drawText(tooltip_x + 5, y_offset, line)
                y_offset += metrics.height()