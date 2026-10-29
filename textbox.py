"""Shared behavior for every editable text field in Focus Quest.

Use ``InputBox`` for one-line fields and ``MultilineInputBox`` for text areas.
Both provide a visible insertion cursor, mouse placement and drag selection,
keyboard navigation, held-key deletion, and Ctrl+A/C/X/V editing. Multiline
fields also support line navigation and vertical scrolling. Display-only labels
and buttons should continue to use the regular UI drawing classes.
"""

import pygame

from constants import LIGHT_GRAY, GOLD, WHITE


SELECTION_COLOR = (55, 95, 155)
TEXT_BACKGROUND = (20, 20, 30)


class EditableTextBox:
    """Shared editing behavior for single-line and multiline text boxes."""

    def __init__(self, x, y, width, height, text="", multiline=False, font_size=28):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = LIGHT_GRAY
        self.text = text
        self.font = pygame.font.SysFont(None, font_size)
        self.active = False
        self.multiline = multiline
        self.cursor = len(text)
        self.selection_anchor = None
        self.dragging = False
        self.scroll_x = 0
        self.scroll_y = 0
        self.padding = 8
        self.cursor_blink_ms = 500
        self.cursor_last_moved = pygame.time.get_ticks()
        self.txt_surface = self.font.render(text, True, WHITE)

    def set_text(self, text):
        self.text = text
        self.cursor = len(text)
        self.selection_anchor = None
        self.scroll_x = 0
        self.scroll_y = 0
        self._refresh_surface()
        self._ensure_cursor_visible()

    def _refresh_surface(self):
        self.txt_surface = self.font.render(self.text, True, WHITE)

    def _selection(self):
        if self.selection_anchor is None or self.selection_anchor == self.cursor:
            return None
        return min(self.selection_anchor, self.cursor), max(self.selection_anchor, self.cursor)

    def _line_data(self):
        lines = self.text.split("\n") if self.multiline else [self.text]
        result = []
        start = 0
        for line in lines:
            result.append((line, start))
            start += len(line) + (1 if self.multiline else 0)
        return result

    def _cursor_line_column(self):
        line_data = self._line_data()
        for line_index, (line, start) in enumerate(line_data):
            line_end = start + len(line)
            if self.cursor <= line_end or line_index == len(line_data) - 1:
                return line_index, max(0, min(len(line), self.cursor - start))
        return len(line_data) - 1, len(line_data[-1][0])

    def _text_position(self, line_index, column):
        line_data = self._line_data()
        line_index = max(0, min(line_index, len(line_data) - 1))
        line, start = line_data[line_index]
        column = max(0, min(column, len(line)))
        return start + column

    def _inner_rect(self):
        if not self.multiline:
            line_height = self.font.get_linesize()
            return pygame.Rect(
                self.rect.x + self.padding,
                self.rect.centery - line_height // 2,
                max(1, self.rect.width - self.padding * 2),
                line_height,
            )
        return self.rect.inflate(-self.padding * 2, -self.padding * 2)

    def _ensure_cursor_visible(self):
        inner = self._inner_rect()
        line_data = self._line_data()
        line_index, column = self._cursor_line_column()
        line, _ = line_data[line_index]
        cursor_x = self.font.size(line[:column])[0]
        cursor_y = line_index * self.font.get_linesize()

        if cursor_x < self.scroll_x:
            self.scroll_x = cursor_x
        elif cursor_x - self.scroll_x > inner.width - 2:
            self.scroll_x = cursor_x - max(0, inner.width - 2)

        if self.multiline:
            line_height = self.font.get_linesize()
            visible_height = max(1, inner.height)
            if cursor_y < self.scroll_y:
                self.scroll_y = cursor_y
            elif cursor_y + line_height > self.scroll_y + visible_height:
                self.scroll_y = cursor_y + line_height - visible_height
            max_scroll = max(0, len(line_data) * line_height - visible_height)
            self.scroll_y = max(0, min(self.scroll_y, max_scroll))
        else:
            self.scroll_y = 0

    def _char_column_at_x(self, line, x):
        target_x = max(0, x + self.scroll_x)
        low, high = 0, len(line) + 1
        while low < high:
            middle = (low + high) // 2
            if self.font.size(line[:middle])[0] < target_x:
                low = middle + 1
            else:
                high = middle

        if low == 0:
            return 0
        if low > len(line):
            return len(line)
        before = self.font.size(line[:low - 1])[0]
        after = self.font.size(line[:low])[0]
        return low - 1 if target_x - before < after - target_x else low

    def _index_at_point(self, point):
        inner = self._inner_rect()
        line_data = self._line_data()
        if self.multiline:
            line_height = self.font.get_linesize()
            row = int((point[1] - inner.y + self.scroll_y) // line_height)
            row = max(0, min(row, len(line_data) - 1))
        else:
            row = 0
        line, start = line_data[row]
        column = self._char_column_at_x(line, point[0] - inner.x)
        return start + column

    def _move_cursor(self, new_cursor, selecting=False):
        new_cursor = max(0, min(new_cursor, len(self.text)))
        if selecting:
            if self.selection_anchor is None:
                self.selection_anchor = self.cursor
        else:
            self.selection_anchor = None
        self.cursor = new_cursor
        self.cursor_last_moved = pygame.time.get_ticks()
        self._ensure_cursor_visible()

    def _replace_range(self, start, end, replacement):
        if not self.multiline:
            replacement = replacement.replace("\r", "").replace("\n", " ")
        self.text = self.text[:start] + replacement + self.text[end:]
        self.cursor = start + len(replacement)
        self.selection_anchor = None
        self.cursor_last_moved = pygame.time.get_ticks()
        self._refresh_surface()
        self._ensure_cursor_visible()

    def _insert_text(self, text):
        if not text:
            return
        text = "".join(character for character in text if character in "\n\t" or character.isprintable())
        if not self.multiline:
            text = text.replace("\r", "").replace("\n", " ")
        selected = self._selection()
        start, end = selected if selected else (self.cursor, self.cursor)
        self._replace_range(start, end, text)

    def _delete_backward(self, by_word=False):
        selected = self._selection()
        if selected:
            self._replace_range(*selected, "")
        elif self.cursor > 0:
            start = self.cursor - 1
            if by_word:
                while start > 0 and self.text[start - 1].isspace():
                    start -= 1
                while start > 0 and not self.text[start - 1].isspace():
                    start -= 1
            self._replace_range(start, self.cursor, "")

    def _delete_forward(self, by_word=False):
        selected = self._selection()
        if selected:
            self._replace_range(*selected, "")
        elif self.cursor < len(self.text):
            end = self.cursor + 1
            if by_word:
                while end < len(self.text) and self.text[end].isspace():
                    end += 1
                while end < len(self.text) and not self.text[end].isspace():
                    end += 1
            self._replace_range(self.cursor, end, "")

    def _word_left(self):
        position = self.cursor
        while position > 0 and self.text[position - 1].isspace():
            position -= 1
        while position > 0 and not self.text[position - 1].isspace():
            position -= 1
        return position

    def _word_right(self):
        position = self.cursor
        while position < len(self.text) and not self.text[position].isspace():
            position += 1
        while position < len(self.text) and self.text[position].isspace():
            position += 1
        return position

    def _copy_selection(self, cut=False):
        selected = self._selection()
        if not selected:
            return
        copied_text = self.text[selected[0]:selected[1]]
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, copied_text.encode("utf-8"))
        except (AttributeError, pygame.error):
            return
        if cut:
            self._replace_range(*selected, "")

    def _paste(self):
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            clipboard_text = pygame.scrap.get(pygame.SCRAP_TEXT)
            if clipboard_text:
                self._insert_text(clipboard_text.decode("utf-8", errors="replace").rstrip("\x00"))
        except (AttributeError, pygame.error, UnicodeError):
            pass

    def _handle_keydown(self, event):
        key = event.key
        modifiers = event.mod
        control = bool(modifiers & pygame.KMOD_CTRL)
        shift = bool(modifiers & pygame.KMOD_SHIFT)

        if control:
            if key == pygame.K_a:
                self.selection_anchor = 0
                self.cursor = len(self.text)
                self.cursor_last_moved = pygame.time.get_ticks()
                self._ensure_cursor_visible()
                return None
            if key == pygame.K_c:
                self._copy_selection()
                return None
            if key == pygame.K_x:
                self._copy_selection(cut=True)
                return None
            if key == pygame.K_v:
                self._paste()
                return None

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.multiline:
                self._insert_text("\n")
                return None
            return "enter"
        if key == pygame.K_BACKSPACE:
            self._delete_backward(by_word=control)
            return None
        if key == pygame.K_DELETE:
            self._delete_forward(by_word=control)
            return None

        line_index, column = self._cursor_line_column()
        line_data = self._line_data()
        line, line_start = line_data[line_index]
        if key == pygame.K_LEFT:
            if not shift and self._selection():
                self._move_cursor(self._selection()[0])
            else:
                self._move_cursor(self._word_left() if control else self.cursor - 1, shift)
        elif key == pygame.K_RIGHT:
            if not shift and self._selection():
                self._move_cursor(self._selection()[1])
            else:
                self._move_cursor(self._word_right() if control else self.cursor + 1, shift)
        elif key == pygame.K_UP and self.multiline:
            target_column = column
            if line_index > 0:
                self._move_cursor(self._text_position(line_index - 1, target_column), shift)
        elif key == pygame.K_DOWN and self.multiline:
            target_column = column
            if line_index + 1 < len(line_data):
                self._move_cursor(self._text_position(line_index + 1, target_column), shift)
        elif key == pygame.K_HOME:
            target = 0 if control else line_start
            self._move_cursor(target, shift)
        elif key == pygame.K_END:
            target = len(self.text) if control else line_start + len(line)
            self._move_cursor(target, shift)
        elif key == pygame.K_PAGEUP and self.multiline:
            rows = max(1, self._inner_rect().height // self.font.get_linesize())
            self._move_cursor(self._text_position(max(0, line_index - rows), column), shift)
        elif key == pygame.K_PAGEDOWN and self.multiline:
            rows = max(1, self._inner_rect().height // self.font.get_linesize())
            self._move_cursor(self._text_position(min(len(line_data) - 1, line_index + rows), column), shift)
        return None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.active = True
                self.color = GOLD
                index = self._index_at_point(event.pos)
                if getattr(event, "mod", pygame.key.get_mods()) & pygame.KMOD_SHIFT:
                    if self.selection_anchor is None:
                        self.selection_anchor = self.cursor
                    self.cursor = index
                else:
                    self.cursor = index
                    self.selection_anchor = index
                self.dragging = True
                self.cursor_last_moved = pygame.time.get_ticks()
                self._ensure_cursor_visible()
                try:
                    pygame.key.start_text_input()
                except pygame.error:
                    pass
            else:
                self.active = False
                self.color = LIGHT_GRAY
                self.dragging = False
            return None

        if event.type == pygame.MOUSEMOTION and self.active and self.dragging:
            self.cursor = self._index_at_point(event.pos)
            if self.selection_anchor is None:
                self.selection_anchor = self.cursor
            self.cursor_last_moved = pygame.time.get_ticks()
            if self.multiline:
                inner = self._inner_rect()
                if event.pos[1] < inner.y:
                    self.scroll_y = max(0, self.scroll_y - self.font.get_linesize())
                elif event.pos[1] >= inner.bottom:
                    self.scroll_y += self.font.get_linesize()
            self._ensure_cursor_visible()
            return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            return None

        if event.type == pygame.MOUSEWHEEL and self.active and self.multiline:
            self.scroll_y = max(0, self.scroll_y - event.y * self.font.get_linesize() * 3)
            total_height = len(self._line_data()) * self.font.get_linesize()
            self.scroll_y = min(self.scroll_y, max(0, total_height - self._inner_rect().height))
            return None

        if event.type == pygame.TEXTINPUT and self.active:
            self._insert_text(event.text)
            return None

        if event.type == pygame.KEYDOWN and self.active:
            return self._handle_keydown(event)

        return None

    def draw(self, surface):
        pygame.draw.rect(surface, TEXT_BACKGROUND, self.rect, border_radius=6)
        pygame.draw.rect(surface, self.color, self.rect, 2, border_radius=6)

        viewport = self._inner_rect()
        previous_clip = surface.get_clip()
        surface.set_clip(viewport)
        line_height = self.font.get_linesize()
        selection = self._selection()

        for line_index, (line, line_start) in enumerate(self._line_data()):
            y = viewport.y + line_index * line_height - self.scroll_y
            if y + line_height < viewport.y or y > viewport.bottom:
                continue

            if selection:
                selection_start, selection_end = selection
                line_end = line_start + len(line)
                selected_start = max(selection_start, line_start)
                selected_end = min(selection_end, line_end)
                if selected_start < selected_end:
                    left = self.font.size(line[:selected_start - line_start])[0]
                    right = self.font.size(line[:selected_end - line_start])[0]
                    pygame.draw.rect(
                        surface, SELECTION_COLOR,
                        (viewport.x + left - self.scroll_x, y, max(1, right - left), line_height)
                    )
                elif self.multiline and selection_start <= line_end < selection_end:
                    left = self.font.size(line)[0]
                    pygame.draw.rect(
                        surface, SELECTION_COLOR,
                        (viewport.x + left - self.scroll_x, y, max(4, self.font.size(" ")[0]), line_height)
                    )

            line_surface = self.font.render(line, True, WHITE)
            surface.blit(line_surface, (viewport.x - self.scroll_x, y))

        if self.active:
            now = pygame.time.get_ticks()
            if (now - self.cursor_last_moved) % (self.cursor_blink_ms * 2) < self.cursor_blink_ms:
                line_data = self._line_data()
                line_index, column = self._cursor_line_column()
                line, _ = line_data[line_index]
                cursor_x = viewport.x + self.font.size(line[:column])[0] - self.scroll_x
                cursor_y = viewport.y + line_index * line_height - self.scroll_y
                if viewport.collidepoint(cursor_x, cursor_y + line_height // 2):
                    pygame.draw.line(
                        surface, WHITE,
                        (cursor_x, cursor_y + 2),
                        (cursor_x, cursor_y + line_height - 2), 2
                    )

        surface.set_clip(previous_clip)


class InputBox(EditableTextBox):
    """Single-line editable text field."""

    def __init__(self, x, y, width, height, text=""):
        super().__init__(x, y, width, height, text=text, multiline=False, font_size=28)


class MultilineInputBox(EditableTextBox):
    """Multiline editable text field with vertical and horizontal scrolling."""

    def __init__(self, x, y, width, height, text=""):
        super().__init__(x, y, width, height, text=text, multiline=True, font_size=26)
