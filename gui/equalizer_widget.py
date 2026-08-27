"""
Animated Audio Equalizer Visualizer for Yakob Assistant.
Renders real-time pulsating frequency visualizer bars that react
when music or radio is streaming.
"""
import random
import math
import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional


class AudioEqualizerWidget(ctk.CTkFrame):
    def __init__(self, master, num_bars: int = 16, height: int = 32, is_active_fn: Optional[Callable[[], bool]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", height=height, **kwargs)
        self.num_bars = num_bars
        self.eq_height = height
        self.is_active_fn = is_active_fn or (lambda: False)
        self._animation_running = True
        self._target_heights = [3.0] * num_bars
        self._current_heights = [3.0] * num_bars
        self._phase = 0.0

        # Create canvas for buttery-smooth rendering
        self.canvas = tk.Canvas(
            self,
            height=height,
            width=num_bars * 7,
            bg="#141822",
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        self._start_animation()

    def _start_animation(self):
        self._animate()

    def _animate(self):
        if not self.winfo_exists():
            return

        is_active = self.is_active_fn()
        self._phase += 0.15

        self.canvas.delete("all")
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.eq_height

        if canvas_w <= 1:
            canvas_w = self.num_bars * 7

        bar_width = max(3, (canvas_w - (self.num_bars * 2)) // self.num_bars)
        spacing = 2

        # Vibrant Cyberpunk Gradient Palette
        colors = ["#38bdf8", "#60a5fa", "#818cf8", "#a78bfa", "#c084fc", "#e879f9", "#f43f5e"]

        for i in range(self.num_bars):
            if is_active:
                # Dynamic sinusoidal frequency wave simulation
                sine_val = math.sin(self._phase + i * 0.45) * 0.5 + 0.5
                rand_kick = random.uniform(0.7, 1.3)
                target = max(4.0, sine_val * (canvas_h - 4) * rand_kick)
                # Smooth interpolation
                self._current_heights[i] += (target - self._current_heights[i]) * 0.35
            else:
                # Flat idle bar
                self._current_heights[i] += (3.0 - self._current_heights[i]) * 0.2

            h = max(2.0, min(float(canvas_h), self._current_heights[i]))
            x0 = i * (bar_width + spacing) + 4
            x1 = x0 + bar_width
            y0 = canvas_h - h
            y1 = canvas_h

            color = colors[i % len(colors)] if is_active else "#334155"
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="", width=0)

        self.after(45, self._animate)
