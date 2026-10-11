"""Design tokens and shared widgets, borrowed from waypoint's design language.

Five colour tokens, each a (light, dark) pair that customtkinter resolves against
the current appearance mode. Red is reserved for recording and errors; everything
else is greyscale.
"""

import re
import subprocess
import sys
import tkinter.font
from functools import cache

import customtkinter as ctk

BG = ("#ffffff", "#1e1e1e")
FG = ("#1a1a1a", "#f2f2f2")
MUTED = ("#6b6b6b", "#9a9a9a")
BORDER = ("#d8d8d8", "#3a3a3a")
ERROR = ("#a4262c", "#ff9a9a")

# Hover shades for filled buttons: a step toward the muted grey.
FG_HOVER = ("#3d3d3d", "#d4d4d4")
ERROR_HOVER = ("#871f24", "#ffb4b4")

# What `system-ui` resolves to across the desktops this runs on, best first.
_FAMILIES = ("Ubuntu Sans", "Cantarell", "Inter", "Segoe UI", "Noto Sans")

BODY_SIZE = 15
SMALL_SIZE = 12
PRIMARY_SIZE = 14
HEADING_SIZE = 17


def parse_xft_dpi(xrdb_output: str) -> float | None:
    """Extract the Xft.dpi value from ``xrdb -query`` output."""
    match = re.search(r"^Xft\.dpi:\s*(\S+)", xrdb_output, re.MULTILINE)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


@cache
def xft_dpi() -> float | None:
    """The DPI fontconfig renders at on X11/XWayland, or None if unknown."""
    if not sys.platform.startswith("linux"):
        return None
    try:
        result = subprocess.run(
            ["xrdb", "-query"], capture_output=True, text=True, timeout=2
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_xft_dpi(result.stdout)


def display_scale() -> float:
    """The desktop's scale factor (2.0 at 200%), as seen by X11 apps."""
    dpi = xft_dpi()
    return dpi / 96 if dpi else 1.0


def match_font_dpi(root) -> None:
    """Make Tk's pixel font sizes come out at the pixel size asked for.

    Tk turns a pixel size into points assuming the X screen's DPI (96), but
    fontconfig renders those points at Xft.dpi — 192 under GNOME's native
    XWayland scaling at 200% — so every font came out twice its size while
    widget geometry did not. Telling Tk the real DPI makes the two agree;
    customtkinter's scaling then enlarges fonts and geometry together.
    """
    dpi = xft_dpi()
    if dpi:
        root.tk.call("tk", "scaling", dpi / 72)


@cache
def _family() -> str:
    available = set(tkinter.font.families())
    return next((f for f in _FAMILIES if f in available), "TkDefaultFont")


def font(size: int = BODY_SIZE, weight: str = "normal") -> ctk.CTkFont:
    """A CTkFont in the UI family; *size* is in pixels."""
    return ctk.CTkFont(family=_family(), size=size, weight=weight)


def resolve(color: tuple[str, str]) -> str:
    """Pick the light or dark half of a token, for raw tk widgets like Canvas."""
    return color[1] if ctk.get_appearance_mode() == "Dark" else color[0]


def blend(color: tuple[str, str], toward: tuple[str, str], amount: float) -> str:
    """Mix *amount* (0..1) of *toward* into *color* — tk has no opacity."""
    a, b = resolve(color), resolve(toward)
    mixed = (
        round(int(a[i : i + 2], 16) * (1 - amount) + int(b[i : i + 2], 16) * amount)
        for i in (1, 3, 5)
    )
    return "#" + "".join(f"{c:02x}" for c in mixed)


class Pill(ctk.CTkButton):
    """Waypoint's rounded button, in three weights.

    ``"outline"`` is waypoint's pill: muted at rest, full colour on hover.
    ``"link"`` drops the border, for quiet secondary actions.
    ``"filled"`` is solid and larger — reserved for the one thing the user is
    there to do next (Record, then Accept).

    ``accent=True`` swaps the neutral colour for the recording red.
    """

    def __init__(
        self,
        master,
        text: str,
        command,
        variant: str = "outline",
        accent: bool = False,
        large: bool = False,
    ) -> None:
        self._accent = accent
        large = large or variant == "filled"
        pill_font = font(PRIMARY_SIZE, "bold" if variant == "filled" else "normal")
        if not large:
            pill_font = font(SMALL_SIZE)
        height = 36 if large else 26
        tone = ERROR if accent else FG

        if variant == "filled":
            style = dict(
                fg_color=tone,
                hover_color=ERROR_HOVER if accent else FG_HOVER,
                text_color=BG,
                border_width=0,
            )
        else:
            style = dict(
                fg_color="transparent",
                hover=False,
                text_color=self._rest_text(),
                border_color=self._rest_border(),
                border_width=1 if variant == "outline" else 0,
            )

        super().__init__(
            master,
            text=text,
            command=command,
            width=pill_font.measure(text) + (44 if large else 26),
            height=height,
            corner_radius=height // 2,
            border_spacing=4,
            text_color_disabled=BORDER,
            font=pill_font,
            **style,
        )
        if variant != "filled":
            # Named so as not to shadow CTkButton._on_enter/_on_leave, which
            # track whether the pointer is inside — clicks only fire if it is.
            self.bind("<Enter>", self._hover_on)
            self.bind("<Leave>", self._hover_off)

    def _rest_text(self) -> tuple[str, str]:
        return ERROR if self._accent else MUTED

    def _rest_border(self) -> tuple[str, str]:
        return ERROR if self._accent else BORDER

    def _hover_on(self, _event=None) -> None:
        if self.cget("state") == "disabled":
            return
        self.configure(
            text_color=ERROR if self._accent else FG,
            border_color=ERROR if self._accent else MUTED,
        )

    def _hover_off(self, _event=None) -> None:
        self.configure(text_color=self._rest_text(), border_color=self._rest_border())
