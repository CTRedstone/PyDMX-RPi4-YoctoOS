import tkinter as tk
import customtkinter as ctk

# Mapping of digit characters to the segments that should be lit
# using the standard 7‑segment notation:
#    A
#  F   B
#    G
#  E   C
#    D
SEGMENT_MAP = {
    '0': ("A", "B", "C", "D", "E", "F"),
    '1': ("B", "C"),
    '2': ("A", "B", "G", "E", "D"),
    '3': ("A", "B", "G", "C", "D"),
    '4': ("F", "G", "B", "C"),
    '5': ("A", "F", "G", "C", "D"),
    '6': ("A", "F", "G", "C", "D", "E"),
    '7': ("A", "B", "C"),
    '8': ("A", "B", "C", "D", "E", "F", "G"),
    '9': ("A", "B", "C", "D", "F", "G"),
    '-': ("G")
}

def draw_digit_on_canvas(canvas, digit, x, y, size, active_color, inactive_color):
    """
    Draws a single 7‑segment digit on the given canvas.
    All seven segments are drawn in inactive_color first,
    then the segments corresponding to the digit (if any) are drawn over in active_color.
    
    Parameters:
      canvas        : The Tkinter canvas.
      digit         : A character ('0'-'9').
      x, y          : Top‑left coordinate of the digit box.
      size          : A scaling factor that determines the segment length.
      active_color  : Color for the "on" segments.
      inactive_color: Color for inactive segments.
    """
    # Determine segment thickness and segment length.
    seg_thick = max(size // 4, 2)
    seg_len = size
    # Define positions for each of the seven segments relative to (x,y)
    # The digit “box” is defined as:
    #   Width  = size + 2 * seg_thick
    #   Height = 2 * size + 3 * seg_thick
    segments = {
        "A": (x + seg_thick, y, x + seg_thick + seg_len, y + seg_thick),  # Top horizontal
        "B": (x + seg_thick + seg_len, y + seg_thick, x + seg_thick + seg_len + seg_thick, y + seg_thick + seg_len),  # Upper right vertical
        "C": (x + seg_thick + seg_len, y + 2*seg_thick + seg_len, x + seg_thick + seg_len + seg_thick, y + 2*seg_thick + 2*seg_len),  # Lower right vertical
        "D": (x + seg_thick, y + 2*seg_thick + 2*seg_len, x + seg_thick + seg_len, y + 2*seg_thick + 2*seg_len + seg_thick),  # Bottom horizontal
        "E": (x, y + 2*seg_thick + seg_len, x + seg_thick, y + 2*seg_thick + 2*seg_len),  # Lower left vertical
        "F": (x, y + seg_thick, x + seg_thick, y + seg_thick + seg_len),  # Upper left vertical
        "G": (x + seg_thick, y + seg_thick + seg_len, x + seg_thick + seg_len, y + seg_thick + seg_len + seg_thick)  # Middle horizontal
    }
    
    # First draw every segment with the inactive color.
    for coords in segments.values():
        canvas.create_rectangle(*coords, fill=inactive_color, outline="")
    
    # Now overlay (redraw) the segments that are active.
    active_segments = SEGMENT_MAP.get(str(digit), [])
    for seg in active_segments:
        if seg in segments:
            canvas.create_rectangle(*segments[seg], fill=active_color, outline="")

def draw_separator_on_canvas(canvas, sep, x, y, digit_height, size, color):
    """
    Draws a separator (':' or ',') on the canvas.
    
    For a colon, two small circles are drawn centered vertically.
    For a comma, a single small circle (or dot) is drawn near the bottom.
    
    Parameters:
      canvas       : The Tkinter canvas.
      sep          : The separator character (':' or ',').
      x, y         : Top‑left coordinate where the separator should be drawn.
      digit_height : The height of a digit (used to position the circles).
      size         : The size factor (used to determine circle radius).
      color        : Color for drawing the separator.
    """
    seg_thick = max(size // 4, 2)
    # Define the separator width (here, we use twice the segment thickness)
    sep_width = seg_thick * 2
    if sep == ":":
        # For a colon, draw two circles (upper and lower dots)
        r = max(seg_thick // 2, 1)
        circle1_center_x = x + sep_width // 2
        circle1_center_y = y + digit_height // 3
        circle2_center_x = x + sep_width // 2
        circle2_center_y = y + 2 * digit_height // 3
        canvas.create_oval(circle1_center_x - r, circle1_center_y - r,
                           circle1_center_x + r, circle1_center_y + r,
                           fill=color, outline="")
        canvas.create_oval(circle2_center_x - r, circle2_center_y - r,
                           circle2_center_x + r, circle2_center_y + r,
                           fill=color, outline="")
    elif sep == ",":
        # For a comma, draw a single small circle (or dot) at the bottom center.
        r = max(seg_thick // 2, 1)
        circle_center_x = x + sep_width // 2
        circle_center_y = y + digit_height - r
        canvas.create_oval(circle_center_x - r, circle_center_y - r,
                           circle_center_x + r, circle_center_y + r,
                           fill=color, outline="")

class SevenSegmentDisplay(ctk.CTkFrame):
    """
    A CustomTkinter frame that displays a number or string using a 7‑segment style.
    Supports multi‑digit numbers as well as separator characters like ':' and ','.
    """
    def __init__(self, master, value="", size=60,
                 active_color="#00DF00", inactive_color="#002C00",
                 bg="black", **kwargs):
        super().__init__(master, **kwargs)
        self.size = size
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.bg = bg
        self.value = value

        # Pre-calculate dimensions for a single digit.
        self.seg_thick = max(self.size // 4, 2)
        self.digit_width = self.size + 2 * self.seg_thick
        self.digit_height = 2 * self.size + 3 * self.seg_thick

        # Create a Tkinter Canvas (embedded into the CTkFrame) for drawing.
        self.canvas = tk.Canvas(self, bg=self.bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.set_value(self.value)

    def set_value(self, value):
        """
        Update the displayed value.
        
        The input value can include digits (0-9) and separators (':' or ',').
        The entire string is drawn centered horizontally.
        """
        self.value = value
        self.canvas.delete("all")

        spacing = self.seg_thick  # spacing between elements
        total_width = 0
        # Compute total width required based on each character.
        for char in value:
            if char.isdigit():
                total_width += self.digit_width + spacing
            elif char in [":", ","]:
                sep_width = self.seg_thick * 2
                total_width += sep_width + spacing
            else:
                total_width += spacing
        total_width = max(total_width - spacing, self.digit_width)  # remove last extra spacing

        # Set canvas dimensions (you may also let the canvas expand fluidly)
        canvas_width = total_width
        canvas_height = self.digit_height
        self.canvas.config(width=canvas_width, height=canvas_height)

        # Center the drawing horizontally
        cur_x = (canvas_width - total_width) // 2
        for char in value:
            if char.isdigit():
                draw_digit_on_canvas(self.canvas, char, cur_x, 0, self.size,
                                     self.active_color, self.inactive_color)
                cur_x += self.digit_width + spacing
            elif char in [":", ","]:
                # Draw the separator with the active color.
                sep_width = self.seg_thick * 2
                draw_separator_on_canvas(self.canvas, char, cur_x, 0,
                                           self.digit_height, self.size, self.active_color)
                cur_x += sep_width + spacing
            else:
                cur_x += spacing
