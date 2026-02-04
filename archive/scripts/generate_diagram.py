"""
Generate System Architecture Diagram as PNG
Run this script to create a PNG image of the system architecture
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create image with white background
width = 1200
height = 1650
img = Image.new('RGB', (width, height), color='white')
draw = ImageDraw.Draw(img)

# Try to use a nice font, fallback to default
try:
    title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 28)
    subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
    label_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Italic.ttf", 16)
except:
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()
    label_font = ImageFont.load_default()

# Colors (matching the web diagram)
colors = {
    'user': '#ffeaa7',
    'frontend': '#74b9ff',
    'backend': '#a29bfe',
    'database': '#fd79a8',
    'calculation': '#00b894',
    'output': '#fab1a0',
    'border': '#2c3e50',
    'text': '#2c3e50',
    'arrow': '#3498db',
    'arrow_bi': '#e91e63'
}

def draw_rounded_rectangle(draw, xy, radius, fill, outline, width=3):
    """Draw a rounded rectangle"""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill, outline=outline, width=0)
    draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill, outline=outline, width=0)
    draw.pieslice([x1, y1, x1+radius*2, y1+radius*2], 180, 270, fill=fill, outline=outline)
    draw.pieslice([x2-radius*2, y1, x2, y1+radius*2], 270, 360, fill=fill, outline=outline)
    draw.pieslice([x1, y2-radius*2, x1+radius*2, y2], 90, 180, fill=fill, outline=outline)
    draw.pieslice([x2-radius*2, y2-radius*2, x2, y2], 0, 90, fill=fill, outline=outline)
    draw.rectangle([x1+radius, y1, x2-radius, y2], fill=None, outline=outline, width=width)
    draw.rectangle([x1, y1+radius, x2, y2-radius], fill=None, outline=outline, width=width)

def draw_arrow(draw, x1, y1, x2, y2, color, width=3):
    """Draw an arrow"""
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    # Arrow head
    draw.polygon([(x2, y2), (x2-10, y2-15), (x2+10, y2-15)], fill=color)

def draw_bidirectional_arrow(draw, x1, y1, x2, y2, color, width=3):
    """Draw a bidirectional arrow"""
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    # Top arrow head
    draw.polygon([(x1, y1), (x1-10, y1+15), (x1+10, y1+15)], fill=color)
    # Bottom arrow head
    draw.polygon([(x2, y2), (x2-10, y2-15), (x2+10, y2-15)], fill=color)

def draw_centered_text(draw, text, x, y, font, fill):
    """Draw centered text"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text((x - text_width/2, y), text, font=font, fill=fill)

# Box positions (x, y, width, height)
boxes = [
    # (x, y, width, height, color, title, subtitles)
    (375, 30, 450, 120, 'user', '👤 User', ['Browser Interface', 'AJAX Requests']),
    (375, 210, 450, 180, 'frontend', '🎨 Frontend', ['HTML Templates', 'JavaScript/jQuery', 'Bootstrap CSS', 'Chart.js Visualization', 'Django Template Engine']),
    (375, 420, 450, 210, 'backend', '⚙️ Django Views', ['URL Routing', 'Request Controllers', 'Balance Algorithm', 'Authentication', 'Session Management', 'JSON API Endpoints']),
    (375, 660, 450, 240, 'database', '💾 Database', ['SQLite Database', 'Django ORM', 'LandUse Model', 'RenewableData Model', 'VerbrauchData Model', 'Cascade Updates', 'Formula Storage']),
    (375, 930, 450, 240, 'calculation', '🔬 Calculation Engine', ['bilanz_engine.py', 'renewable_engine.py', 'verbrauch_engine.py', 'landuse_engine.py', 'formula_evaluator.py', 'Binary Search Algorithm', 'Energy Balance Logic']),
    (375, 1200, 450, 210, 'output', '📊 Output', ['JSON Responses', 'Chart Data', 'Energy Balance Results', 'Visualization Data', 'Dashboard Metrics', 'Real-time Updates'])
]

# Draw boxes
for x, y, w, h, color_key, title, subtitles in boxes:
    draw_rounded_rectangle(draw, [x, y, x+w, y+h], 15, colors[color_key], colors['border'], width=3)
    
    # Draw title
    draw_centered_text(draw, title, x + w/2, y + 20, title_font, colors['text'])
    
    # Draw subtitles
    subtitle_y = y + 60
    for subtitle in subtitles:
        draw_centered_text(draw, subtitle, x + w/2, subtitle_y, subtitle_font, colors['text'])
        subtitle_y += 25

# Draw arrows
center_x = 600

# User to Frontend
draw_arrow(draw, center_x, 150, center_x, 200, colors['arrow'])
draw.text((center_x + 20, 170), 'HTTP POST/GET', font=label_font, fill=colors['text'])

# Frontend to Django
draw_arrow(draw, center_x, 390, center_x, 410, colors['arrow'])
draw.text((center_x + 20, 395), 'HTTP Request', font=label_font, fill=colors['text'])

# Django to Database (bidirectional)
draw_bidirectional_arrow(draw, center_x, 630, center_x, 650, colors['arrow_bi'])
draw.text((center_x + 20, 635), 'ORM Queries', font=label_font, fill=colors['text'])

# Database to Calculation (bidirectional)
draw_bidirectional_arrow(draw, center_x, 900, center_x, 920, colors['arrow_bi'])
draw.text((center_x + 20, 905), 'Data Exchange', font=label_font, fill=colors['text'])

# Calculation to Output
draw_arrow(draw, center_x, 1170, center_x, 1190, colors['arrow'])
draw.text((center_x + 20, 1175), 'Processed Data', font=label_font, fill=colors['text'])

# Output back to Frontend (return arrow on the right side)
return_x = 850
draw.line([(return_x, 1305), (return_x + 150, 1305)], fill=colors['arrow'], width=3)
draw.line([(return_x + 150, 1305), (return_x + 150, 300)], fill=colors['arrow'], width=3)
draw.line([(return_x + 150, 300), (825, 300)], fill=colors['arrow'], width=3)
# Arrow head pointing left
draw.polygon([(825, 300), (840, 290), (840, 310)], fill=colors['arrow'])
draw.text((return_x + 160, 750), 'Response Data', font=label_font, fill=colors['text'], angle=270)

# Save the image
output_path = '/Users/deeptimaheedharan/Desktop/check kiran/check kiran/system_architecture_diagram.png'
img.save(output_path, 'PNG')
print(f"✅ Diagram saved successfully!")
print(f"📁 Location: {output_path}")
print(f"📏 Size: {width}x{height} pixels")
