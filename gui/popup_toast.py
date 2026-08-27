"""
Minimalist Desktop Notification Toast Popup for Yakob Assistant.
Displays a clean, frameless, non-intrusive response bubble at the bottom-right
of the screen when running in Silent Chatbot Mode or when minimized.
"""
import time
import threading
import tkinter as tk
import customtkinter as ctk

from config import ASSISTANT_NAME, ASSISTANT_NAME_AM

TOAST_THEME = {
    "bg": "#0f1219",
    "card": "#181d28",
    "border": "#2c3548",
    "primary": "#3b82f6",
    "text_primary": "#f8fafc",
    "text_secondary": "#94a3b8",
}


class ResponseToast(ctk.CTkToplevel):
    def __init__(self, parent=None, title_text="✦ Yakob", message_text=""):
        super().__init__(parent)
        
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.96)
        self.configure(fg_color=TOAST_THEME["bg"])

        # Calculate position: bottom right above taskbar
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        toast_w = 380
        toast_h = 110
        pos_x = screen_w - toast_w - 24
        pos_y = screen_h - toast_h - 60
        self.geometry(f"{toast_w}x{toast_h}+{pos_x}+{pos_y}")

        # Container Card
        card = ctk.CTkFrame(
            self,
            corner_radius=16,
            fg_color=TOAST_THEME["card"],
            border_width=1,
            border_color=TOAST_THEME["border"]
        )
        card.pack(fill="both", expand=True, padx=2, pady=2)

        # Header Row
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(10, 2))

        title_lbl = ctk.CTkLabel(
            hdr,
            text=f"✦ {ASSISTANT_NAME} ({ASSISTANT_NAME_AM})",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TOAST_THEME["primary"]
        )
        title_lbl.pack(side="left")

        close_btn = ctk.CTkButton(
            hdr,
            text="✕",
            width=20,
            height=20,
            corner_radius=10,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            hover_color="#331a1a",
            text_color="gray70",
            command=self.destroy
        )
        close_btn.pack(side="right")

        # Message Preview
        preview = message_text if len(message_text) <= 120 else (message_text[:120] + "...")
        msg_lbl = ctk.CTkLabel(
            card,
            text=preview,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TOAST_THEME["text_primary"],
            wraplength=340,
            justify="left"
        )
        msg_lbl.pack(anchor="w", padx=16, pady=(0, 10))

        # Auto-dismiss after 6 seconds
        self.after(6000, self._fade_out)

    def _fade_out(self):
        try:
            self.destroy()
        except Exception:
            pass


def show_response_toast(parent=None, message: str = ""):
    """Helper to display response toast non-blockingly."""
    try:
        ResponseToast(parent=parent, message_text=message)
    except Exception as e:
        print(f"[Toast] Note: {e}")
