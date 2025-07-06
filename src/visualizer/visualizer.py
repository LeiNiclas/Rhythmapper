import time
import pygame
from pygame.locals import *

GENERATED_FILE_PATH = "Z:\\Programs\\Python\\osumania-levelgen\\generated\\generated6.osu"
AUDIO_FILE_PATH = "Z:\\Programs\\Python\\osumania-levelgen\\data\\audio\\test_audio.mp3"
HIT_SFX_FILE_PATH = "Z:\\Programs\\Python\\osumania-levelgen\\src\\visualizer\\hit_sfx.mp3"

# The hit SFX is royalty free.
# Download: https://pixabay.com/sound-effects/electronic-closed-hat-11-stereo-100413/

VISUALIZER_VERSION = "1.0"
FPS = 60

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


class Note():
    def __init__(self, lane, timing_ms):
        self.lane = lane
        self.timing_ms = timing_ms
        self.x_pos = lane * 128 + 64
        self.y_pos = -1000
    
    def update(self, current_timing_ms):
        self.y_pos = current_timing_ms - self.timing_ms + 800

    def draw(self, surface):
        # Shadow
        pygame.draw.circle(
            surface=surface,
            color=NOTE_SHADOW_COLS[self.lane],
            center=(self.x_pos - 2, self.y_pos + 2),
            radius=20
        )
        
        # Based
        pygame.draw.circle(
            surface=surface,
            color=NOTE_BASE_COLS[self.lane],
            center=(self.x_pos, self.y_pos),
            radius=20
        )
        
        # Accent
        pygame.draw.circle(
            surface=surface,
            color=NOTE_ACCENT_COLS[self.lane],
            center=(self.x_pos + 5, self.y_pos - 5),
            radius=5
        )
        

def get_notes_from_generated(file_path : str):
    contents = None
    
    with open(file_path, "r") as f:
        contents = f.readlines()
    
    notes = []
    
    for line in contents:
        line_contents = line.split(",")
        
        lane_idx = (int(line_contents[0]) - 64) // 128
        timing = int(line_contents[2])
        
        note = Note(lane=lane_idx, timing_ms=timing)
        
        notes.append(note)
    
    return notes


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

    SCREEN_WIDTH = 540
    SCREEN_HEIGHT = 960
    # ---------------------------------
    
    quit_game = False
    
    DISPLAY_SURFACE = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    pygame.display.set_caption(f"Beatmap Visualizer v{VISUALIZER_VERSION}")

    remaining_notes = get_notes_from_generated(file_path=GENERATED_FILE_PATH)
    active_notes = []
    
    start_time_s = time.time()
    
    pygame.mixer_music.play()

    
    
    while not quit_game:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                quit_game = True
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    quit_game = True
                    return
        
        DISPLAY_SURFACE.fill(color=BG_COL)
        
        current_time_s = time.time() - start_time_s
        current_time_ms = current_time_s * 1000
        
        # Update all note positions
        for note in remaining_notes:
            note.update(current_time_ms)
        
        for note in active_notes:
            note.update(current_time_ms)
        
        note_idxs_remaining = len(remaining_notes)
        active_note_idxs = len(active_notes)
        
        upcoming_notes_idx = [ i for i in range(0, min(note_idxs_remaining, 4))]
        recent_notes_idx = [ i for i in range(0, min(active_note_idxs, 4))]

        # Move possible upcoming notes into the active list
        for note_idx in upcoming_notes_idx[::-1]:
            if remaining_notes[note_idx].y_pos >= -10:
                active_notes.append(remaining_notes[note_idx])
                remaining_notes.pop(note_idx)
        
        # Move played notes out of the active list
        for note_idx in recent_notes_idx[::-1]:
            if active_notes[note_idx].y_pos >= 800:
                sfx_hit.play()
                active_notes.pop(note_idx)
        
        # Draw active notes
        for note in active_notes:
            note.draw(DISPLAY_SURFACE)

        # Draw judgement line
        pygame.draw.line(
            surface=DISPLAY_SURFACE,
            color=WHITE,
            width=5,
            start_pos=(0, 800),
            end_pos=(540, 800)
        )
        
        # Fill area below judgement line
        pygame.draw.rect(
            surface=DISPLAY_SURFACE,
            color=BG_ACCENT_COL,
            rect=((0, 800, SCREEN_WIDTH, SCREEN_HEIGHT))
        )
        
        pygame.display.update()


if __name__ == "__main__":
    main()

