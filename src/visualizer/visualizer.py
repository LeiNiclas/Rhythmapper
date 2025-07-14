import argparse
import os
import pygame
import time
from pygame.locals import *

parser = argparse.ArgumentParser()
parser.add_argument("--beatmap_path", type=str, default=os.path.join(os.getcwd(), "generation", "test.gblf"))
parser.add_argument("--audio_path", type=str, default=os.path.join(os.getcwd(), "generation", "audio", "test_audio.mp3"))
args = parser.parse_args()

GENERATED_FILE_PATH = args.beatmap_path
AUDIO_FILE_PATH = args.audio_path
HIT_SFX_FILE_PATH = os.path.join(os.getcwd(), "src", "visualizer", "hit_sfx.mp3")

# The hit SFX is royalty free.
# Download: https://pixabay.com/sound-effects/electronic-closed-hat-11-stereo-100413/

VISUALIZER_VERSION = "1.4"
FPS = 144

# -------- Colors --------
NOTE_L0_BASE_COL = (200, 150, 255)
NOTE_L0_ACCENT_COL = (225, 175, 255)
NOTE_L0_SHADOW_COL = (75, 25, 130)

NOTE_L1_BASE_COL = (255, 200, 150)
NOTE_L1_ACCENT_COL = (255, 225, 175)
NOTE_L1_SHADOW_COL = (130, 75, 25)

NOTE_L2_BASE_COL = (150, 255, 200)
NOTE_L2_ACCENT_COL = (175, 255, 225)
NOTE_L2_SHADOW_COL = (25, 130, 75)

NOTE_L3_BASE_COL = (200, 255, 150)
NOTE_L3_ACCENT_COL = (225, 255, 175)
NOTE_L3_SHADOW_COL = (75, 130, 25)

NOTE_BASE_COLS = [ NOTE_L0_BASE_COL, NOTE_L1_BASE_COL, NOTE_L2_BASE_COL, NOTE_L3_BASE_COL ]
NOTE_ACCENT_COLS = [ NOTE_L0_ACCENT_COL, NOTE_L1_ACCENT_COL, NOTE_L2_ACCENT_COL, NOTE_L3_ACCENT_COL ]
NOTE_SHADOW_COLS = [ NOTE_L0_SHADOW_COL, NOTE_L1_SHADOW_COL, NOTE_L2_SHADOW_COL, NOTE_L3_SHADOW_COL ]

BG_COL = (225, 225, 255)
BG_ACCENT_COL = (240, 240, 255)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
# ------------------------

# -------- Input --------
KEY_LANE_MAP = {
    pygame.K_d: 0,
    pygame.K_f: 1,
    pygame.K_j: 2,
    pygame.K_k: 3
}

keys_held = [ False ] * 4
last_pressed_times = [ 999 ] * 4
last_pressed_colors = [ WHITE ] * 4

KEYPRESS_FADE_DURATION = 0.2
# -----------------------

# -------- General --------
SCREEN_WIDTH = 512
SCREEN_HEIGHT = 1024

USE_AUTOPLAY = True

NOTE_DISPLAY_MODE = 3
NOTE_SPRITE_TYPE = 1

JUDGEMENT_Y_POSITION = 850

SCROLL_SPEED = 1.2
# -------------------------




class Note():
    def __init__(self, lane, timing_ms, raw_pred_value, is_placed_note):
        self.lane = lane
        self.timing_ms = timing_ms
        self.x_pos = lane * 128 + 64
        self.y_pos = -1000
        self.raw_pred_value = raw_pred_value
        self.is_placed_note = is_placed_note
        self.base_color = BLACK


    def update(self, current_timing_ms):
        self.y_pos = SCROLL_SPEED * (current_timing_ms - self.timing_ms) + JUDGEMENT_Y_POSITION


    def draw(self, surface):
        base_color, shadow_color, accent_color = get_note_colors(
            lane=self.lane,
            is_placed_note=self.is_placed_note,
            raw_pred_value=self.raw_pred_value,
            y_pos=self.y_pos
        )
        
        self.base_color = base_color
        
        # No need to draw anything if the alpha comoponent of the base color is 0.
        if base_color[3] == 0:
            return
        
        surface_size = None
        note_surface = None
        
        if NOTE_SPRITE_TYPE == 0:
            surface_size = (60, 60)
            note_surface = pygame.Surface(surface_size, flags=pygame.SRCALPHA)
            
            center = (surface_size[0] // 2, surface_size[1] // 2)
            
            # Shadow
            pygame.draw.circle(
                surface=note_surface,
                color=shadow_color,
                center=(center[0] - 2, center[1] + 2),
                radius=25
            )

            # Base
            pygame.draw.circle(
                surface=note_surface,
                color=base_color,
                center=center,
                radius=25
            )

            # Accent
            pygame.draw.circle(
                surface=note_surface,
                color=accent_color,
                center=(center[0] + 7, center[1] - 7),
                radius=7
            )
            
            surface.blit(note_surface, (self.x_pos - (surface_size[0] / 2), self.y_pos - (surface_size[1] / 2)))

        elif NOTE_SPRITE_TYPE == 1:
            surface_size = (128, 48)
            note_surface = pygame.Surface(surface_size, flags=pygame.SRCALPHA)
            
            
            # All rects relative to local surface.
            shadow_rect = pygame.Rect(4, 4, surface_size[0]-8, surface_size[1]-8)
            base_rect = pygame.Rect(0, 0, surface_size[0], surface_size[1])
            accent_rect = pygame.Rect(surface_size[0]//8, surface_size[1]//8, surface_size[0]//1.33, surface_size[1]//6)
            
            # Shadow
            pygame.draw.rect(
                note_surface,
                color=shadow_color,
                rect=shadow_rect,
                border_radius=4
            )
            
            # Base
            pygame.draw.rect(
                note_surface,
                color=base_color,
                rect=base_rect,
                border_radius=4
            )
            
            # Accent
            pygame.draw.rect(
                note_surface,
                color=accent_color,
                rect=accent_rect,
                border_radius=8
            )

            surface.blit(note_surface, (self.x_pos - (surface_size[0] // 2), self.y_pos - (surface_size[1] // 2)))
        

def get_note_colors(lane, is_placed_note, raw_pred_value, y_pos):
    def get_faded_alpha():
        # Smoothing formula: alpha(x) = 3x^2 - 2x^3
        alpha = int(
            ((3 * (raw_pred_value**2)) - (2 * (raw_pred_value**3))) * 255
        )
        
        # Percentage to calculate fade-in and fade-out factors.
        max_visible_distance_to_judgement = 300
        squared_positional_percentage_to_judgement = (y_pos**2) / ((JUDGEMENT_Y_POSITION - max_visible_distance_to_judgement)**2)
        
        # Fade-out.
        if not is_placed_note:                
            alpha_decay_factor = 1 - squared_positional_percentage_to_judgement
            
            alpha *= alpha_decay_factor
            alpha = max(0, alpha)
        # Fade-in
        else:
            alpha_growth_factor = 0.5 + squared_positional_percentage_to_judgement
            alpha_growth_factor = max(1, alpha_growth_factor)
            
            alpha *= alpha_growth_factor
            alpha = min(255, alpha)
        
        return alpha
    
    # Only show actually placed notes.
    if NOTE_DISPLAY_MODE == 0:
        alpha = int(is_placed_note) * 255
            
        base_color = NOTE_BASE_COLS[lane] + (alpha,)
        shadow_color = NOTE_SHADOW_COLS[lane] + (alpha,)
        accent_color = NOTE_ACCENT_COLS[lane] + (alpha,)
    
    # Show raw prediction values as note opacity.
    # Notes that are not "real" (i.e. not placed) fade out,
    # notes that are "real" (i.e. placed) fade in.
    elif NOTE_DISPLAY_MODE == 1:
        alpha = get_faded_alpha()
        
        base_color = NOTE_BASE_COLS[lane] + (alpha,)
        shadow_color = NOTE_SHADOW_COLS[lane] + (alpha,)
        accent_color = NOTE_ACCENT_COLS[lane] + (alpha,)
    
    # Show raw prediction values as R and B color-channel values.
    elif NOTE_DISPLAY_MODE == 2:
        alpha = int((raw_pred_value + 0.75) * 146)
        
        r = raw_pred_value * 255
        g = 0
        b = (1 - raw_pred_value) * 255
        
        base_color = (r, g, b, alpha)
        accent_color = (min(255, r + 125), 125, min(255, b + 125), alpha)
        shadow_color = (max(0, r - 125), 0, max(0, b - 125), alpha)
    
    # Show raw prediction values as R and B color-channel values
    # as well as note opacity.
    else:
        alpha = get_faded_alpha()
        
        r = raw_pred_value * 255
        g = 0
        b = (1 - raw_pred_value) * 255
        
        base_color = (r, g, b, alpha)
        accent_color = (min(255, r + 125), 125, min(255, b + 125), alpha)
        shadow_color = (max(0, r - 125), 0, max(0, b - 125), alpha)
    
    return base_color, shadow_color, accent_color
     

def get_notes_from_gblf(file_path : str) -> list:
    contents = None
    
    with open(file_path, "r") as f:
        contents = f.readlines()
    
    notes = []
    
    for line in contents:
        line_contents = line.strip().split("|")
        
        timing = int(line_contents[0])
        
        for lane_idx, lane in enumerate(line_contents[1:]):
            if lane.isspace():
                continue
            
            lane_info = lane.split(":")
            
            is_placed_note = int(lane_info[0])
            is_placed_note = bool(is_placed_note)
            
            raw_pred_value = float(lane_info[1])
        
            note = Note(
                lane=lane_idx,
                timing_ms=timing,
                raw_pred_value=raw_pred_value,
                is_placed_note=is_placed_note
            )
            
            notes.append(note)
    
    return notes


def process_event(event : pygame.event.Event) -> int:
    if event.type == QUIT:
        return -1
    
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            return -1
        
        # Reset keypress times.
        if event.key in KEY_LANE_MAP:
            last_pressed_times[KEY_LANE_MAP[event.key]] = 0
            keys_held[KEY_LANE_MAP[event.key]] = True
            return 1    
        
        # Toggle autoplay.
        if event.key == pygame.K_TAB:
            global USE_AUTOPLAY
            USE_AUTOPLAY = not USE_AUTOPLAY
            return 0
        
        # Toggle note display mode.
        if event.key == pygame.K_n:
            global NOTE_DISPLAY_MODE
            NOTE_DISPLAY_MODE = NOTE_DISPLAY_MODE + 1 if NOTE_DISPLAY_MODE < 3 else 0
            return 0
        
        # Toggle note sprite type.
        if event.key == pygame.K_m:
            global NOTE_SPRITE_TYPE
            NOTE_SPRITE_TYPE = NOTE_SPRITE_TYPE + 1 if NOTE_SPRITE_TYPE < 1 else 0
            return 0

        global SCROLL_SPEED
        
        # Change scrollspeed.
        if event.key == pygame.K_F3:
            SCROLL_SPEED -= 0.1
            SCROLL_SPEED = max(SCROLL_SPEED, 0.5)
            return 0
        
        if event.key == pygame.K_F4:
            SCROLL_SPEED += 0.1
            SCROLL_SPEED = min(SCROLL_SPEED, 3)
            return 0
        
        return 0
    
    # Reset keys-held values for highlight fade-out.
    if event.type == pygame.KEYUP:
        if event.key in KEY_LANE_MAP:
            keys_held[KEY_LANE_MAP[event.key]] = False
            return 0

        return 0


def draw_keypress_highlights(surface : pygame.Surface, lane_idx : int, fade_factor : float) -> None:
    rect_x = lane_idx * 128
    rect_y = JUDGEMENT_Y_POSITION
    width = 128
    height = SCREEN_HEIGHT - rect_y
    
    highlight_surface = pygame.Surface((width, height), flags=pygame.SRCALPHA).convert_alpha()
    
    alpha = int(255 * fade_factor)
    fade_color = (*last_pressed_colors[lane_idx][:3], alpha)
    
    highlight_surface.fill(fade_color)
    surface.blit(highlight_surface, (rect_x, rect_y))


def draw_judgement_line(surface : pygame.Surface) -> None:
    # Judgement line.
    pygame.draw.line(
        surface=surface,
        color=WHITE,
        width=5,
        start_pos=(0, JUDGEMENT_Y_POSITION),
        end_pos=(540, JUDGEMENT_Y_POSITION)
    )
        
    # Area below judgement line.
    pygame.draw.rect(
        surface=surface,
        color=BG_ACCENT_COL,
        rect=((0, JUDGEMENT_Y_POSITION, SCREEN_WIDTH, SCREEN_HEIGHT))
    )


def main():
    # -------- Pygame settings --------
    pygame.init()
    
    pygame.mixer.init()
    pygame.mixer.music.load(AUDIO_FILE_PATH)
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer_music.set_endevent(QUIT)
    
    sfx_hit = pygame.mixer.Sound(HIT_SFX_FILE_PATH)
    sfx_hit.set_volume(0.3)

    frame_clock = pygame.time.Clock()
    
    DISPLAY_SURFACE = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    pygame.display.set_caption(f"Beatmap Visualizer v{VISUALIZER_VERSION}")
    # ---------------------------------
    
    # -------- Other settings --------
    quit_game = False

    remaining_notes = get_notes_from_gblf(file_path=GENERATED_FILE_PATH)
    active_notes = []
    
    start_time_s = time.time()
    
    pygame.mixer_music.play()
    # ---------------------------------
    
    
    while not quit_game:
        for event in pygame.event.get():
            event_feedback = process_event(event=event)
            
            # Feedback = -1 -> Quit.
            if event_feedback == -1:
                pygame.quit()
                quit_game = True
                return

            # Feedback = 1 -> Play SFX.
            if event_feedback == 1:
                sfx_hit.play()
        
        DISPLAY_SURFACE.fill(color=BG_COL)
        
        current_time_s = time.time() - start_time_s
        current_time_ms = current_time_s * 1000
        
        delta_time = frame_clock.tick(FPS) / 1000
        
        for lane in range(4):
            if not keys_held[lane]:
                last_pressed_times[lane] += delta_time

        # Update all note positions.
        for note in remaining_notes:
            note.update(current_time_ms, )
        
        for note in active_notes:
            note.update(current_time_ms)
        
        # Get both the next notes as well as the oldest notes.
        note_idxs_remaining = len(remaining_notes)
        active_note_idxs = len(active_notes)
        
        upcoming_notes_idx = [ i for i in range(0, min(note_idxs_remaining, 4))]
        oldest_notes_idx = [ i for i in range(0, min(active_note_idxs, 4))]

        
        # Move possible upcoming notes into the active list.
        for note_idx in upcoming_notes_idx[::-1]:
            if remaining_notes[note_idx].y_pos >= -10:
                active_notes.append(remaining_notes[note_idx])
                remaining_notes.pop(note_idx)
        
        # Move played notes out of the active list.
        for note_idx in oldest_notes_idx[::-1]:
            if active_notes[note_idx].y_pos >= JUDGEMENT_Y_POSITION:
                # Update keypress highlighting for autoplay.
                if USE_AUTOPLAY:
                    lane_idx = active_notes[note_idx].lane
                    
                    if active_notes[note_idx].is_placed_note:
                        last_pressed_colors[lane_idx] = active_notes[note_idx].base_color
                        last_pressed_times[lane_idx] = 0
                        sfx_hit.play()
                
                # Remove the note from the active notes list.
                active_notes.pop(note_idx)
        
        
        # -------- Rendering --------
        # Draw active notes.
        for note in active_notes:
            note.draw(DISPLAY_SURFACE)
        
        # Draw judgement lines.
        draw_judgement_line(DISPLAY_SURFACE)
        
        # Draw keypress highlights.
        for lane_idx in range(4):
            time_since = last_pressed_times[lane_idx]
            
            if time_since < KEYPRESS_FADE_DURATION:
                fade_factor = 1.0 - (time_since / KEYPRESS_FADE_DURATION)
                draw_keypress_highlights(surface=DISPLAY_SURFACE, lane_idx=lane_idx, fade_factor=fade_factor)
        
        pygame.display.update()
        # ---------------------------


if __name__ == "__main__":
    main()
