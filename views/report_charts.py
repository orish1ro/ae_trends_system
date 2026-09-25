"""Lightweight, dependency-free chart widgets for the Reports & Analytics page.

Drawn with QPainter (no matplotlib / QtCharts needed) so they stay visually
consistent with the rest of the app and don't add a new runtime dependency.
"""
from PyQt6.QtWidgets import QWidget, QToolTip
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath

GOLD = "#C7A53B"
SUCCESS = "#22C55E"
DANGER = "#EF4444"
MUTED = "#9C9284"
GRID = "#EDE6D8"
INK = "#20283A"


class LineAreaChart(QWidget):
    """Multi-series line/area chart with hover tooltips."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumHeight(260)
        self.labels = []
        self.series = []          # [{"name","color","values":[...],"fill":bool}]
        self.tooltip_formatter = None
        self._hover_index = None
        self._plot_rect = QRectF()

    def set_data(self, labels, series, tooltip_formatter=None):
        self.labels = labels or []
        self.series = series or []
        self.tooltip_formatter = tooltip_formatter
        self._hover_index = None
        self.update()

    @staticmethod
    def _fmt_short(v):
        av = abs(v)
        if av >= 1_000_000:
            return f"{v/1_000_000:.1f}M"
        if av >= 1000:
            return f"{v/1000:.0f}k"
        return f"{v:.0f}"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        if not self.labels or not self.series or not any(self.series[i]["values"] for i in range(len(self.series))):
            painter.setPen(QColor(MUTED))
            painter.setFont(QFont("Inter", 10))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No data for this period yet")
            painter.end()
            return

        margin_left, margin_right, margin_top, margin_bottom = 58, 16, 14, 28
        plot_rect = QRectF(margin_left, margin_top,
                            rect.width() - margin_left - margin_right,
                            rect.height() - margin_top - margin_bottom)
        self._plot_rect = plot_rect

        all_values = [v for s in self.series for v in s["values"]] or [0]
        max_val = max(max(all_values), 0) * 1.18 or 1
        n = len(self.labels)
        step_x = plot_rect.width() / max(n - 1, 1)

        # Gridlines + y-axis labels
        grid_lines = 4
        for i in range(grid_lines + 1):
            y = plot_rect.top() + plot_rect.height() * i / grid_lines
            painter.setPen(QPen(QColor(GRID), 1))
            painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))
            value = max_val * (1 - i / grid_lines)
            painter.setPen(QColor(MUTED))
            painter.setFont(QFont("Inter", 8))
            painter.drawText(QRectF(0, y - 8, margin_left - 8, 16),
                              Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                              self._fmt_short(value))

        # X-axis labels (thin out if crowded)
        label_step = max(1, n // 6)
        painter.setPen(QColor(MUTED))
        painter.setFont(QFont("Inter", 8))
        for i, label in enumerate(self.labels):
            if i % label_step != 0 and i != n - 1:
                continue
            x = plot_rect.left() + step_x * i
            painter.drawText(QRectF(x - 32, plot_rect.bottom() + 6, 64, 16),
                              Qt.AlignmentFlag.AlignCenter, label)

        # Series
        for s in self.series:
            values = s["values"]
            if not values:
                continue
            color = QColor(s["color"])
            points = [
                QPointF(plot_rect.left() + step_x * i,
                        plot_rect.bottom() - (v / max_val) * plot_rect.height())
                for i, v in enumerate(values)
            ]
            if s.get("fill"):
                fill_color = QColor(color)
                fill_color.setAlpha(32)
                path = QPainterPath()
                path.moveTo(points[0].x(), plot_rect.bottom())
                for p in points:
                    path.lineTo(p)
                path.lineTo(points[-1].x(), plot_rect.bottom())
                path.closeSubpath()
                painter.fillPath(path, fill_color)

            pen = QPen(color, 2.4)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            path = QPainterPath()
            path.moveTo(points[0])
            for p in points[1:]:
                path.lineTo(p)
            painter.drawPath(path)

            if len(points) <= 45:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                for p in points:
                    painter.drawEllipse(p, 2.6, 2.6)

        # Hover crosshair
        if self._hover_index is not None and 0 <= self._hover_index < n:
            x = plot_rect.left() + step_x * self._hover_index
            painter.setPen(QPen(QColor(GOLD), 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(x, plot_rect.top()), QPointF(x, plot_rect.bottom()))

        # Legend
        if len(self.series) > 1:
            lx = plot_rect.left()
            ly = 2
            painter.setFont(QFont("Inter", 8, QFont.Weight.Bold))
            for s in self.series:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(s["color"]))
                painter.drawEllipse(QPointF(lx + 4, ly + 5), 4, 4)
                painter.setPen(QColor(INK))
                painter.drawText(QRectF(lx + 12, ly, 110, 14),
                                  Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, s["name"])
                lx += 12 + len(s["name"]) * 6 + 22
        painter.end()

    def _index_at(self, x):
        if not self.labels:
            return None
        n = len(self.labels)
        step_x = self._plot_rect.width() / max(n - 1, 1)
        if step_x <= 0:
            return 0
        idx = round((x - self._plot_rect.left()) / step_x)
        return max(0, min(n - 1, idx))

    def mouseMoveEvent(self, event):
        pos = event.position()
        if not self._plot_rect.contains(QPointF(pos.x(), self._plot_rect.center().y())) and \
           not (self._plot_rect.left() - 10 <= pos.x() <= self._plot_rect.right() + 10):
            self._hover_index = None
            QToolTip.hideText()
            self.update()
            return
        idx = self._index_at(pos.x())
        if idx != self._hover_index:
            self._hover_index = idx
            self.update()
        if idx is not None and self.tooltip_formatter:
            text = self.tooltip_formatter(idx, self.labels[idx], self.series)
            QToolTip.showText(event.globalPosition().toPoint(), text, self)

    def leaveEvent(self, event):
        self._hover_index = None
        QToolTip.hideText()
        self.update()


class DonutChart(QWidget):
    """Simple donut/ring chart. Pass segments as [(label, value, color_hex), ...]."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.segments = []

    def set_data(self, segments):
        self.segments = segments or []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height()) - 24
        side = max(side, 60)
        rect = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)
        pen_width = max(12, int(side * 0.16))
        inner = rect.adjusted(pen_width / 2, pen_width / 2, -pen_width / 2, -pen_width / 2)

        total = sum(v for _, v, _ in self.segments)
        if total <= 0:
            pen = QPen(QColor(GRID), pen_width)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen)
            painter.drawArc(inner, 0, 360 * 16)
            painter.setPen(QColor(MUTED))
            painter.setFont(QFont("Inter", 9))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No orders\nyet")
            painter.end()
            return

        start_angle = 90 * 16
        for _, value, color in self.segments:
            span = -int(360 * 16 * (value / total))
            pen = QPen(QColor(color), pen_width)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen)
            painter.drawArc(inner, start_angle, span)
            start_angle += span

        painter.setPen(QColor(INK))
        painter.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        painter.drawText(rect.adjusted(0, -6, 0, -6), Qt.AlignmentFlag.AlignCenter, str(int(total)))
        painter.setPen(QColor(MUTED))
        painter.setFont(QFont("Inter", 8))
        painter.drawText(rect.adjusted(0, 16, 0, 16), Qt.AlignmentFlag.AlignCenter, "orders")
        painter.end()