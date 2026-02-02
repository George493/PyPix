import pygame
import pygame_gui
import numpy as np
from PIL import Image
import os
import math
import tkinter as tk
from tkinter import filedialog

pygame.init()

CONFIG = {
    'screen_width': 1200,
    'screen_height': 700,
    'default_canvas_width': 32,
    'default_canvas_height': 32,
    'min_pixel_size': 2,
    'max_pixel_size': 32,
    'default_pixel_size': 16,
    'panel_height': 130,
    'scrollbar_size': 20,
    'colors': [
        (0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0),
        (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255),
        
        (128, 128, 128), (64, 64, 64), (192, 192, 192), (96, 96, 96),
        
        (255, 128, 0), (128, 0, 128), (0, 128, 0), (128, 64, 0),
        (255, 192, 203), (64, 224, 208), (255, 218, 185),
        
        (139, 69, 19),
        (75, 0, 130),
        (255, 140, 0),
        (255, 20, 147),
        (0, 128, 128),
        (107, 142, 35),
        (72, 61, 139),
        (199, 21, 133),
        
        (255, 182, 193),
        (173, 216, 230),
        (221, 160, 221),
        (152, 251, 152),
        (240, 230, 140),
        (255, 228, 196),
        (176, 224, 230),
        (255, 239, 213),
        
        (255, 105, 180),
        (0, 255, 127),
        (0, 191, 255),
        (255, 215, 0),
        (218, 112, 214),
        (50, 205, 50),
        (30, 144, 255),
        (255, 69, 0),
        
        (25, 25, 112),
        (139, 0, 0),
        (85, 107, 47),
        (139, 0, 139),
        (0, 100, 0),
        (47, 79, 79),
        (128, 0, 0),
        (105, 105, 105),
        
        (255, 127, 80),
        (138, 43, 226),
        (34, 139, 34),
        (250, 128, 114),
        (123, 104, 238),
        (102, 205, 170),
        (186, 85, 211),
        (244, 164, 96),
        
        (220, 20, 60),
        (0, 206, 209),
        (148, 0, 211),
        (255, 99, 71),
        (64, 224, 208),
        (238, 130, 238),
        (127, 255, 212),
        (255, 160, 122),
        
        (106, 90, 205),
        (205, 92, 92),
        (255, 222, 173),
        (70, 130, 180),
        (210, 105, 30),
        (189, 183, 107),
        (233, 150, 122),
        (143, 188, 143),
    ]
}

class Canvas:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = np.ones((height, width, 3), dtype=np.uint8) * 255
        self.history = []
        self.history_index = -1
        self.show_grid = True
        
    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.save_state()
            self.grid[y, x] = color
            
    def get_pixel(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return tuple(self.grid[y, x])
        return (255, 255, 255)
    
    def fill(self, x, y, new_color):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
            
        old_color = self.get_pixel(x, y)
        if old_color == new_color:
            return
            
        self.save_state()
        stack = [(x, y)]
        visited = set()
        
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))
            
            if tuple(self.grid[cy, cx]) == old_color:
                self.grid[cy, cx] = new_color
                
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if (nx, ny) not in visited:
                            stack.append((nx, ny))
    
    def clear(self):
        self.save_state()
        self.grid[:, :] = 255
        
    def resize(self, new_width, new_height):
        self.save_state()
        new_grid = np.ones((new_height, new_width, 3), dtype=np.uint8) * 255
        
        min_h = min(self.height, new_height)
        min_w = min(self.width, new_width)
        new_grid[:min_h, :min_w] = self.grid[:min_h, :min_w]
        
        self.grid = new_grid
        self.width = new_width
        self.height = new_height
    
    def save_state(self):
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        self.history.append(self.grid.copy())
        self.history_index += 1
        
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1
    
    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.grid = self.history[self.history_index].copy()
            return True
        return False
    
    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.grid = self.history[self.history_index].copy()
            return True
        return False
    
    def to_image(self):
        return Image.fromarray(self.grid, 'RGB')

class PixelArtEditor:
    def __init__(self):
        self.screen = pygame.display.set_mode(
            (CONFIG['screen_width'], CONFIG['screen_height']),
            pygame.RESIZABLE
        )
        pygame.display.set_caption("PyPix - Пиксель-арт редактор")
        
        self.canvas = Canvas(CONFIG['default_canvas_width'], CONFIG['default_canvas_height'])
        self.pixel_size = CONFIG['default_pixel_size']
        self.offset_x = 0
        self.offset_y = 0
        
        self.primary_color = (0, 0, 0)
        self.secondary_color = (255, 255, 255)
        self.current_tool = 'Карандаш'
        self.tools = ['Карандаш', 'Заливка', 'Линия', 'Прямоугольник', 'Эллипс', 'Пипетка', 'Ластик']
        
        self.drawing = False
        self.last_pos = None
        self.first_click = None
        self.temp_canvas = None
        
        self.dragging_horizontal = False
        self.dragging_vertical = False
        
        self.gui_manager = pygame_gui.UIManager((CONFIG['screen_width'], CONFIG['screen_height']))
        self.create_ui()
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.ui_needs_update = False
        
        self.font = pygame.font.SysFont('Arial', 12)
        
    def create_ui(self):
        screen_width, screen_height = self.screen.get_size()
        
        self.gui_manager.clear_and_reset()
        
        panel_top = 10
        panel_bottom = CONFIG['panel_height'] - 10
        panel_mid_y = (panel_top + panel_bottom) // 2
        
        total_padding = 60
        available_width = screen_width - total_padding
        section_width = available_width // 5
        
        section1_x = 10
        self.create_tools_section(section1_x, panel_top, section_width, panel_bottom - panel_top)
        
        section2_x = section1_x + section_width + 10
        self.create_colors_section(section2_x, panel_top, section_width, panel_bottom - panel_top)
        
        section3_x = section2_x + section_width + 10
        self.create_control_section(section3_x, panel_top, section_width, panel_bottom - panel_top)
        
        section4_x = section3_x + section_width + 10
        self.create_file_section(section4_x, panel_top, section_width, panel_bottom - panel_top)
        
        section5_x = section4_x + section_width + 10
        section5_width = screen_width - section5_x - 10
        self.create_settings_section(section5_x, panel_top, section5_width, panel_bottom - panel_top)
        
        self.update_scrollbars()
        
    def create_tools_section(self, x, y, width, height):
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(x, y, width, 20),
            text="Инструменты",
            manager=self.gui_manager
        )
        
        self.tool_buttons = []
        button_height = 22
        tools_y = y + 25
        
        for i, tool in enumerate(self.tools):
            col = i % 2
            row = i // 2
            
            btn_width = (width - 15) // 2
            
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    x + 5 + col * (btn_width + 5), 
                    tools_y + row * (button_height + 3),
                    btn_width, button_height
                ),
                text=tool[:10],
                manager=self.gui_manager
            )
            self.tool_buttons.append(btn)
    
    def create_colors_section(self, x, y, width, height):
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(x, y, width, 20),
            text="Цвета",
            manager=self.gui_manager
        )
        
        colors_y = y + 25
        self.primary_color_rect = pygame.Rect(x + 5, colors_y, 25, 25)
        self.secondary_color_rect = pygame.Rect(x + 35, colors_y, 25, 25)
        
        self.swap_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + 70, colors_y, width - 75, 25),
            text="Поменять",
            manager=self.gui_manager
        )
        
        quick_y = colors_y + 35
        self.quick_colors = []
        color_size = 18
        
        for i, color in enumerate(CONFIG['colors'][:16]):
            col = i % 4
            row = (i % 8) // 4 + (i // 8) * 0

            rect = pygame.Rect(
                x + 5 + col * (color_size + 5) + (i // 8) * (4 * (color_size + 5) + 10),
                quick_y + row * (color_size + 3),
                color_size, color_size
            )
            self.quick_colors.append((rect, color))
    
    def create_control_section(self, x, y, width, height):
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(x, y, width, 20),
            text="Управление",
            manager=self.gui_manager
        )
        
        control_y = y + 25
        btn_height = 22
        
        self.undo_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + 5, control_y, width - 10, btn_height),
            text="Отменить (Z)",
            manager=self.gui_manager
        )
        
        control_y += btn_height + 3
        
        self.redo_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + 5, control_y, width - 10, btn_height),
            text="Повторить (Y)",
            manager=self.gui_manager
        )
        
        control_y += btn_height + 3
        
        self.clear_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + 5, control_y, width - 10, btn_height),
            text="Очистить (C)",
            manager=self.gui_manager
        )
        
        control_y += btn_height + 3
        
        self.grid_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + 5, control_y, width - 10, btn_height),
            text="Сетка: Вкл",
            manager=self.gui_manager
        )
    
    def create_file_section(self, x, y, width, height):
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(x, y, width, 20),
            text="Файлы",
            manager=self.gui_manager
        )
        
        file_y = y + 25
        btn_height = 22
        
        self.save_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + 5, file_y, width - 10, btn_height),
            text="Сохранить (S)",
            manager=self.gui_manager
        )
        
        file_y += btn_height + 3
        
        self.load_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + 5, file_y, width - 10, btn_height),
            text="Загрузить (L)",
            manager=self.gui_manager
        )
        
        size_y = file_y + btn_height + 8
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(x, size_y, width, 18),
            text="Размер:",
            manager=self.gui_manager
        )
        
        size_y += 20
        self.size_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=['16x16', '32x32', '64x64', '128x128', '32x64', '64x32'],
            starting_option='32x32',
            relative_rect=pygame.Rect(x + 5, size_y, width - 10, 22),
            manager=self.gui_manager
        )
    
    def create_settings_section(self, x, y, width, height):
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(x, y, width, 20),
            text="Масштаб",
            manager=self.gui_manager
        )
        
        zoom_y = y + 25
        
        self.zoom_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(x + 5, zoom_y, width - 80, 20),
            start_value=self.pixel_size,
            value_range=(CONFIG['min_pixel_size'], CONFIG['max_pixel_size']),
            manager=self.gui_manager
        )
        
        self.zoom_out_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + width - 70, zoom_y, 30, 20),
            text="-",
            manager=self.gui_manager
        )
        
        self.zoom_in_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + width - 35, zoom_y, 30, 20),
            text="+",
            manager=self.gui_manager
        )
        
        self.zoom_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(x + 5, zoom_y + 25, width - 10, 18),
            text=f"{self.pixel_size}x",
            manager=self.gui_manager
        )
        
        fullscreen_y = zoom_y + 45
        self.fullscreen_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + 5, fullscreen_y, width - 10, 25),
            text="Полный экран",
            manager=self.gui_manager
        )
    
    def update_scrollbars(self):
        screen_width, screen_height = self.screen.get_size()
        
        canvas_width = self.canvas.width * self.pixel_size
        canvas_height = self.canvas.height * self.pixel_size
        
        self.canvas_area_width = screen_width - 40
        self.canvas_area_height = screen_height - CONFIG['panel_height'] - 40
        
        max_offset_x = max(0, canvas_width - self.canvas_area_width)
        max_offset_y = max(0, canvas_height - self.canvas_area_height)
        
        self.offset_x = max(0, min(self.offset_x, max_offset_x))
        self.offset_y = max(0, min(self.offset_y, max_offset_y))
        
        if canvas_width > self.canvas_area_width:
            self.h_scroll_visible = True
            scrollable = canvas_width - self.canvas_area_width
            thumb_width = max(30, int(self.canvas_area_width / canvas_width * (self.canvas_area_width - 40)))
            
            if scrollable > 0:
                thumb_pos = (self.offset_x / scrollable) * (self.canvas_area_width - thumb_width - 40)
            else:
                thumb_pos = 0
                
            self.h_scroll_rect = pygame.Rect(
                20 + thumb_pos,
                screen_height - 25,
                thumb_width,
                15
            )
            self.h_track_rect = pygame.Rect(20, screen_height - 25, self.canvas_area_width - 40, 15)
        else:
            self.h_scroll_visible = False
            self.offset_x = 0
        
        if canvas_height > self.canvas_area_height:
            self.v_scroll_visible = True
            scrollable = canvas_height - self.canvas_area_height
            thumb_height = max(30, int(self.canvas_area_height / canvas_height * (self.canvas_area_height - 40)))
            
            if scrollable > 0:
                thumb_pos = (self.offset_y / scrollable) * (self.canvas_area_height - thumb_height - 40)
            else:
                thumb_pos = 0
                
            self.v_scroll_rect = pygame.Rect(
                screen_width - 25,
                CONFIG['panel_height'] + 20 + thumb_pos,
                15,
                thumb_height
            )
            self.v_track_rect = pygame.Rect(
                screen_width - 25,
                CONFIG['panel_height'] + 20,
                15,
                self.canvas_area_height - 40
            )
        else:
            self.v_scroll_visible = False
            self.offset_y = 0
    
    def handle_events(self):
        for event in pygame.event.get():
            self.gui_manager.process_events(event)
            
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.VIDEORESIZE:
                try:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.gui_manager = pygame_gui.UIManager((event.w, event.h))
                    self.create_ui()
                    self.ui_needs_update = True
                except:
                    print("Ошибка при изменении размера окна")
                
            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                for i, btn in enumerate(self.tool_buttons):
                    if event.ui_element == btn:
                        if i < len(self.tools):
                            self.current_tool = self.tools[i]
                            self.first_click = None
                            self.temp_canvas = None
                
                if event.ui_element == self.swap_btn:
                    self.primary_color, self.secondary_color = self.secondary_color, self.primary_color
                
                elif event.ui_element == self.undo_btn:
                    self.canvas.undo()
                elif event.ui_element == self.redo_btn:
                    self.canvas.redo()
                elif event.ui_element == self.clear_btn:
                    self.canvas.clear()
                elif event.ui_element == self.grid_btn:
                    self.canvas.show_grid = not self.canvas.show_grid
                    self.grid_btn.set_text(f"Сетка: {'Выкл' if not self.canvas.show_grid else 'Вкл'}")
                
                elif event.ui_element == self.save_btn:
                    self.save_image_dialog()
                elif event.ui_element == self.load_btn:
                    self.load_image()
                
                elif event.ui_element == self.zoom_in_btn:
                    self.zoom_in()
                elif event.ui_element == self.zoom_out_btn:
                    self.zoom_out()
                elif event.ui_element == self.fullscreen_btn:
                    self.toggle_fullscreen()
                    
            elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                if event.ui_element == self.zoom_slider:
                    try:
                        new_size = int(event.value)
                        if new_size != self.pixel_size:
                            self.pixel_size = new_size
                            if hasattr(self, 'zoom_label'):
                                self.zoom_label.set_text(f"{self.pixel_size}x")
                            self.ui_needs_update = True
                    except:
                        print("Ошибка изменения масштаба")
                        
            elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                if event.ui_element == self.size_dropdown:
                    try:
                        size_str = event.text
                        if 'x' in size_str:
                            w, h = map(int, size_str.split('x'))
                            self.canvas.resize(w, h)
                            self.ui_needs_update = True
                    except:
                        print("Ошибка изменения размера холста")
            
            mouse_pos = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, color in self.quick_colors:
                    if rect.collidepoint(mouse_pos):
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            self.secondary_color = color
                        else:
                            self.primary_color = color
                        break
            
            self.handle_scrollbars(event, mouse_pos)
            
            self.handle_canvas(event, mouse_pos)
            
            if event.type == pygame.MOUSEWHEEL:
                self.handle_mouse_wheel(event, mouse_pos)
            
            if event.type == pygame.KEYDOWN:
                self.handle_keyboard(event)
    
    def handle_mouse_wheel(self, event, mouse_pos):
        try:
            if event.y > 0:
                self.zoom_in_at_pos(mouse_pos)
            elif event.y < 0:
                self.zoom_out_at_pos(mouse_pos)
        except Exception as e:
            print(f"Ошибка при масштабировании колесом: {e}")
    
    def handle_scrollbars(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.h_scroll_visible and self.h_scroll_rect.collidepoint(mouse_pos):
                self.dragging_horizontal = True
                self.drag_start_x = mouse_pos[0]
                self.drag_start_offset = self.offset_x
                
            elif self.v_scroll_visible and self.v_scroll_rect.collidepoint(mouse_pos):
                self.dragging_vertical = True
                self.drag_start_y = mouse_pos[1]
                self.drag_start_offset = self.offset_y
                
            elif self.h_scroll_visible and self.h_track_rect.collidepoint(mouse_pos):
                canvas_width = self.canvas.width * self.pixel_size
                scrollable = canvas_width - self.canvas_area_width
                click_x = mouse_pos[0] - self.h_track_rect.x
                track_width = self.h_track_rect.width
                thumb_width = self.h_scroll_rect.width
                
                if track_width > thumb_width and scrollable > 0:
                    ratio = click_x / (track_width - thumb_width)
                    self.offset_x = ratio * scrollable
                    self.update_scrollbars()
                    
            elif self.v_scroll_visible and self.v_track_rect.collidepoint(mouse_pos):
                canvas_height = self.canvas.height * self.pixel_size
                scrollable = canvas_height - self.canvas_area_height
                click_y = mouse_pos[1] - self.v_track_rect.y
                track_height = self.v_track_rect.height
                thumb_height = self.v_scroll_rect.height
                
                if track_height > thumb_height and scrollable > 0:
                    ratio = click_y / (track_height - thumb_height)
                    self.offset_y = ratio * scrollable
                    self.update_scrollbars()
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_horizontal = False
            self.dragging_vertical = False
            
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_horizontal:
                delta_x = mouse_pos[0] - self.drag_start_x
                canvas_width = self.canvas.width * self.pixel_size
                scrollable = canvas_width - self.canvas_area_width
                track_width = self.h_track_rect.width
                thumb_width = self.h_scroll_rect.width
                
                if track_width > thumb_width and scrollable > 0:
                    ratio = delta_x / (track_width - thumb_width)
                    self.offset_x = self.drag_start_offset + (ratio * scrollable)
                    self.update_scrollbars()
                    
            elif self.dragging_vertical:
                delta_y = mouse_pos[1] - self.drag_start_y
                canvas_height = self.canvas.height * self.pixel_size
                scrollable = canvas_height - self.canvas_area_height
                track_height = self.v_track_rect.height
                thumb_height = self.v_scroll_rect.height
                
                if track_height > thumb_height and scrollable > 0:
                    ratio = delta_y / (track_height - thumb_height)
                    self.offset_y = self.drag_start_offset + (ratio * scrollable)
                    self.update_scrollbars()
    
    def handle_canvas(self, event, mouse_pos):
        canvas_x = 20 - self.offset_x
        canvas_y = CONFIG['panel_height'] + 20 - self.offset_y
        
        canvas_width = self.canvas.width * self.pixel_size
        canvas_height = self.canvas.height * self.pixel_size
        
        if (canvas_x <= mouse_pos[0] < canvas_x + canvas_width and
            canvas_y <= mouse_pos[1] < canvas_y + canvas_height):
            
            pixel_x = (mouse_pos[0] - canvas_x) // self.pixel_size
            pixel_y = (mouse_pos[1] - canvas_y) // self.pixel_size
            
            if not (0 <= pixel_x < self.canvas.width and 0 <= pixel_y < self.canvas.height):
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                current_color = self.primary_color
                if event.button == 3:
                    current_color = self.secondary_color
                elif event.button == 2:
                    try:
                        color = self.canvas.get_pixel(pixel_x, pixel_y)
                        self.primary_color = color
                    except:
                        pass
                    return
                
                if self.current_tool == 'Карандаш':
                    self.drawing = True
                    try:
                        self.canvas.set_pixel(pixel_x, pixel_y, current_color)
                        self.last_pos = (pixel_x, pixel_y)
                    except:
                        pass
                    
                elif self.current_tool == 'Ластик':
                    self.drawing = True
                    try:
                        self.canvas.set_pixel(pixel_x, pixel_y, (255, 255, 255))
                        self.last_pos = (pixel_x, pixel_y)
                    except:
                        pass
                    
                elif self.current_tool == 'Заливка':
                    try:
                        self.canvas.fill(pixel_x, pixel_y, current_color)
                    except:
                        pass
                    
                elif self.current_tool == 'Пипетка':
                    try:
                        color = self.canvas.get_pixel(pixel_x, pixel_y)
                        if event.button == 1:
                            self.primary_color = color
                        else:
                            self.secondary_color = color
                    except:
                        pass
                        
                elif self.current_tool == 'Линия':
                    if self.first_click is None:
                        self.first_click = (pixel_x, pixel_y)
                    else:
                        try:
                            self.draw_line(self.first_click[0], self.first_click[1], 
                                          pixel_x, pixel_y, current_color)
                        except:
                            pass
                        self.first_click = None
                        self.temp_canvas = None
                        
                elif self.current_tool in ['Прямоугольник', 'Эллипс']:
                    self.drawing = True
                    self.first_click = (pixel_x, pixel_y)
                    self.temp_canvas = self.canvas.grid.copy()
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if self.drawing and self.current_tool in ['Прямоугольник', 'Эллипс'] and self.first_click:
                    start_x, start_y = self.first_click
                    
                    try:
                        if self.current_tool == 'Прямоугольник':
                            self.draw_rectangle(start_x, start_y, pixel_x, pixel_y, 
                                              self.primary_color if event.button == 1 else self.secondary_color)
                        elif self.current_tool == 'Эллипс':
                            self.draw_ellipse(start_x, start_y, pixel_x, pixel_y, 
                                             self.primary_color if event.button == 1 else self.secondary_color)
                    except:
                        pass
                    
                    self.drawing = False
                    self.first_click = None
                    self.temp_canvas = None
                    
                elif self.current_tool in ['Карандаш', 'Ластик']:
                    self.drawing = False
                    self.last_pos = None
                    
            elif event.type == pygame.MOUSEMOTION:
                if self.drawing and self.current_tool == 'Карандаш' and self.last_pos:
                    current_color = self.primary_color if pygame.mouse.get_pressed()[0] else self.secondary_color
                    try:
                        self.draw_line(self.last_pos[0], self.last_pos[1], 
                                      pixel_x, pixel_y, current_color)
                        self.last_pos = (pixel_x, pixel_y)
                    except:
                        pass
                    
                elif self.drawing and self.current_tool == 'Ластик' and self.last_pos:
                    try:
                        self.draw_line(self.last_pos[0], self.last_pos[1], 
                                      pixel_x, pixel_y, (255, 255, 255))
                        self.last_pos = (pixel_x, pixel_y)
                    except:
                        pass
                    
                elif self.drawing and self.current_tool in ['Прямоугольник', 'Эллипс'] and self.first_click and self.temp_canvas is not None:
                    try:
                        self.canvas.grid = self.temp_canvas.copy()
                        start_x, start_y = self.first_click
                        current_color = self.primary_color if pygame.mouse.get_pressed()[0] else self.secondary_color
                        
                        if self.current_tool == 'Прямоугольник':
                            self.draw_rectangle(start_x, start_y, pixel_x, pixel_y, current_color, preview=True)
                        elif self.current_tool == 'Эллипс':
                            self.draw_ellipse(start_x, start_y, pixel_x, pixel_y, current_color, preview=True)
                    except:
                        pass
                        
                elif self.current_tool == 'Линия' and self.first_click:
                    try:
                        if self.temp_canvas is None:
                            self.temp_canvas = self.canvas.grid.copy()
                        else:
                            self.canvas.grid = self.temp_canvas.copy()
                        
                        current_color = self.primary_color if pygame.mouse.get_pressed()[0] else self.secondary_color
                        self.draw_line(self.first_click[0], self.first_click[1], 
                                      pixel_x, pixel_y, current_color, preview=True)
                    except:
                        pass
    
    def handle_keyboard(self, event):
        mods = pygame.key.get_mods()
        
        if event.key == pygame.K_z and mods & pygame.KMOD_CTRL:
            self.canvas.undo()
        elif event.key == pygame.K_y and mods & pygame.KMOD_CTRL:
            self.canvas.redo()
        elif event.key == pygame.K_s and mods & pygame.KMOD_CTRL:
            self.save_image_dialog()
        elif event.key == pygame.K_l and mods & pygame.KMOD_CTRL:
            self.load_image()
        elif event.key == pygame.K_c:
            self.canvas.clear()
        elif event.key == pygame.K_g:
            self.canvas.show_grid = not self.canvas.show_grid
            self.grid_btn.set_text(f"Сетка: {'Выкл' if not self.canvas.show_grid else 'Вкл'}")
        elif event.key == pygame.K_SPACE:
            self.primary_color, self.secondary_color = self.secondary_color, self.primary_color
        elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
            self.zoom_in()
        elif event.key == pygame.K_MINUS:
            self.zoom_out()
        elif event.key == pygame.K_F11:
            self.toggle_fullscreen()
        elif event.key == pygame.K_ESCAPE and pygame.display.get_surface().get_flags() & pygame.FULLSCREEN:
            self.toggle_fullscreen()
    
    def save_image_dialog(self):
        try:
            root = tk.Tk()
            root.withdraw()
            
            file_path = filedialog.asksaveasfilename(
                title="Сохранить изображение",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("Все файлы", "*.*")]
            )
            
            if file_path:
                if not file_path.endswith('.png'):
                    file_path += '.png'
                self.save_image(file_path)
                
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")
    
    def save_image(self, file_path):
        try:
            image = self.canvas.to_image()
            image.save(file_path)
            print(f"Изображение сохранено: {file_path}")
            
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")
    
    def zoom_in(self):
        if self.pixel_size < CONFIG['max_pixel_size']:
            self.pixel_size = min(self.pixel_size * 2, CONFIG['max_pixel_size'])
            try:
                if hasattr(self, 'zoom_slider'):
                    self.zoom_slider.set_current_value(self.pixel_size)
                if hasattr(self, 'zoom_label'):
                    self.zoom_label.set_text(f"{self.pixel_size}x")
                self.ui_needs_update = True
            except:
                pass
    
    def zoom_out(self):
        if self.pixel_size > CONFIG['min_pixel_size']:
            self.pixel_size = max(self.pixel_size // 2, CONFIG['min_pixel_size'])
            try:
                if hasattr(self, 'zoom_slider'):
                    self.zoom_slider.set_current_value(self.pixel_size)
                if hasattr(self, 'zoom_label'):
                    self.zoom_label.set_text(f"{self.pixel_size}x")
                self.ui_needs_update = True
            except:
                pass
    
    def zoom_in_at_pos(self, mouse_pos):
        try:
            if self.pixel_size < CONFIG['max_pixel_size']:
                canvas_x = 20 - self.offset_x
                canvas_y = CONFIG['panel_height'] + 20 - self.offset_y
                
                canvas_width = self.canvas.width * self.pixel_size
                canvas_height = self.canvas.height * self.pixel_size
                
                if (canvas_x <= mouse_pos[0] < canvas_x + canvas_width and
                    canvas_y <= mouse_pos[1] < canvas_y + canvas_height):
                    
                    rel_x = (mouse_pos[0] - canvas_x) / max(self.pixel_size, 1)
                    rel_y = (mouse_pos[1] - canvas_y) / max(self.pixel_size, 1)
                    
                    old_size = self.pixel_size
                    self.zoom_in()
                    
                    if self.pixel_size != old_size:
                        new_x = rel_x * self.pixel_size
                        new_y = rel_y * self.pixel_size
                        
                        self.offset_x += (mouse_pos[0] - 20 - new_x)
                        self.offset_y += (mouse_pos[1] - CONFIG['panel_height'] - 20 - new_y)
        except Exception as e:
            print(f"Ошибка при увеличении масштаба: {e}")
    
    def zoom_out_at_pos(self, mouse_pos):
        try:
            if self.pixel_size > CONFIG['min_pixel_size']:
                canvas_x = 20 - self.offset_x
                canvas_y = CONFIG['panel_height'] + 20 - self.offset_y
                
                canvas_width = self.canvas.width * self.pixel_size
                canvas_height = self.canvas.height * self.pixel_size
                
                if (canvas_x <= mouse_pos[0] < canvas_x + canvas_width and
                    canvas_y <= mouse_pos[1] < canvas_y + canvas_height):
                    
                    rel_x = (mouse_pos[0] - canvas_x) / max(self.pixel_size, 1)
                    rel_y = (mouse_pos[1] - canvas_y) / max(self.pixel_size, 1)
                    
                    old_size = self.pixel_size
                    self.zoom_out()
                    
                    if self.pixel_size != old_size:
                        new_x = rel_x * self.pixel_size
                        new_y = rel_y * self.pixel_size
                        
                        self.offset_x += (mouse_pos[0] - 20 - new_x)
                        self.offset_y += (mouse_pos[1] - CONFIG['panel_height'] - 20 - new_y)
        except Exception as e:
            print(f"Ошибка при уменьшении масштаба: {e}")
    
    def toggle_fullscreen(self):
        try:
            if pygame.display.get_surface().get_flags() & pygame.FULLSCREEN:
                self.screen = pygame.display.set_mode((CONFIG['screen_width'], CONFIG['screen_height']), pygame.RESIZABLE)
            else:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            
            self.gui_manager = pygame_gui.UIManager(self.screen.get_size())
            self.create_ui()
            self.ui_needs_update = True
        except Exception as e:
            print(f"Ошибка переключения полноэкранного режима: {e}")
    
    def draw_line(self, x1, y1, x2, y2, color, preview=False):
        if not preview:
            self.canvas.save_state()
        
        try:
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            sx = 1 if x1 < x2 else -1
            sy = 1 if y1 < y2 else -1
            err = dx - dy
            
            while True:
                if 0 <= x1 < self.canvas.width and 0 <= y1 < self.canvas.height:
                    self.canvas.grid[y1, x1] = color
                
                if x1 == x2 and y1 == y2:
                    break
                
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x1 += sx
                if e2 < dx:
                    err += dx
                    y1 += sy
        except:
            pass
    
    def draw_rectangle(self, x1, y1, x2, y2, color, preview=False):
        if not preview:
            self.canvas.save_state()
        
        try:
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)
            
            for x in range(x_min, x_max + 1):
                for y in range(y_min, y_max + 1):
                    if 0 <= x < self.canvas.width and 0 <= y < self.canvas.height:
                        self.canvas.grid[y, x] = color
        except:
            pass
    
    def draw_ellipse(self, x1, y1, x2, y2, color, preview=False):
        if not preview:
            self.canvas.save_state()
        
        try:
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)
            
            if x_min == x_max or y_min == y_max:
                self.draw_rectangle(x_min, y_min, x_max, y_max, color, preview)
                return
            
            center_x = (x_min + x_max) // 2
            center_y = (y_min + y_max) // 2
            radius_x = abs(x_max - x_min) // 2
            radius_y = abs(y_max - y_min) // 2
            
            if radius_x == 0 or radius_y == 0:
                self.draw_rectangle(x_min, y_min, x_max, y_max, color, preview)
                return
            
            for x in range(x_min, x_max + 1):
                for y in range(y_min, y_max + 1):
                    dx = (x - center_x) / radius_x
                    dy = (y - center_y) / radius_y
                    if dx*dx + dy*dy <= 1.0:
                        if 0 <= x < self.canvas.width and 0 <= y < self.canvas.height:
                            self.canvas.grid[y, x] = color
        except:
            pass
    
    def load_image(self):
        try:
            root = tk.Tk()
            root.withdraw()
            
            file_path = filedialog.askopenfilename(
                title="Выберите изображение",
                filetypes=[("PNG files", "*.png"), ("Все файлы", "*.*")]
            )
            
            if file_path:
                image = Image.open(file_path).convert('RGB')
                self.load_image_data(image)
                print(f"Изображение загружено: {file_path}")
                self.ui_needs_update = True
                
        except Exception as e:
            print(f"Ошибка при загрузке: {e}")
    
    def load_image_data(self, image):
        try:
            self.canvas.save_state()
            img_array = np.array(image)
            self.canvas.grid = img_array
            self.canvas.width = image.width
            self.canvas.height = image.height
        except:
            pass
    
    def draw(self):
        self.screen.fill((50, 54, 60))
        
        self.draw_canvas()
        
        self.draw_ui()
        
        self.draw_scrollbars()
        
        self.gui_manager.draw_ui(self.screen)
        
        self.draw_cursor_info()
    
    def draw_canvas(self):
        canvas_x = 20 - self.offset_x
        canvas_y = CONFIG['panel_height'] + 20 - self.offset_y
        
        pygame.draw.rect(self.screen, (240, 240, 240),
                        (20, CONFIG['panel_height'] + 20,
                         self.canvas_area_width, self.canvas_area_height))
        
        try:
            start_x = max(0, self.offset_x // self.pixel_size)
            end_x = min(self.canvas.width, (self.offset_x + self.canvas_area_width) // self.pixel_size + 1)
            
            start_y = max(0, self.offset_y // self.pixel_size)
            end_y = min(self.canvas.height, (self.offset_y + self.canvas_area_height) // self.pixel_size + 1)
            
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    color = tuple(self.canvas.grid[y, x])
                    rect = pygame.Rect(
                        canvas_x + x * self.pixel_size,
                        canvas_y + y * self.pixel_size,
                        self.pixel_size, self.pixel_size
                    )
                    pygame.draw.rect(self.screen, color, rect)
                    
                    if self.canvas.show_grid and self.pixel_size >= 4:
                        pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)
        except:
            pass
        
        pygame.draw.rect(self.screen, (100, 100, 100),
                        (20, CONFIG['panel_height'] + 20,
                         self.canvas_area_width, self.canvas_area_height), 2)
        
        if self.current_tool == 'Линия' and self.first_click:
            try:
                x, y = self.first_click
                center_x = canvas_x + x * self.pixel_size + self.pixel_size // 2
                center_y = canvas_y + y * self.pixel_size + self.pixel_size // 2
                pygame.draw.circle(self.screen, (255, 0, 0), (center_x, center_y), 4)
            except:
                pass
    
    def draw_ui(self):
        screen_width, _ = self.screen.get_size()
        
        pygame.draw.rect(self.screen, (40, 44, 52), (0, 0, screen_width, CONFIG['panel_height']))
        
        pygame.draw.line(self.screen, (60, 63, 65),
                        (0, CONFIG['panel_height']),
                        (screen_width, CONFIG['panel_height']), 2)
        
        pygame.draw.rect(self.screen, self.primary_color, self.primary_color_rect)
        pygame.draw.rect(self.screen, (30, 30, 30), self.primary_color_rect, 2)
        
        pygame.draw.rect(self.screen, self.secondary_color, self.secondary_color_rect)
        pygame.draw.rect(self.screen, (30, 30, 30), self.secondary_color_rect, 2)
        
        for rect, color in self.quick_colors:
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (30, 30, 30), rect, 1)
            
            if color == self.primary_color:
                pygame.draw.rect(self.screen, (255, 255, 0), rect, 2)
            elif color == self.secondary_color:
                pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
    
    def draw_scrollbars(self):
        screen_width, screen_height = self.screen.get_size()
        
        if self.h_scroll_visible:
            pygame.draw.rect(self.screen, (180, 180, 180), self.h_track_rect, border_radius=3)
            pygame.draw.rect(self.screen, (100, 100, 100), self.h_scroll_rect, border_radius=3)
            pygame.draw.rect(self.screen, (60, 60, 60), self.h_scroll_rect, 2, border_radius=3)
        
        if self.v_scroll_visible:
            pygame.draw.rect(self.screen, (180, 180, 180), self.v_track_rect, border_radius=3)
            pygame.draw.rect(self.screen, (100, 100, 100), self.v_scroll_rect, border_radius=3)
            pygame.draw.rect(self.screen, (60, 60, 60), self.v_scroll_rect, 2, border_radius=3)
    
    def draw_cursor_info(self):
        mouse_pos = pygame.mouse.get_pos()
        canvas_x = 20 - self.offset_x
        canvas_y = CONFIG['panel_height'] + 20 - self.offset_y
        
        canvas_width = self.canvas.width * self.pixel_size
        canvas_height = self.canvas.height * self.pixel_size
        
        if (canvas_x <= mouse_pos[0] < canvas_x + canvas_width and
            canvas_y <= mouse_pos[1] < canvas_y + canvas_height):
            
            try:
                pixel_x = (mouse_pos[0] - canvas_x) // self.pixel_size
                pixel_y = (mouse_pos[1] - canvas_y) // self.pixel_size
                color = self.canvas.get_pixel(pixel_x, pixel_y)
                
                preview_size = 100
                preview_x = min(mouse_pos[0] + 20, self.screen.get_width() - preview_size - 10)
                preview_y = min(mouse_pos[1] + 20, self.screen.get_height() - preview_size - 60)
                
                if preview_y < CONFIG['panel_height'] + 40:
                    preview_y = CONFIG['panel_height'] + 40
                
                pygame.draw.rect(self.screen, (60, 60, 60), (preview_x, preview_y, preview_size, preview_size))
                pygame.draw.rect(self.screen, (100, 100, 100), (preview_x, preview_y, preview_size, preview_size), 2)
                pygame.draw.rect(self.screen, color, (preview_x + 10, preview_y + 10, preview_size - 20, preview_size - 20))
                
                lines = [
                    f"Цвет: {color}",
                    f"X: {pixel_x}, Y: {pixel_y}",
                    f"Инструмент: {self.current_tool}",
                    f"Масштаб: {self.pixel_size}x"
                ]
                
                for i, line in enumerate(lines):
                    text = self.font.render(line, True, (220, 220, 220))
                    self.screen.blit(text, (preview_x, preview_y + preview_size + 5 + i * 16))
            except:
                pass
    
    def run(self):
        while self.running:
            time_delta = self.clock.tick(60) / 1000.0
            
            if self.ui_needs_update:
                self.update_scrollbars()
                self.ui_needs_update = False
            
            self.handle_events()
            
            self.gui_manager.update(time_delta)
            self.draw()
            
            pygame.display.flip()
        
        pygame.quit()

if __name__ == "__main__":
    app = PixelArtEditor()
    app.run()