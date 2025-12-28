import pygame
import os
import ctypes
import random
from PIL import Image, ImageSequence
import webbrowser
import json
import requests
import time
import importlib.util
import sys
import subprocess
import platform

try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass

pygame.init()
pygame.mixer.quit()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

info = pygame.display.Info()
WIN_W, WIN_H = info.current_w, info.current_h
screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.FULLSCREEN)
pygame.display.set_caption("Five Nights at Freddy's 2")

base_path = os.path.dirname(os.path.abspath(__file__))
images_path = os.path.join(base_path, "images")
sounds_path = os.path.join(base_path, "sounds")

OFFICE_SCALE = 1.25
office_size = (int(WIN_W * OFFICE_SCALE), WIN_H)

os.makedirs(images_path, exist_ok=True)
os.makedirs(sounds_path, exist_ok=True)

font_clock = pygame.font.SysFont("OCR A Extended", 40)
font_dev = pygame.font.SysFont("Consolas", 18)
font_main = pygame.font.SysFont("Arial", 100, bold=True)
font_title = pygame.font.SysFont("Arial", 50, bold=True)
font_button = pygame.font.SysFont("Arial", 30, bold=True)
font_bug_report = pygame.font.SysFont("Arial", 20)
font_bug_input = pygame.font.SysFont("Arial", 18)
font_mods = pygame.font.SysFont("Arial", 24)
font_mods_warning = pygame.font.SysFont("Arial", 16, bold=True)
font_mods_tab = pygame.font.SysFont("Arial", 20, bold=True)

appdata_path = os.getenv('APPDATA') or os.path.expanduser('~')
if os.name == 'nt' and not os.getenv('APPDATA'):
    appdata_path = os.path.join(appdata_path, 'AppData', 'Roaming')

save_dir = os.path.join(appdata_path, 'FNAF2')
mods_dir = os.path.join(save_dir, 'Mods')

try:
    os.makedirs(mods_dir, exist_ok=True)
except:
    pass

save_file = os.path.join(save_dir, "save.json")

available_mods = []
installed_mod = None
active_mod = None
mods_scroll_offset = 0
current_mods_tab = "library"

def scan_mods():
    global available_mods
    available_mods = []
    if not os.path.exists(mods_dir):
        try:
            os.makedirs(mods_dir, exist_ok=True)
        except:
            pass
        return available_mods
    try:
        for filename in os.listdir(mods_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                available_mods.append({
                    'name': filename[:-3],
                    'filename': filename,
                    'path': os.path.join(mods_dir, filename),
                    'installed': False
                })
    except:
        pass
    return available_mods

def install_mod(mod_info):
    global installed_mod
    installed_mod = mod_info
    mod_info['installed'] = True

def uninstall_mod():
    global installed_mod, active_mod
    if installed_mod:
        installed_mod['installed'] = False
        installed_mod = None
    active_mod = None

def launch_mod(mod_info):
    global active_mod
    try:
        spec = importlib.util.spec_from_file_location(mod_info['name'], mod_info['path'])
        mod_module = importlib.util.module_from_spec(spec)
        sys.modules[mod_info['name']] = mod_module
        spec.loader.exec_module(mod_module)
        active_mod = mod_info
        if hasattr(mod_module, 'init_mod'):
            mod_module.init_mod()
        return True
    except:
        return False

def open_mods_folder():
    try:
        if not os.path.exists(mods_dir):
            os.makedirs(mods_dir, exist_ok=True)
        if platform.system() == 'Windows':
            os.startfile(mods_dir)
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', mods_dir])
        else:
            subprocess.Popen(['xdg-open', mods_dir])
    except:
        pass

def load_img(name, target_size=(WIN_W, WIN_H)):
    path = os.path.join(images_path, name)
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, target_size)
    except:
        surf = pygame.Surface(target_size, pygame.SRCALPHA)
        surf.fill((30, 30, 30))
        return surf

def load_gif_frames(filename, target_size=(WIN_W, WIN_H), make_transparent=False):
    path = os.path.join(images_path, filename)
    if not os.path.exists(path):
        return None
    try:
        pil_image = Image.open(path)
        frames = []
        for frame in ImageSequence.Iterator(pil_image):
            frame = frame.convert("RGBA")
            if make_transparent:
                datas = frame.getdata()
                newData = [(255, 255, 255, 0) if item[0] < 10 and item[1] < 10 and item[2] < 10 else item for item in datas]
                frame.putdata(newData)
            pygame_surface = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode).convert_alpha()
            frames.append((pygame.transform.scale(pygame_surface, target_size), frame.info.get('duration', 33)))
        return frames
    except:
        return None

def load_sound(filename):
    path = os.path.join(sounds_path, filename)
    if not os.path.exists(path):
        return None
    try:
        return pygame.mixer.Sound(path)
    except:
        return None

map_size = (WIN_W // 2, WIN_H)

imgs = {
    "main": load_img("office_main.png", office_size),
    "hall_clear": load_img("office_center_clear.png", office_size),
    "hall_foxy": load_img("WitheredFoxyStage.png", office_size),
    "vent_l_clear": load_img("FNaF_2_Office_Left_Vent_Light.png", office_size),
    "vent_l_chica": load_img("FNaF_2_Office_Left_Vent_Toy_Chica.png", office_size),
    "vent_r_clear": load_img("FNaF_2_Office_Right_Vent_Light.png", office_size),
    "vent_r_bonnie": load_img("FNaF_2_Office_Right_Vent_Toy_Bonnie.png", office_size),
    "mask": load_img("Mask.png"),
    "puppet_awake_light": load_img("PuppetAwakeLight.png"),
    "puppet_in_box_light": load_img("PuppetInBoxLight.png"),
    "puppet_box_no_light": load_img("PuppetBoxNoLight.png"),
    "map8": load_img("Cam8.png", map_size),
    "map9": load_img("cam9.png", map_size),
    "map11": load_img("Cam11.png", map_size),
    "stage_full": load_img("StageFull.png"),
    "stage_full_light": load_img("StageLightFull.png"),
    "stage_freddy_chica": load_img("StageFreddyChicka.png"),
    "stage_freddy_chica_light": load_img("StageFreddyChickaLight.png"),
    "stage_freddy_bonnie": load_img("StageFreddyBonnie.png"),
    "stage_freddy_bonnie_light": load_img("StageFreddyBonnieLight.png"),
    "stage_freddy": load_img("StageFreddy.png"),
    "stage_freddy_light": load_img("StageFreddyLight.png"),
    "stage_bonnie_freddy": load_img("ToyBonnieToyFreddyStage.png"),
    "stage_bonnie_freddy_light": load_img("ToyBonnieToyFreddyStageLight.png"),
    "cam8_view": load_img("Cam8View.png"),
    "menu": load_img("menuTest.png"),
    "toy_chica_face": load_img("ToyChikaFace.png", (150, 150)),
    "toy_chica_face2": load_img("ToyChickaFace2.png", (150, 150)),
    "toy_chica_face3": load_img("ToyChickaFace3.png", (150, 150)),
    "toy_bonnie_face": load_img("ToyBonnyFace.png", (150, 150)),
    "toy_bonnie_face2": load_img("BonnieFace2.png", (150, 150)),
    "toy_bonnie_face3": load_img("BonnieFace3.png", (150, 150)),
    "withered_foxy_face": load_img("WitheredFoxyFace.png", (150, 150)),
    "withered_foxy_face2": load_img("FoxyFace2.png", (150, 150)),
    "withered_foxy_face3": load_img("FoxyFace3.png", (150, 150)),
    "puppet_face": load_img("PuppetFace.png", (150, 150)),
    "main_hall_clear": load_img("MainHallClear.png"),
    "main_hall_toy_chica": load_img("MainHallToyChicka.png"),
    "main_hall_clear_light": load_img("MainHalLClearLight.png"),
    "main_hall_toy_chica_light": load_img("MainHallToyChickaLight.png"),
    "party_room2_toy_bonnie": load_img("PartyRoom2ToyBonnie.png"),
    "party_room2_toy_bonnie_light": load_img("PartyRoom2ToyBonnieLight.png"),
    "party_room2_clear": load_img("PartyRoom2Clear.png"),
    "party_room2_clear_light": load_img("PartyRoomClearLight.png"),
    "bb_face": load_img("BBFace.png", (150, 150)),
    "bb_face2": load_img("BBFace2.png", (150, 150)),
    "bb_face3": load_img("BBFace3.png", (150, 150)),
    "bb_face4": load_img("BBFace4.png", (150, 150)),
    "parts_service_lo_light": load_img("PartsServiceLoLight.png"),
    "parts_service_all_light": load_img("PartsServiceAllLight.png"),
    "parts_service_without_foxy": load_img("PartsServiceWithoutFoxy.png"),
    "game_area_bb": load_img("GameAreaBB.png"),
    "game_area_bb_light": load_img("GameAreBBLight.png"),
    "game_area_clear": load_img("GameAreaClear.png"),
    "game_area_clear_light": load_img("GameAreClearLight.png"),
    "left_vent": load_img("LeftVent.png"),
    "left_vent_bb_light": load_img("LeftVentBBLight.png"),
    "left_vent_toy_chicka": load_img("LeftVentToyChicka.png"),
    "office_bb_vent": load_img("OfficeBBVent.png", office_size),
    "office_bb": load_img("OfficeBB.png", office_size),
    "tg_icon": load_img("TGIcon.png", (50, 50)),
    "tiktok_icon": load_img("TikTokIcon.png", (50, 50)),
    "bug_icon": load_img("BugIcon.png", (50, 50)),
    "monitor_button": load_img("MonitorButton.png", (650, 40)),
    "mask_button": load_img("MaskButton.png", (650, 40)),
    "withered_freddy_face": load_img("WitheredFreddyFace.png", (150, 150)),
    "withered_chica_face": load_img("WitheredChicaFace.png", (150, 150)),
    "withered_bonny_face": load_img("WitheredBonnyFace.png", (150, 150)),
    "toy_freddy_face": load_img("ToyFreddyFace.png", (150, 150)),
    "toy_chica_hallway": load_img("ToyChicaHallway.png", office_size),
    "toy_freddy_hallway": load_img("ToyFreddyHalway.png", office_size),
    "toy_freddy_near": load_img("ToyFreddyNear.png", office_size),
    "withered_bonny_hallway": load_img("WitheredBonnyHallway.png", office_size),
    "withered_freddy_hallway": load_img("WitheredFreddyHallway.png", office_size),
    "wfoxy_wbonny": load_img("WFoxyWBonny.png", office_size),
    "game_area_bb_and_toy_freddy": load_img("GameAreaBBAndToyFreddy.png"),
    "game_area_toy_freddy_light": load_img("GameAreaToyFreddyLight.png"),
    "left_air_vent_clear_light": load_img("LeftAirVentClearLight.png"),
    "left_air_vent_withered_bonny": load_img("LeftAirVentWitheredBonny.png"),
    "withered_bonny_main_hall_light": load_img("WitheredBonnyMainHallLight.png"),
    "withered_freddy_mail_hall_light": load_img("WitheredFreddyMailHallLight.png"),
    "parts_service_without_foxy_and_bonny_light": load_img("PartsServiceWithoutFoxyAndBonnyLight.png"),
    "parts_service_withered_freddy": load_img("PartsServiceWitheredFreddy.png"),
    "parts_service_clear_light": load_img("PartsServiceClearLight.png"),
    "parts_service_withered_foxy_light": load_img("PartsServiceWitheredFoxyLight.png"),
    "shadow_freddy": load_img("ShadowFreddy.png"),
    "party_room1_clear": load_img("PartyRoom1Clear.png"),
    "party_room1_clear_light": load_img("PartyRoom1ClearLight.png"),
    "party_room1_withered_bonny_light": load_img("PartyRoom1WitheredBonnyLight.png"),
    "party_room1_toy_chica_light": load_img("PartyRoom1ToyChicaLight.png"),
    "party_room2_withered_chica": load_img("PartyRoom2WitheredChicka.png"),
    "party_room2_withered_chica_light": load_img("PartyRoom2WitheredChicaLight.png"),
    "party_room3_clear": load_img("PartyRoomClear.png"),
    "party_room3_clear_light": load_img("PartyRoom3ClearLight.png"),
    "party_room3_toy_bonny_light": load_img("PartyRoom3ToyBonnyLight.png"),
    "party_room3_withered_freddy": load_img("PartyRoom3WitheredFreddy.png"),
    "party_room4_withered_freddy_light": load_img("PartyRoom4WitheredFreddyLight.png"),
    "party_room4_clear": load_img("PartyRoom4Clear.png"),
    "party_room4_clear_light": load_img("PartyRoom4ClearLight.png"),
    "party_room4_toy_bonny": load_img("PartyRoom4ToyBonny.png"),
    "party_room4_toy_bonny_light": load_img("PartyRoom4ToyBonnyLight.png"),
    "party_room4_toy_chica_light": load_img("PartyRoom4ToyChicaLight.png"),
    "party_room4_withered_chica_light": load_img("PartyRoom4WitheredChicaLight.png"),
    "right_air_vent_clear": load_img("RightAirVentClear.png"),
    "right_air_vent_clear_light": load_img("RightAirVentClearLight.png"),
    "right_air_vent_toy_bonny_light": load_img("RightAirVentToyBonnyLight.png"),
    "right_air_vent_withered_chica_light": load_img("RightAirVentWitheredChicaLight.png"),
    "stage_clear": load_img("StageClear.png"),
}

imgs["mask"].set_colorkey((255, 255, 255))

jumpscares = {
    "Toy Bonnie": load_gif_frames("FNaF_2_Toy_Bonnie_Jumpscare.gif"),
    "Toy Chica": load_gif_frames("FNaF_2_Toy_Chica_Jumpscare.gif"),
    "Withered Foxy": load_gif_frames("FNaF_2_Withered_Foxy_Jumpscare.gif"),
    "Puppet": load_gif_frames("PuppetJumpScare.gif"),
    "Withered Freddy": load_gif_frames("WitheredFreddyJumpscare.gif"),
    "Withered Bonny": load_gif_frames("WitheredBonnyJumpscare.gif"),
    "Withered Chica": load_gif_frames("WitheredChicaJumpscare.gif"),
    "Toy Freddy": load_gif_frames("ToyBonnyJumpscare.gif"),
}

checks = {
    "Toy Bonnie_fail": load_gif_frames("ToyBonnieShake.gif", office_size),
    "Toy Chica_fail": load_gif_frames("ToyChicaShake.gif", office_size),
    "Withered Freddy_fail": load_gif_frames("WitheredFreddyCheck.png", office_size),
    "Withered Bonny_fail": load_gif_frames("WitheredBonnyCheck.png", office_size),
    "Withered Chica_fail": load_gif_frames("WitheredChicaCheck.png", office_size),
    "Toy Freddy_fail": load_gif_frames("ToyFreddyCheck.png", office_size),
}

puppet_dance_frames = load_gif_frames("PuppetDance.gif")
monitor_up_frames = load_gif_frames("MonitorUp.gif")
monitor_down_frames = load_gif_frames("MonitorDown.gif")
mask_equip_frames = load_gif_frames("MaskEquip.gif")
mask_unequip_frames = load_gif_frames("MaskUnequip.gif")
pomexi_frames = load_gif_frames("Pomexi.gif")
orange_alert_frames = load_gif_frames("Orange_Alert.gif", (100, 100))
red_alert_frames = load_gif_frames("Red_Alert.gif", (100, 100))
six_am_frames = load_gif_frames("6AM.gif")

jumpscare_sound = load_sound("JumpScare1.mp3")
foxy_line1_sound = load_sound("FoxyLine1.mp3")
vent_light_sound = load_sound("VentLight.mp3")
hall_sound = load_sound("Hall.mp3")
vent_crawl_sound = load_sound("VentCrawl.mp3")
mask_equip_sound = load_sound("MaskEquip.mp3")
mask_unequip_sound = load_sound("MaskUnequip.mp3")
mask_breathing_sound = load_sound("MaskBreathing.mp3")
music_box_song = load_sound("MusicBoxSong.mp3")
music_box_charge = load_sound("MusicBoxCharge.mp3")
check_sound = load_sound("CheckSound.mp3")
menu_music = load_sound("MenuTheme.mp3")
bb_hi = load_sound("BBHi.mp3")
bb_hello = load_sound("BBHello.mp3")
bb_laugh = load_sound("BBLaugh.mp3")
bb_laught = load_sound("BBLaught.mp3")
flash_error = load_sound("FlashLightError.mp3")
six_am_theme = load_sound("6AMTheme.mp3")

def play_sound(sound, loops=0):
    if sound:
        try:
            sound.play(loops)
        except:
            pass

def stop_sound(sound):
    if sound:
        try:
            sound.stop()
        except:
            pass

def stop_all_sounds():
    for sound in [jumpscare_sound, foxy_line1_sound, vent_light_sound, hall_sound, vent_crawl_sound, 
                  mask_equip_sound, mask_unequip_sound, mask_breathing_sound, music_box_song, 
                  music_box_charge, check_sound, menu_music, bb_hi, bb_hello, bb_laugh, bb_laught, 
                  flash_error, six_am_theme]:
        stop_sound(sound)

class SimpleBeatDetector:
    def __init__(self):
        self.shake_intensity = 0
        self.shake_decay = 0.85
        self.beat_pattern = [(0.0, 8), (0.5, 3), (1.0, 8), (1.5, 3), (2.0, 8), (2.5, 3), (3.0, 8), (3.5, 3),
                            (4.0, 10), (4.5, 4), (5.0, 10), (5.5, 4), (6.0, 10), (6.5, 4), (7.0, 10), (7.5, 4),
                            (8.0, 12), (8.25, 5), (8.5, 8), (8.75, 5), (9.0, 12), (9.25, 5), (9.5, 8), (9.75, 5)]
        self.pattern_duration = 10.0
        self.last_beat_time = -1

    def update(self, music_position_sec):
        self.shake_intensity *= self.shake_decay
        loop_position = music_position_sec % self.pattern_duration
        for beat_time, strength in self.beat_pattern:
            if abs(loop_position - beat_time) < 0.05:
                if abs(music_position_sec - self.last_beat_time) > 0.1:
                    self.shake_intensity = strength
                    self.last_beat_time = music_position_sec
                    break

    def get_shake_offset(self):
        if self.shake_intensity > 0.5:
            return (int(random.uniform(-self.shake_intensity, self.shake_intensity)),
                   int(random.uniform(-self.shake_intensity, self.shake_intensity)))
        return 0, 0

    def reset(self):
        self.shake_intensity = 0
        self.last_beat_time = -1

bug_report_text = ""
bug_report_category = ""
last_bug_report_time = 0
BUG_REPORT_COOLDOWN = 600
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1453443649680703639/Sae4YeT500kDNZoR_M7an7Fqle1Fo-Mx7lo_yvZWyIJo2RBQIaerxAkygXeTnYXcR9Ms"
bug_categories = ["Слабый (не мешающий игровому процессу)", "Средний (немного мешает игре)", "Сильный (очень мешает игре)"]

def send_bug_report_to_discord(text, category):
    try:
        data = {"content": f"**Новый баг!**\n\n**Текст:**\n{text}\n\n**Категория:** {category}"}
        response = requests.post(DISCORD_WEBHOOK, json=data, timeout=5)
        return response.status_code == 204
    except:
        return False

def can_submit_bug_report():
    return (time.time() - last_bug_report_time) >= BUG_REPORT_COOLDOWN

def get_time_until_next_report():
    time_remaining = max(0, BUG_REPORT_COOLDOWN - (time.time() - last_bug_report_time))
    return int(time_remaining // 60), int(time_remaining % 60)

class Animatronic:
    def __init__(self, name, start_pos, target_pos, ai_level, interval=5000):
        self.name = name
        self.start_pos = start_pos
        self.pos = start_pos
        self.target_name = target_pos
        self.ai_level = ai_level
        self.interval = interval
        self.last_think = pygame.time.get_ticks()
        self.think_interval = interval
        self.foxy_unwatched_time = 0
        self.foxy_watched_time = 0
        self.vent_arrival_time = 0
        self.status_msg = "Waiting"
        self.charge = 100.0 if name == "Puppet" else None
        self.last_discharge = pygame.time.get_ticks()
        self.discharge_time = 0

    def reset(self):
        self.pos = self.start_pos
        self.last_think = pygame.time.get_ticks()
        self.think_interval = self.interval
        self.foxy_unwatched_time = 0
        self.foxy_watched_time = 0
        self.vent_arrival_time = 0
        self.status_msg = "Waiting"
        self.last_discharge = pygame.time.get_ticks()
        self.discharge_time = 0
        if self.name == "Puppet":
            self.charge = 100.0

    def update(self, is_watching_hall, dt):
        now = pygame.time.get_ticks()
        if self.ai_level == 0:
            return

        if self.name == "Puppet":
            if self.pos == "Box" and self.charge > 0:
                if now - self.last_discharge >= 1000:
                    self.charge -= 6
                    self.last_discharge = now
                    if self.charge <= 0:
                        self.charge = 0
                        self.discharge_time = now
                        self.pos = "Awake"
            elif self.pos == "Awake" and now - self.discharge_time >= 3000:
                self.pos = "Office"
            return

        if self.name == "Withered Foxy":
            if self.pos == "Parts Service":
                if now - self.last_think > self.think_interval:
                    self.last_think = now
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == self.target_name for b in bots if b != self):
                            self.pos = self.target_name
                            self.vent_arrival_time = now
                            self.status_msg = "ENTERING HALL"
                        else:
                            self.status_msg = "Hall occupied"
                    else:
                        self.status_msg = "Idle in Parts Service"
            elif self.pos == self.target_name:
                if not is_watching_hall:
                    self.foxy_unwatched_time += dt
                    self.status_msg = f"Attack in: {7.5 - self.foxy_unwatched_time/1000:.1f}s"
                    if self.foxy_unwatched_time >= 7500:
                        self.pos = "Office"
                else:
                    self.foxy_watched_time += dt
                    self.foxy_unwatched_time = max(0, self.foxy_unwatched_time - dt)
                    self.status_msg = f"Blinding: {6.0 - self.foxy_watched_time/1000:.1f}s"
                    if self.foxy_watched_time >= 6000:
                        self.pos = self.start_pos
                        self.foxy_watched_time = 0
            return

        if now - self.last_think > self.think_interval:
            self.last_think = now

            if self.name == "Toy Chica":
                if self.pos == "Stage":
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Main Hall" for b in bots if b != self):
                            self.pos = "Main Hall"
                            self.status_msg = "MOVING TO MAIN HALL"
                        else:
                            self.status_msg = "Main Hall occupied"
                    else:
                        self.status_msg = "Idle on Stage"
                elif self.pos == "Main Hall":
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Left Air Vent" for b in bots if b != self):
                            self.pos = "Left Air Vent"
                            self.vent_arrival_time = now
                            play_sound(vent_crawl_sound)
                            self.status_msg = "ENTERING LEFT AIR VENT"
                        else:
                            self.status_msg = "Left Air Vent occupied"
                    else:
                        self.status_msg = "Idle in Main Hall"
                elif self.pos == "Left Air Vent":
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Office Vent Left" for b in bots if b != self):
                            self.pos = "Office Vent Left"
                            self.vent_arrival_time = now
                            play_sound(vent_crawl_sound)
                            self.status_msg = "ENTERING OFFICE VENT LEFT"
                        else:
                            self.status_msg = "Office Vent Left occupied"
                    else:
                        self.status_msg = "Idle in Left Air Vent"

            elif self.name == "Toy Bonnie":
                if self.pos == "Stage":
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Party Room2" for b in bots if b != self):
                            self.pos = "Party Room2"
                            self.status_msg = "MOVING TO PARTY ROOM2"
                        else:
                            self.status_msg = "Party Room2 occupied"
                    else:
                        self.status_msg = "Idle on Stage"
                elif self.pos == "Party Room2":
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Office Vent Right" for b in bots if b != self):
                            self.pos = "Office Vent Right"
                            self.vent_arrival_time = now
                            play_sound(vent_crawl_sound)
                            self.status_msg = "ENTERING OFFICE VENT RIGHT"
                        else:
                            self.status_msg = "Office Vent Right occupied"
                    else:
                        self.status_msg = "Idle in Party Room2"

            elif self.name == "Balloon Boy":
                if self.pos == "Left Air Vent":
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Office Vent Left" for b in bots if b != self):
                            self.pos = "Office Vent Left"
                            self.vent_arrival_time = now
                            self.status_msg = "ENTERING OFFICE VENT LEFT"
                        else:
                            self.status_msg = "Office Vent Left occupied"
                    else:
                        self.status_msg = "Idle in Left Air Vent"

            elif self.name == "Withered Freddy":
                if self.pos == "Parts Service":
                    if random.randint(1, 20) <= self.ai_level:
                        next_pos = random.choice(["Party Room3", "Main Hall"])
                        if not any(b.pos == next_pos for b in bots if b != self):
                            self.pos = next_pos
                            self.status_msg = f"MOVING TO {next_pos}"
                        else:
                            self.status_msg = f"{next_pos} occupied"
                    else:
                        self.status_msg = "Idle in Parts Service"
                elif self.pos in ["Party Room3", "Main Hall"]:
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Hall" for b in bots if b != self):
                            self.pos = "Hall"
                            self.status_msg = "ENTERING HALL"
                        else:
                            self.status_msg = "Hall occupied"
                    else:
                        self.status_msg = f"Idle in {self.pos}"
                elif self.pos == "Hall":
                    if random.randint(1, 20) <= self.ai_level:
                        self.pos = "Office"
                        self.status_msg = "ATTACKING!"

            elif self.name == "Withered Chica":
                if self.pos == "Parts Service":
                    if random.randint(1, 20) <= self.ai_level:
                        next_pos = random.choice(["Party Room2", "Party Room4"])
                        if not any(b.pos == next_pos for b in bots if b != self):
                            self.pos = next_pos
                            self.status_msg = f"MOVING TO {next_pos}"
                        else:
                            self.status_msg = f"{next_pos} occupied"
                    else:
                        self.status_msg = "Idle in Parts Service"
                elif self.pos in ["Party Room2", "Party Room4"]:
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Right Air Vent" for b in bots if b != self):
                            self.pos = "Right Air Vent"
                            self.vent_arrival_time = now
                            play_sound(vent_crawl_sound)
                            self.status_msg = "ENTERING RIGHT AIR VENT"
                        else:
                            self.status_msg = "Right Air Vent occupied"
                    else:
                        self.status_msg = f"Idle in {self.pos}"
                elif self.pos == "Right Air Vent":
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Office Vent Right" for b in bots if b != self):
                            self.pos = "Office Vent Right"
                            self.vent_arrival_time = now
                            play_sound(vent_crawl_sound)
                            self.status_msg = "ENTERING OFFICE VENT RIGHT"
                        else:
                            self.status_msg = "Office Vent Right occupied"
                    else:
                        self.status_msg = "Idle in Right Air Vent"

            elif self.name == "Withered Bonny":
                if self.pos == "Parts Service":
                    if random.randint(1, 20) <= self.ai_level:
                        next_pos = random.choice(["Party Room1", "Main Hall"])
                        if not any(b.pos == next_pos for b in bots if b != self):
                            self.pos = next_pos
                            self.status_msg = f"MOVING TO {next_pos}"
                        else:
                            self.status_msg = f"{next_pos} occupied"
                    else:
                        self.status_msg = "Idle in Parts Service"
                elif self.pos in ["Party Room1", "Main Hall"]:
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Left Air Vent" for b in bots if b != self):
                            self.pos = "Left Air Vent"
                            self.vent_arrival_time = now
                            play_sound(vent_crawl_sound)
                            self.status_msg = "ENTERING LEFT AIR VENT"
                        else:
                            self.status_msg = "Left Air Vent occupied"
                    else:
                        self.status_msg = f"Idle in {self.pos}"
                elif self.pos == "Left Air Vent":
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Office Vent Left" for b in bots if b != self):
                            self.pos = "Office Vent Left"
                            self.vent_arrival_time = now
                            play_sound(vent_crawl_sound)
                            self.status_msg = "ENTERING OFFICE VENT LEFT"
                        else:
                            self.status_msg = "Office Vent Left occupied"
                    else:
                        self.status_msg = "Idle in Left Air Vent"

            elif self.name == "Toy Freddy":
                if self.pos == "Stage":
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Game Area" for b in bots if b != self):
                            self.pos = "Game Area"
                            self.status_msg = "MOVING TO GAME AREA"
                        else:
                            self.status_msg = "Game Area occupied"
                    else:
                        self.status_msg = "Idle on Stage"
                elif self.pos == "Game Area":
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == "Hall" for b in bots if b != self):
                            self.pos = "Hall"
                            self.status_msg = "ENTERING HALL"
                        else:
                            self.status_msg = "Hall occupied"
                    else:
                        self.status_msg = "Idle in Game Area"
                elif self.pos == "Hall":
                    if random.randint(1, 20) <= self.ai_level:
                        self.pos = "Office"
                        self.status_msg = "ATTACKING!"

        if self.pos in ["Office Vent Left", "Office Vent Right"]:
            if now - self.vent_arrival_time < 3000:
                self.status_msg = f"Preparing: {3.0 - (now - self.vent_arrival_time)/1000:.1f}s"
            else:
                roll = random.randint(1, 20)
                if roll <= 5:
                    self.pos = "Office"
                    self.status_msg = "ATTACKING!"
                else:
                    self.status_msg = f"Vent Wait (Roll {roll}>5)"

bots = [
    Animatronic("Toy Bonnie", "Stage", "Office Vent Right", ai_level=2, interval=5000),
    Animatronic("Toy Chica", "Stage", "Main Hall", ai_level=1, interval=6000),
    Animatronic("Withered Foxy", "Parts Service", "Hall", ai_level=0, interval=8000),
    Animatronic("Puppet", "Box", "Office", ai_level=1, interval=10000),
    Animatronic("Balloon Boy", "Game Area", "Left Air Vent", ai_level=0, interval=5000),
    Animatronic("Withered Freddy", "Parts Service", "Hall", ai_level=0, interval=7000),
    Animatronic("Withered Chica", "Parts Service", "Right Air Vent", ai_level=0, interval=7000),
    Animatronic("Withered Bonny", "Parts Service", "Left Air Vent", ai_level=0, interval=7000),
    Animatronic("Toy Freddy", "Stage", "Hall", ai_level=0, interval=8000)
]

custom_levels = {bot.name: bot.ai_level for bot in bots}

nights_ai = {
    1: {"Toy Bonnie":2, "Toy Chica":1, "Withered Foxy":0, "Puppet":2, "Balloon Boy":0, 
        "Withered Freddy":0, "Withered Chica":0, "Withered Bonny":0, "Toy Freddy":0},
    2: {"Toy Bonnie":3, "Toy Chica":3, "Withered Foxy":2, "Puppet":3, "Balloon Boy":3,
        "Withered Freddy":2, "Withered Chica":2, "Withered Bonny":2, "Toy Freddy":1},
    3: {"Toy Bonnie":6, "Toy Chica":4, "Withered Foxy":4, "Puppet":6, "Balloon Boy":5,
        "Withered Freddy":4, "Withered Chica":4, "Withered Bonny":3, "Toy Freddy":3},
    4: {"Toy Bonnie":8, "Toy Chica":7, "Withered Foxy":7, "Puppet":8, "Balloon Boy":7,
        "Withered Freddy":6, "Withered Chica":6, "Withered Bonny":5, "Toy Freddy":5},
    5: {"Toy Bonnie":15, "Toy Chica":14, "Withered Foxy":8, "Puppet":11, "Balloon Boy":7,
        "Withered Freddy":10, "Withered Chica":10, "Withered Bonny":9, "Toy Freddy":8},
    6: {"Toy Bonnie":15, "Toy Chica":14, "Withered Foxy":11, "Puppet":11, "Balloon Boy":11,
        "Withered Freddy":12, "Withered Chica":12, "Withered Bonny":11, "Toy Freddy":10},
}

game_time_ms = 0
hour = 12
HOUR_DURATION = 60000
office_x = 0
mask_on = False
mask_on_start = 0
is_breathing_playing = False
dev_mode_active = False
running = True
game_state = "MENU"
active_js_bot = None
checking_bot = None
check_type = ""
check_start = 0
success_start = 0
js_frame_index = 0
js_frame_index_alert = 0
is_vent_light_playing = False
is_hall_sound_playing = False
camera_mode = False
light_on = False
charging = False
last_charge = 0
charge_button_rect = pygame.Rect(WIN_W // 2 - 50, WIN_H - 100, 100, 50)
music_box_playing = False
current_cam = '11'
clock = pygame.time.Clock()
is_custom_night = False
bb_sound_count = 0
bb_move_time = 0
bb_mask_start = 0
bb_in_office = False
bb_laugh_playing = False
bb_last_speak_time = 0
bb_idle_start = 0
bb_return_idle = False
flash_error_playing = False
monitor_animation_start = 0
pomexi_frame = 0
monitor_button_hovered = False
mask_button_hovered = False
current_night = 1
is_custom_unlocked = False
mask_animation_state = None
mask_animation_start = 0
mask_animation_frame = 0
six_am_animation_start = 0
six_am_frame_index = 0
six_am_sound_playing = False
shadow_freddy_shown = False
shadow_freddy_trigger_time = 0

def load_save():
    global current_night, is_custom_unlocked, last_bug_report_time, installed_mod
    if os.path.exists(save_file):
        try:
            with open(save_file, 'r') as f:
                data = json.load(f)
                current_night = data.get('current_night', 1)
                is_custom_unlocked = data.get('custom_unlocked', False)
                last_bug_report_time = data.get('last_bug_report_time', 0)
                saved_mod = data.get('installed_mod', None)
                if saved_mod and os.path.exists(saved_mod.get('path', '')):
                    installed_mod = saved_mod
        except:
            current_night = 1
            is_custom_unlocked = False
            last_bug_report_time = 0
            installed_mod = None
    else:
        current_night = 1
        is_custom_unlocked = False
        last_bug_report_time = 0
        installed_mod = None

def save_progress():
    data = {
        'current_night': current_night,
        'custom_unlocked': is_custom_unlocked,
        'last_bug_report_time': last_bug_report_time,
        'installed_mod': installed_mod
    }
    try:
        os.makedirs(save_dir, exist_ok=True)
        with open(save_file, 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass

load_save()
save_progress()
scan_mods()

puppet = next(b for b in bots if b.name == "Puppet")
foxy = next(b for b in bots if b.name == "Withered Foxy")

map_pos = (WIN_W // 2, 0)

cam_buttons = {
    str(i): {'rect': pygame.Rect(50 + (i-1)%3*120, 100 + (i-1)//3*100, 100, 60), 'label': f'CAM {i:02d}'}
    for i in range(1, 13)
}

custom_pos_y = 200
custom_characters = [b.name for b in bots]
custom_rects_left = {}
custom_rects_right = {}
custom_level_rects = {}

char_positions = [(WIN_W//4 + (i%3)*(WIN_W//4), custom_pos_y + (i//3)*200) for i in range(9)]

for i, name in enumerate(custom_characters):
    x, y = char_positions[i]
    custom_rects_left[name] = pygame.Rect(x - 80, y + 100, 40, 40)
    custom_rects_right[name] = pygame.Rect(x + 40, y + 100, 40, 40)
    custom_level_rects[name] = pygame.Rect(x - 40, y + 100, 80, 40)

rect_start_custom = pygame.Rect(WIN_W//2 - 100, custom_pos_y + 600, 200, 50)

foxy_sequence_start = 0
black_screen_alpha = 0
foxy_sound_played = False
foxy_sound_end = 0

rect_bug = pygame.Rect(WIN_W - 170, 10, 50, 50)
rect_tg = pygame.Rect(WIN_W - 110, 10, 50, 50)
rect_tiktok = pygame.Rect(WIN_W - 50, 10, 50, 50)

monitor_button_rect = pygame.Rect(WIN_W // 2 + 50, WIN_H - 60, 650, 40)
mask_button_rect = pygame.Rect(WIN_W // 2 - 700, WIN_H - 60, 650, 40)

menu_buttons = [
    {"text": "ИГРАТЬ", "action": "new_game"},
    {"text": "ПРОДОЛЖИТЬ", "action": "continue"},
    {"text": "КАСТОМ НАЙТ", "action": "custom"},
    {"text": "МОДЫ", "action": "mods"}
]

menu_font = pygame.font.SysFont("Arial", 60, bold=True)
menu_button_y_start = WIN_H // 2 - 100
menu_button_spacing = 80
menu_selected = -1
menu_button_rects = []

for i, btn in enumerate(menu_buttons):
    text_surf = menu_font.render(btn["text"], True, (255, 255, 255))
    y = menu_button_y_start + (i if i <= 2 else 3) * menu_button_spacing
    menu_button_rects.append(pygame.Rect(200, y, text_surf.get_width(), text_surf.get_height()))

beat_detector = SimpleBeatDetector()
menu_music_start_time = 0

def set_ai_levels():
    if is_custom_night:
        for bot in bots:
            bot.ai_level = custom_levels.get(bot.name, 0)
    else:
        ai_dict = nights_ai.get(current_night, nights_ai[1])
        for bot in bots:
            bot.ai_level = ai_dict.get(bot.name, 0)
        if current_night == 1:
            foxy.ai_level = 0

def reset_game():
    global game_time_ms, hour, office_x, mask_on, mask_on_start, is_breathing_playing, active_js_bot, checking_bot, check_type, check_start, success_start, js_frame_index, js_frame_index_alert, is_vent_light_playing, is_hall_sound_playing, camera_mode, light_on, charging, last_charge, music_box_playing, current_cam, foxy_sequence_start, black_screen_alpha, foxy_sound_played, foxy_sound_end, bb_sound_count, bb_move_time, bb_mask_start, bb_in_office, bb_laugh_playing, bb_last_speak_time, bb_idle_start, bb_return_idle, flash_error_playing, monitor_animation_start, pomexi_frame, monitor_button_hovered, mask_button_hovered, mask_animation_state, mask_animation_start, mask_animation_frame, shadow_freddy_shown, shadow_freddy_trigger_time

    for bot in bots:
        bot.reset()

    set_ai_levels()

    game_time_ms = hour = office_x = mask_on_start = check_start = success_start = js_frame_index = js_frame_index_alert = foxy_sequence_start = black_screen_alpha = foxy_sound_end = bb_sound_count = bb_move_time = bb_mask_start = bb_idle_start = monitor_animation_start = pomexi_frame = mask_animation_start = mask_animation_frame = shadow_freddy_trigger_time = 0
    hour = 12
    last_charge = bb_last_speak_time = bb_idle_start = pygame.time.get_ticks()
    mask_on = is_breathing_playing = camera_mode = light_on = charging = music_box_playing = foxy_sound_played = bb_in_office = bb_laugh_playing = bb_return_idle = flash_error_playing = monitor_button_hovered = mask_button_hovered = shadow_freddy_shown = False
    active_js_bot = checking_bot = check_type = mask_animation_state = None
    is_vent_light_playing = is_hall_sound_playing = False
    current_cam = '11'

play_sound(menu_music, -1)
menu_music_start_time = pygame.time.get_ticks()

while running:
    dt = clock.tick(30)
    js_frame_index_alert += 1
    pomexi_frame += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "BUG_REPORT" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                bug_report_text = bug_report_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                game_state = "MENU"
                bug_report_text = bug_report_category = ""
            elif event.key not in [pygame.K_RETURN, pygame.K_TAB] and len(bug_report_text) < 500:
                bug_report_text += event.unicode

        if event.type == pygame.KEYDOWN:
            if game_state in ["PLAY", "CHECKING"]:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LCTRL] and keys[pygame.K_h] and keys[pygame.K_g] and keys[pygame.K_f]:
                    dev_mode_active = not dev_mode_active

                if bb_in_office and event.key in [pygame.K_x, pygame.K_c, pygame.K_z] and not flash_error_playing:
                    play_sound(flash_error)
                    flash_error_playing = True

            if game_state == "MENU":
                if event.key == pygame.K_UP:
                    menu_selected = max(0, (menu_selected - 1) if menu_selected != -1 else 0)
                    if menu_selected == 2 and not is_custom_unlocked:
                        menu_selected = max(0, menu_selected - 1)
                elif event.key == pygame.K_DOWN:
                    menu_selected = min(3, (menu_selected + 1) if menu_selected != -1 else 0)
                    if menu_selected == 2 and not is_custom_unlocked:
                        menu_selected = 3
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE] and menu_selected != -1:
                    if menu_selected == 2 and not is_custom_unlocked:
                        continue

                    action = menu_buttons[menu_selected]["action"]
                    if action == "new_game":
                        current_night = 1
                        save_progress()
                        is_custom_night = False
                        reset_game()
                        game_state = "PLAY"
                        stop_sound(menu_music)
                        beat_detector.reset()
                    elif action == "continue":
                        is_custom_night = False
                        reset_game()
                        game_state = "PLAY"
                        stop_sound(menu_music)
                        beat_detector.reset()
                    elif action == "custom":
                        game_state = "CUSTOM"
                    elif action == "mods":
                        scan_mods()
                        game_state = "MODS"

            if game_state == "SIX_AM_ANIMATION":
                stop_sound(six_am_theme)
                if not is_custom_night:
                    current_night = min(6, current_night + 1)
                    if current_night == 6:
                        is_custom_unlocked = True
                    save_progress()
                game_state = "MENU"
                play_sound(menu_music, -1)
                menu_music_start_time = pygame.time.get_ticks()
                beat_detector.reset()

            if game_state == "GAMEOVER":
                game_state = "MENU"
                play_sound(menu_music, -1)
                menu_music_start_time = pygame.time.get_ticks()
                beat_detector.reset()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            if game_state in ["PLAY", "CHECKING"]:
                if camera_mode:
                    for cam_id, cam_data in cam_buttons.items():
                        adjusted_rect = cam_data['rect'].copy()
                        adjusted_rect.move_ip(map_pos)
                        if adjusted_rect.collidepoint(mouse_pos):
                            current_cam = cam_id
                            break

                    if current_cam == '11' and puppet.charge > 0 and puppet.pos == "Box":
                        if charge_button_rect.collidepoint(mouse_pos):
                            charging = True
                            last_charge = pygame.time.get_ticks()
                            play_sound(music_box_charge, -1)

            if game_state == "BUG_REPORT":
                close_btn = pygame.Rect(WIN_W // 2 + 350, WIN_H // 2 - 250, 40, 40)
                if close_btn.collidepoint(mouse_pos):
                    game_state = "MENU"
                    bug_report_text = bug_report_category = ""

                for i, cat in enumerate(bug_categories):
                    if pygame.Rect(WIN_W // 2 - 300, WIN_H // 2 - 50 + i * 60, 30, 30).collidepoint(mouse_pos):
                        bug_report_category = cat

                submit_btn = pygame.Rect(WIN_W // 2 - 100, WIN_H // 2 + 200, 200, 50)
                if submit_btn.collidepoint(mouse_pos) and bug_report_text.strip() and bug_report_category:
                    if can_submit_bug_report():
                        if send_bug_report_to_discord(bug_report_text, bug_report_category):
                            last_bug_report_time = time.time()
                            save_progress()
                            bug_report_text = bug_report_category = ""
                            game_state = "MENU"

            if game_state == "MODS":
                window_x, window_y = WIN_W // 2 - 400, WIN_H // 2 - 300
                panel_width = 150

                tab_buttons_data = [
                    {"text": "Популярное", "id": "popular", "y": window_y + 80},
                    {"text": "Моды игры", "id": "developer", "y": window_y + 140},
                    {"text": "Библиотека", "id": "library", "y": window_y + 200}
                ]

                for tab in tab_buttons_data:
                    if pygame.Rect(window_x + 15, tab["y"], panel_width - 10, 50).collidepoint(mouse_pos):
                        current_mods_tab = tab["id"]
                        break

                if pygame.Rect(WIN_W // 2 + 350, WIN_H // 2 - 300, 40, 40).collidepoint(mouse_pos):
                    game_state = "MENU"

                if pygame.Rect(WIN_W // 2 - 100, WIN_H // 2 + 230, 200, 50).collidepoint(mouse_pos):
                    open_mods_folder()

                for i, mod in enumerate(available_mods):
                    mod_y = WIN_H // 2 - 250 + 50 + i * 80
                    is_installed = installed_mod and installed_mod['name'] == mod['name']

                    if is_installed:
                        if pygame.Rect(WIN_W // 2 + 100, mod_y + 10, 150, 40).collidepoint(mouse_pos):
                            launch_mod(mod)
                        if pygame.Rect(WIN_W // 2 + 260, mod_y + 10, 80, 40).collidepoint(mouse_pos):
                            uninstall_mod()
                            save_progress()
                    else:
                        if pygame.Rect(WIN_W // 2 + 100, mod_y + 10, 150, 40).collidepoint(mouse_pos):
                            if installed_mod:
                                uninstall_mod()
                            install_mod(mod)
                            save_progress()

            if game_state == "MENU":
                if rect_bug.collidepoint(mouse_pos):
                    game_state = "BUG_REPORT"
                    bug_report_text = bug_report_category = ""

                for i, rect in enumerate(menu_button_rects):
                    if i == 2 and not is_custom_unlocked:
                        continue
                    if rect.collidepoint(mouse_pos):
                        action = menu_buttons[i]["action"]
                        if action == "new_game":
                            current_night = 1
                            save_progress()
                            is_custom_night = False
                            reset_game()
                            game_state = "PLAY"
                            stop_sound(menu_music)
                            beat_detector.reset()
                        elif action == "continue":
                            is_custom_night = False
                            reset_game()
                            game_state = "PLAY"
                            stop_sound(menu_music)
                            beat_detector.reset()
                        elif action == "custom":
                            game_state = "CUSTOM"
                        elif action == "mods":
                            scan_mods()
                            game_state = "MODS"

                if rect_tg.collidepoint(mouse_pos):
                    webbrowser.open("https://t.me/sh4destudio")
                if rect_tiktok.collidepoint(mouse_pos):
                    webbrowser.open("https://www.tiktok.com/@sh4de_o")

            if game_state == "CUSTOM":
                for name in custom_characters:
                    if custom_rects_left[name].collidepoint(mouse_pos):
                        custom_levels[name] = max(0, custom_levels[name] - 1)
                    if custom_rects_right[name].collidepoint(mouse_pos):
                        custom_levels[name] = min(20, custom_levels[name] + 1)

                if rect_start_custom.collidepoint(mouse_pos):
                    is_custom_night = True
                    for bot in bots:
                        bot.ai_level = custom_levels.get(bot.name, 0)
                    reset_game()
                    game_state = "PLAY"
                    stop_sound(menu_music)
                    beat_detector.reset()

            if game_state == "SIX_AM_ANIMATION":
                stop_sound(six_am_theme)
                if not is_custom_night:
                    current_night = min(6, current_night + 1)
                    if current_night == 6:
                        is_custom_unlocked = True
                    save_progress()
                game_state = "MENU"
                play_sound(menu_music, -1)
                menu_music_start_time = pygame.time.get_ticks()
                beat_detector.reset()

            if game_state == "GAMEOVER":
                game_state = "MENU"
                play_sound(menu_music, -1)
                menu_music_start_time = pygame.time.get_ticks()
                beat_detector.reset()

        if event.type == pygame.MOUSEBUTTONUP:
            if game_state in ["PLAY", "CHECKING"] and charging:
                charging = False
                stop_sound(music_box_charge)

        if event.type == pygame.MOUSEMOTION and game_state == "MENU":
            mouse_pos = pygame.mouse.get_pos()
            menu_selected = -1
            for i, rect in enumerate(menu_button_rects):
                if i == 2 and not is_custom_unlocked:
                    continue
                if rect.collidepoint(mouse_pos):
                    menu_selected = i
                    break

    if game_state in ["PLAY", "CHECKING"]:
        mouse_pos = pygame.mouse.get_pos()

        current_monitor_hover = monitor_button_rect.collidepoint(mouse_pos)
        if current_monitor_hover and not monitor_button_hovered:
            if charging:
                charging = False
                stop_sound(music_box_charge)

            if not camera_mode and mask_animation_state not in ["equipping", "equipped"]:
                game_state = "MONITOR_OPENING"
                monitor_animation_start = pygame.time.get_ticks()
            elif camera_mode:
                game_state = "MONITOR_CLOSING"
                monitor_animation_start = pygame.time.get_ticks()
                if music_box_playing:
                    stop_sound(music_box_song)
                music_box_playing = False
        monitor_button_hovered = current_monitor_hover

        current_mask_hover = mask_button_rect.collidepoint(mouse_pos)
        if current_mask_hover and not mask_button_hovered:
            if mask_animation_state is None and not camera_mode:
                mask_animation_state = "equipping"
                mask_animation_start = pygame.time.get_ticks()
                mask_animation_frame = 0
                play_sound(mask_equip_sound)
            elif mask_animation_state == "equipped":
                mask_animation_state = "unequipping"
                mask_animation_start = pygame.time.get_ticks()
                mask_animation_frame = 0
                play_sound(mask_unequip_sound)
                if is_breathing_playing:
                    stop_sound(mask_breathing_sound)
                    is_breathing_playing = False
        mask_button_hovered = current_mask_hover

    if mask_animation_state == "equipping" and mask_equip_frames:
        now = pygame.time.get_ticks()
        elapsed = now - mask_animation_start
        cum_time = 0
        finished = True

        for i, (surf, dur) in enumerate(mask_equip_frames):
            if elapsed < cum_time + dur:
                mask_animation_frame = i
                finished = False
                break
            cum_time += dur

        if finished:
            mask_animation_state = "equipped"
            mask_on = True
            mask_on_start = pygame.time.get_ticks()

    elif mask_animation_state == "unequipping" and mask_unequip_frames:
        now = pygame.time.get_ticks()
        elapsed = now - mask_animation_start
        cum_time = 0
        finished = True

        for i, (surf, dur) in enumerate(mask_unequip_frames):
            if elapsed < cum_time + dur:
                mask_animation_frame = i
                finished = False
                break
            cum_time += dur

        if finished:
            mask_animation_state = None
            mask_on = False

    if game_state in ["PLAY", "CHECKING"]:
        game_time_ms += dt
        if game_time_ms >= HOUR_DURATION:
            game_time_ms = 0
            hour = 1 if hour == 12 else hour + 1
            if not is_custom_night and hour == 3 and current_night == 1:
                foxy.ai_level = 1
            if hour == 6:
                for bot in bots:
                    bot.ai_level = 0
                stop_all_sounds()
                is_breathing_playing = is_vent_light_playing = is_hall_sound_playing = music_box_playing = charging = bb_laugh_playing = flash_error_playing = False
                game_state = "SIX_AM_ANIMATION"
                six_am_animation_start = pygame.time.get_ticks()
                six_am_frame_index = 0
                six_am_sound_playing = False

        keys = pygame.key.get_pressed()
        show_hall = keys[pygame.K_z] and mask_animation_state not in ["equipping", "equipped"] and not camera_mode and not bb_in_office
        show_vent_l = keys[pygame.K_x] and mask_animation_state not in ["equipping", "equipped"] and not camera_mode and not bb_in_office
        show_vent_r = keys[pygame.K_c] and mask_animation_state not in ["equipping", "equipped"] and not camera_mode and not bb_in_office
        light_on = keys[pygame.K_LCTRL] and camera_mode

        for bot in bots:
            bot.update(show_hall, dt)

        if camera_mode and current_cam == '11' and puppet.charge > 0:
            if not music_box_playing:
                play_sound(music_box_song, -1)
                music_box_playing = True
        elif music_box_playing:
            stop_sound(music_box_song)
            music_box_playing = False

        now = pygame.time.get_ticks()
        bb_bot = next((b for b in bots if b.name == "Balloon Boy"), None)

        if bb_bot and bb_bot.ai_level > 2 and bb_bot.pos == "Game Area":
            if now - bb_idle_start >= 15000:
                interval = 12000 if bb_bot.ai_level <= 6 else (8000 if bb_bot.ai_level <= 12 else random.choice([5000, 6000, 7000, 7500]))

                if now - bb_last_speak_time >= interval:
                    bb_last_speak_time = now
                    play_sound(random.choice([bb_hi, bb_hello]))
                    bb_sound_count += 1
                    if bb_sound_count == 4:
                        bb_move_time = now + 1000

        if bb_bot and bb_bot.pos == "Game Area" and bb_move_time > 0 and now >= bb_move_time:
            if not any(b.pos == "Left Air Vent" for b in bots if b != bb_bot):
                bb_bot.pos = "Left Air Vent"
                bb_sound_count = bb_move_time = 0
                bb_bot.status_msg = "MOVING TO LEFT AIR VENT"

        if bb_bot and bb_bot.pos == "Office Vent Left":
            if mask_on:
                if bb_mask_start == 0:
                    bb_mask_start = now
                elif now - bb_mask_start >= 5000:
                    bb_bot.pos = "Game Area"
                    bb_mask_start = 0
                    bb_bot.status_msg = "RETURNING TO GAME AREA"
                    bb_idle_start = now
                    bb_return_idle = True
            else:
                bb_mask_start = 0

            if now - bb_bot.vent_arrival_time >= 10000:
                bb_bot.pos = "Office"
                bb_in_office = True
                bb_bot.status_msg = "IN OFFICE"

        if bb_in_office and not bb_laugh_playing:
            play_sound(bb_laught, -1)
            bb_laugh_playing = True
        elif not bb_in_office and bb_laugh_playing:
            stop_sound(bb_laught)
            bb_laugh_playing = False

        if flash_error and flash_error.get_num_channels() == 0:
            flash_error_playing = False

        if game_state == "PLAY":
            for bot in bots:
                if bot.pos == "Office":
                    if bot.name in ["Puppet", "Withered Foxy"]:
                        if camera_mode:
                            camera_mode = False
                            if music_box_playing:
                                stop_sound(music_box_song)
                            music_box_playing = False
                        active_js_bot = bot.name
                        game_state = "JUMPSCARE"
                        js_frame_index = 0
                        stop_all_sounds()
                        play_sound(jumpscare_sound)
                    elif bot.name != "Balloon Boy":
                        if camera_mode:
                            camera_mode = False
                            if music_box_playing:
                                stop_sound(music_box_song)
                            music_box_playing = False
                            active_js_bot = bot.name
                            game_state = "JUMPSCARE"
                            js_frame_index = 0
                            stop_all_sounds()
                            play_sound(jumpscare_sound)
                        else:
                            checking_bot = bot
                            check_start = pygame.time.get_ticks()
                            check_type = "fail"
                            game_state = "CHECKING"
                            js_frame_index = 0
                            bot.status_msg = "Checking office..."
                            play_sound(check_sound, -1)

        if (show_vent_l or show_vent_r) and not is_vent_light_playing:
            play_sound(vent_light_sound, -1)
            is_vent_light_playing = True
        elif not (show_vent_l or show_vent_r) and is_vent_light_playing:
            stop_sound(vent_light_sound)
            is_vent_light_playing = False

        foxy_bot = next((b for b in bots if b.name == "Withered Foxy"), None)
        if foxy_bot:
            if foxy_bot.pos == "Hall" and not is_hall_sound_playing:
                play_sound(hall_sound, -1)
                is_hall_sound_playing = True
            elif foxy_bot.pos != "Hall" and is_hall_sound_playing:
                stop_sound(hall_sound)
                is_hall_sound_playing = False

        if mask_on and mask_animation_state == "equipped":
            if pygame.time.get_ticks() - mask_on_start >= 2000 and not is_breathing_playing:
                play_sound(mask_breathing_sound, -1)
                is_breathing_playing = True

        if charging and camera_mode and current_cam == '11' and puppet.charge > 0 and puppet.pos == "Box":
            now = pygame.time.get_ticks()
            if music_box_charge:
                charge_time = music_box_charge.get_length() * 1000
                if now - last_charge >= charge_time:
                    puppet.charge = min(100, puppet.charge + 20)
                    last_charge = now

        screen.fill((0, 0, 0))

        if camera_mode:
            current_img = None
            if current_cam == '11':
                if light_on:
                    if puppet.charge > 0 and puppet.pos == "Box":
                        current_img = imgs["puppet_in_box_light"]
                    else:
                        if random.random() < 0.08:
                            game_state = "PUPPET_DANCE"
                            js_frame_index = 0
                            continue
                        else:
                            current_img = imgs["puppet_awake_light"]
                else:
                    current_img = imgs["puppet_box_no_light"]

                screen.blit(current_img, (0, 0))

                if puppet.charge > 0 and puppet.pos == "Box":
                    pygame.draw.rect(screen, (255, 255, 255), charge_button_rect)
                    screen.blit(font_dev.render("Charge", True, (0, 0, 0)), (charge_button_rect.x + 10, charge_button_rect.y + 10))

                    charge_circle_center = (charge_button_rect.x - 100, charge_button_rect.y + 25)
                    radius = 20
                    pygame.draw.circle(screen, (0, 0, 0), charge_circle_center, radius, 2)
                    angle = 360 * (puppet.charge / 100)
                    rect = (charge_circle_center[0] - radius, charge_circle_center[1] - radius, radius * 2, radius * 2)
                    pygame.draw.arc(screen, (0, 255, 0), rect, 0, angle * (3.14159 / 180), 2)

            elif current_cam == '9':
                toy_bonnie = next(b for b in bots if b.name == "Toy Bonnie")
                toy_chica = next(b for b in bots if b.name == "Toy Chica")

                stages = {
                    (True, True): ("stage_full_light" if light_on else "stage_full"),
                    (False, True): ("stage_freddy_chica_light" if light_on else "stage_freddy_chica"),
                    (True, False): ("stage_bonnie_freddy_light" if light_on else "stage_bonnie_freddy"),
                    (False, False): ("stage_freddy_light" if light_on else "stage_freddy")
                }
                current_img = imgs[stages[(toy_bonnie.pos == "Stage", toy_chica.pos == "Stage")]]
                screen.blit(current_img, (0, 0))

            elif current_cam == '4':
                toy_chica = next(b for b in bots if b.name == "Toy Chica")
                is_chica = toy_chica.pos == "Main Hall"
                img_key = ("main_hall_toy_chica_light" if is_chica else "main_hall_clear_light") if light_on else ("main_hall_toy_chica" if is_chica else "main_hall_clear")
                screen.blit(imgs[img_key], (0, 0))

            elif current_cam == '7':
                foxy_there = foxy_bot.pos == "Parts Service" if foxy_bot else False
                if light_on:
                    current_img = imgs["parts_service_all_light"] if foxy_there else imgs["parts_service_without_foxy"]
                else:
                    current_img = imgs["parts_service_lo_light"]
                screen.blit(current_img, (0, 0))

            elif current_cam == '3':
                bb_there = bb_bot.pos == "Game Area" if bb_bot else False
                if light_on:
                    current_img = imgs["game_area_bb_light"] if bb_there else imgs["game_area_clear_light"]
                else:
                    current_img = imgs["game_area_bb"] if bb_there else imgs["game_area_clear"]
                screen.blit(current_img, (0, 0))

            elif current_cam == '5':
                toy_chica = next((b for b in bots if b.name == "Toy Chica"), None)
                bb_there = bb_bot.pos == "Left Air Vent" if bb_bot else False
                chica_there = toy_chica.pos == "Left Air Vent" if toy_chica else False

                if light_on:
                    current_img = imgs["left_vent_bb_light"] if bb_there else (imgs["left_vent_toy_chicka"] if chica_there else imgs["left_vent"])
                else:
                    current_img = imgs["left_vent"]
                screen.blit(current_img, (0, 0))

            elif current_cam == '2':
                toy_bonnie = next(b for b in bots if b.name == "Toy Bonnie")
                is_bonnie = toy_bonnie.pos == "Party Room2"
                if light_on:
                    current_img = imgs["party_room2_toy_bonnie_light"] if is_bonnie else imgs["party_room2_clear_light"]
                else:
                    current_img = imgs["party_room2_toy_bonnie"] if is_bonnie else imgs["party_room2_clear"]
                screen.blit(current_img, (0, 0))

            elif current_cam == '8':
                screen.blit(imgs["cam8_view"], (0, 0))

            if pomexi_frames:
                pomexi_overlay = pomexi_frames[pomexi_frame % len(pomexi_frames)][0].copy()
                pomexi_overlay.set_alpha(89)
                screen.blit(pomexi_overlay, (0, 0))

            map_bg = pygame.Surface(map_size, pygame.SRCALPHA)
            map_bg.fill((20, 20, 20, 200))
            screen.blit(map_bg, map_pos)

            font_cam = pygame.font.SysFont("Arial", 16, bold=True)
            for cam_id, cam_data in cam_buttons.items():
                btn_rect = cam_data['rect'].copy()
                btn_rect.move_ip(map_pos)
                color = (50, 200, 50) if cam_id == current_cam else (60, 60, 60)
                pygame.draw.rect(screen, color, btn_rect)
                pygame.draw.rect(screen, (200, 200, 200), btn_rect, 2)
                cam_text = font_cam.render(cam_data['label'], True, (255, 255, 255))
                screen.blit(cam_text, (btn_rect.x + (btn_rect.width - cam_text.get_width()) // 2, 
                                     btn_rect.y + (btn_rect.height - cam_text.get_height()) // 2))
        else:
            mouse_x, _ = pygame.mouse.get_pos()
            target_x = -(mouse_x / WIN_W) * (imgs["main"].get_width() - WIN_W)
            office_x += (target_x - office_x) * 0.1

            current_img = imgs["main"]

            if show_hall:
                current_img = imgs["hall_foxy"] if foxy_bot and foxy_bot.pos == "Hall" else imgs["hall_clear"]
            elif show_vent_l:
                if bb_bot and bb_bot.pos == "Office Vent Left":
                    current_img = imgs["office_bb_vent"]
                else:
                    chica_bot = next(b for b in bots if b.name == "Toy Chica")
                    current_img = imgs["vent_l_chica"] if chica_bot.pos == "Office Vent Left" else imgs["vent_l_clear"]
            elif show_vent_r:
                bonnie_bot = next(b for b in bots if b.name == "Toy Bonnie")
                current_img = imgs["vent_r_bonnie"] if bonnie_bot.pos == "Office Vent Right" else imgs["vent_r_clear"]

            screen.blit(current_img, (office_x, 0))

            if bb_in_office:
                screen.blit(imgs["office_bb"], (office_x, 0))

        if game_state == "CHECKING":
            now = pygame.time.get_ticks()

            if mask_on and check_type == "fail":
                check_type = "success"
                success_start = now

            if check_type == "fail" and now - check_start > 1300:
                active_js_bot = checking_bot.name
                game_state = "JUMPSCARE"
                js_frame_index = 0
                stop_all_sounds()
                play_sound(jumpscare_sound)

            frames = checks.get(checking_bot.name + "_fail")
            if frames:
                screen.blit(frames[js_frame_index % len(frames)][0], (office_x, 0))
                js_frame_index += 1

            if check_type == "success":
                if not mask_on:
                    active_js_bot = checking_bot.name
                    game_state = "JUMPSCARE"
                    js_frame_index = 0
                    stop_all_sounds()
                    play_sound(jumpscare_sound)
                elif now - success_start > 3000:
                    checking_bot.pos = checking_bot.start_pos if checking_bot.name == "Toy Bonnie" else "Stage"
                    checking_bot.last_think = pygame.time.get_ticks() + 3000
                    checking_bot.status_msg = "Waiting"
                    game_state = "PLAY"
                    stop_sound(check_sound)

        if mask_animation_state == "equipping" and mask_equip_frames:
            screen.blit(mask_equip_frames[mask_animation_frame][0], (0, 0))
        elif mask_animation_state == "equipped":
            screen.blit(imgs["mask"], (0, 0))
        elif mask_animation_state == "unequipping" and mask_unequip_frames:
            screen.blit(mask_unequip_frames[mask_animation_frame][0], (0, 0))

        if game_state in ["PLAY", "CHECKING"]:
            mouse_pos = pygame.mouse.get_pos()
            monitor_hover = monitor_button_rect.collidepoint(mouse_pos)
            mask_hover = mask_button_rect.collidepoint(mouse_pos)

            if mask_animation_state == "equipped":
                screen.blit(imgs["mask_button"], mask_button_rect)
            elif camera_mode:
                screen.blit(imgs["monitor_button"], monitor_button_rect)
            else:
                if mask_hover and mask_animation_state is None:
                    screen.blit(imgs["mask_button"], mask_button_rect)
                elif monitor_hover:
                    screen.blit(imgs["monitor_button"], monitor_button_rect)
                else:
                    screen.blit(imgs["monitor_button"], monitor_button_rect)
                    screen.blit(imgs["mask_button"], mask_button_rect)

        if puppet.charge < 50 and puppet.charge > 0:
            alert_frames = red_alert_frames if puppet.charge < 20 else orange_alert_frames
            if alert_frames:
                frame_idx = js_frame_index_alert % len(alert_frames)
                alert_w, alert_h = alert_frames[0][0].get_size()
                screen.blit(alert_frames[frame_idx][0], (WIN_W - alert_w - 10, WIN_H - alert_h - 10))

        screen.blit(font_clock.render(f"{hour} AM", True, (255, 255, 255)), (WIN_W - 150, 30))

        if dev_mode_active:
            dev_panel = pygame.Surface((420, 130), pygame.SRCALPHA)
            dev_panel.fill((0, 0, 0, 180))
            screen.blit(dev_panel, (10, 10))

            for i, bot in enumerate(bots):
                color = (0, 255, 0) if bot.pos == "Stage" else ((255, 255, 0) if bot.pos == "Target" else (255, 0, 0))
                screen.blit(font_dev.render(f"{bot.name}: {bot.pos} | {bot.status_msg}", True, color), (15, 15 + i*30))

    elif game_state == "MONITOR_OPENING":
        if monitor_up_frames:
            elapsed = pygame.time.get_ticks() - monitor_animation_start
            cum_time = current_surf = 0

            for surf, dur in monitor_up_frames:
                if elapsed < cum_time + dur:
                    current_surf = surf
                    break
                cum_time += dur

            if current_surf:
                mouse_x, _ = pygame.mouse.get_pos()
                target_x = -(mouse_x / WIN_W) * (imgs["main"].get_width() - WIN_W)
                office_x += (target_x - office_x) * 0.1
                screen.blit(imgs["main"], (office_x, 0))

                if bb_in_office:
                    screen.blit(imgs["office_bb"], (office_x, 0))

                screen.blit(current_surf, (0, 0))
                screen.blit(imgs["monitor_button"], monitor_button_rect)
            else:
                camera_mode = True
                game_state = "PLAY"
        else:
            camera_mode = True
            game_state = "PLAY"

    elif game_state == "MONITOR_CLOSING":
        if monitor_down_frames:
            elapsed = pygame.time.get_ticks() - monitor_animation_start
            cum_time = current_surf = 0

            for surf, dur in monitor_down_frames:
                if elapsed < cum_time + dur:
                    current_surf = surf
                    break
                cum_time += dur

            if current_surf:
                screen.fill((0, 0, 0))
                screen.blit(current_surf, (0, 0))
                screen.blit(imgs["monitor_button"], monitor_button_rect)
            else:
                camera_mode = False
                game_state = "PLAY"
        else:
            camera_mode = False
            game_state = "PLAY"

    elif game_state == "MENU":
        elapsed_sec = (pygame.time.get_ticks() - menu_music_start_time) / 1000.0
        beat_detector.update(elapsed_sec)
        shake_x, shake_y = beat_detector.get_shake_offset()

        screen.fill((0, 0, 0))
        screen.blit(imgs["menu"], (shake_x, shake_y))

        for i, btn in enumerate(menu_buttons):
            if i == 2 and not is_custom_unlocked:
                continue

            text_surf = menu_font.render(btn["text"], True, (255, 255, 255))
            x, y = 200 + shake_x, (menu_button_y_start + (i if i <= 2 else 3) * menu_button_spacing + shake_y)

            screen.blit(text_surf, (x, y))

            if i == menu_selected:
                screen.blit(menu_font.render(">>", True, (255, 255, 255)), (x - menu_font.size(">>")[0] - 20, y))

                if btn["action"] == "continue":
                    screen.blit(menu_font.render(f"НОЧЬ {current_night}", True, (255, 255, 255)), (x, y + text_surf.get_height() + 10))

        screen.blit(imgs["bug_icon"], (rect_bug.x + shake_x, rect_bug.y + shake_y))
        screen.blit(imgs["tg_icon"], (rect_tg.x + shake_x, rect_tg.y + shake_y))
        screen.blit(imgs["tiktok_icon"], (rect_tiktok.x + shake_x, rect_tiktok.y + shake_y))

    elif game_state == "BUG_REPORT":
        screen.fill((0, 0, 0))

        window_rect = pygame.Rect(WIN_W // 2 - 400, WIN_H // 2 - 250, 800, 500)
        pygame.draw.rect(screen, (40, 40, 40), window_rect)
        pygame.draw.rect(screen, (200, 200, 200), window_rect, 3)

        title = font_title.render("Сообщить о баге", True, (255, 255, 255))
        screen.blit(title, (WIN_W // 2 - title.get_width() // 2, WIN_H // 2 - 230))

        close_btn = pygame.Rect(WIN_W // 2 + 350, WIN_H // 2 - 250, 40, 40)
        pygame.draw.rect(screen, (150, 50, 50), close_btn)
        pygame.draw.rect(screen, (255, 255, 255), close_btn, 2)
        screen.blit(font_button.render("X", True, (255, 255, 255)), (close_btn.x + 8, close_btn.y + 2))

        screen.blit(font_bug_report.render("Опишите баг:", True, (255, 255, 255)), (WIN_W // 2 - 350, WIN_H // 2 - 180))

        text_box = pygame.Rect(WIN_W // 2 - 350, WIN_H // 2 - 150, 700, 100)
        pygame.draw.rect(screen, (60, 60, 60), text_box)
        pygame.draw.rect(screen, (200, 200, 200), text_box, 2)

        words = bug_report_text.split(' ')
        lines, current_line = [], ""
        for word in words:
            test_line = current_line + word + " "
            if font_bug_input.size(test_line)[0] < 680:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)

        y_offset = 0
        for line in lines[-4:]:
            screen.blit(font_bug_input.render(line, True, (255, 255, 255)), (text_box.x + 10, text_box.y + 10 + y_offset))
            y_offset += 25

        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = text_box.x + 10 + font_bug_input.size(lines[-1] if lines else "")[0]
            cursor_y = text_box.y + 10 + (len(lines[-4:]) - 1) * 25
            pygame.draw.line(screen, (255, 255, 255), (cursor_x, cursor_y), (cursor_x, cursor_y + 20), 2)

        screen.blit(font_bug_report.render("Категория:", True, (255, 255, 255)), (WIN_W // 2 - 350, WIN_H // 2 - 30))

        for i, cat in enumerate(bug_categories):
            y_pos = WIN_H // 2 - 50 + i * 60

            radio_rect = pygame.Rect(WIN_W // 2 - 300, y_pos, 30, 30)
            pygame.draw.circle(screen, (200, 200, 200), radio_rect.center, 15, 2)

            if bug_report_category == cat:
                pygame.draw.circle(screen, (50, 200, 50), radio_rect.center, 10)

            screen.blit(font_bug_input.render(cat, True, (255, 255, 255)), (WIN_W // 2 - 260, y_pos + 5))

        submit_btn = pygame.Rect(WIN_W // 2 - 100, WIN_H // 2 + 200, 200, 50)
        can_submit = bug_report_text.strip() and bug_report_category

        btn_color = (50, 150, 50) if (can_submit and can_submit_bug_report()) else (100, 100, 100)

        pygame.draw.rect(screen, btn_color, submit_btn)
        pygame.draw.rect(screen, (200, 200, 200), submit_btn, 3)
        screen.blit(font_button.render("Отправить", True, (255, 255, 255)), 
                   (submit_btn.x + (submit_btn.width - font_button.size("Отправить")[0])//2, submit_btn.y + 10))

        if not can_submit_bug_report():
            minutes, seconds = get_time_until_next_report()
            cooldown_text = font_bug_input.render(f"Подождите {minutes}:{seconds:02d} до следующего отчета", True, (255, 100, 100))
            screen.blit(cooldown_text, (WIN_W // 2 - cooldown_text.get_width() // 2, WIN_H // 2 + 170))

    elif game_state == "MODS":
        screen.fill((0, 0, 0))

        window_width, window_height = 800, 600
        window_x, window_y = WIN_W // 2 - window_width // 2, WIN_H // 2 - window_height // 2

        window_rect = pygame.Rect(window_x, window_y, window_width, window_height)
        pygame.draw.rect(screen, (40, 40, 40), window_rect)
        pygame.draw.rect(screen, (200, 200, 200), window_rect, 3)

        title = font_title.render("Моды", True, (255, 255, 255))
        screen.blit(title, (WIN_W // 2 - title.get_width() // 2, window_y + 20))

        panel_width = 150
        panel_rect = pygame.Rect(window_x + 10, window_y + 70, panel_width, window_height - 80)
        pygame.draw.rect(screen, (30, 30, 30), panel_rect)
        pygame.draw.rect(screen, (200, 200, 200), panel_rect, 2)

        tab_buttons = [
            {"text": "Популярное", "id": "popular", "y": window_y + 80},
            {"text": "Моды игры", "id": "developer", "y": window_y + 140},
            {"text": "Библиотека", "id": "library", "y": window_y + 200}
        ]

        for tab in tab_buttons:
            tab_rect = pygame.Rect(window_x + 15, tab["y"], panel_width - 10, 50)

            color = (70, 130, 180) if current_mods_tab == tab["id"] else (50, 50, 50)
            pygame.draw.rect(screen, color, tab_rect, border_radius=5)
            pygame.draw.rect(screen, (200, 200, 200), tab_rect, 2, border_radius=5)

            tab_text = font_mods_tab.render(tab["text"], True, (255, 255, 255))
            screen.blit(tab_text, (tab_rect.x + (tab_rect.width - tab_text.get_width()) // 2, 
                                  tab_rect.y + (tab_rect.height - tab_text.get_height()) // 2))

        close_btn = pygame.Rect(WIN_W // 2 + 350, WIN_H // 2 - 300, 40, 40)
        pygame.draw.rect(screen, (150, 50, 50), close_btn)
        pygame.draw.rect(screen, (255, 255, 255), close_btn, 2)
        screen.blit(font_button.render("X", True, (255, 255, 255)), (close_btn.x + 8, close_btn.y + 2))

        content_x = window_x + panel_width + 20
        content_y = window_y + 80

        if current_mods_tab in ["popular", "developer"]:
            text = "Популярные моды" if current_mods_tab == "popular" else "Моды от разработчика"
            empty_text = font_mods.render(f"{text} скоро появятся!", True, (200, 200, 200))
            screen.blit(empty_text, (content_x + 50, content_y + 100))

        elif current_mods_tab == "library":
            if not available_mods:
                screen.blit(font_mods.render("Модов пока нет.", True, (200, 200, 200)), (content_x + 100, content_y + 50))
                screen.blit(font_bug_input.render("Добавьте .py файлы в папку с модами", True, (150, 150, 150)), (content_x + 50, content_y + 80))
            else:
                for i, mod in enumerate(available_mods):
                    mod_y = content_y + i * 80

                    screen.blit(font_mods.render(mod['name'], True, (255, 255, 255)), (content_x + 10, mod_y))

                    is_installed = installed_mod and installed_mod['name'] == mod['name']

                    if is_installed:
                        launch_btn = pygame.Rect(content_x + 200, mod_y + 10, 120, 40)
                        pygame.draw.rect(screen, (50, 150, 50), launch_btn)
                        pygame.draw.rect(screen, (200, 200, 200), launch_btn, 2)
                        screen.blit(font_bug_report.render("Запустить", True, (255, 255, 255)), 
                                   (launch_btn.x + (launch_btn.width - font_bug_report.size("Запустить")[0])//2, launch_btn.y + 10))

                        uninstall_btn = pygame.Rect(content_x + 330, mod_y + 10, 60, 40)
                        pygame.draw.rect(screen, (150, 50, 50), uninstall_btn)
                        pygame.draw.rect(screen, (200, 200, 200), uninstall_btn, 2)
                        screen.blit(font_bug_report.render("X", True, (255, 255, 255)), 
                                   (uninstall_btn.x + (uninstall_btn.width - font_bug_report.size("X")[0])//2, uninstall_btn.y + 10))

                        screen.blit(font_bug_input.render("(Установлен)", True, (50, 255, 50)), 
                                   (content_x + 10 + font_mods.size(mod['name'])[0] + 10, mod_y + 5))
                    else:
                        install_btn = pygame.Rect(content_x + 200, mod_y + 10, 120, 40)
                        pygame.draw.rect(screen, (100, 100, 150), install_btn)
                        pygame.draw.rect(screen, (200, 200, 200), install_btn, 2)
                        screen.blit(font_bug_report.render("Установить", True, (255, 255, 255)), 
                                   (install_btn.x + (install_btn.width - font_bug_report.size("Установить")[0])//2, install_btn.y + 10))

            open_folder_btn = pygame.Rect(WIN_W // 2 - 100, WIN_H // 2 + 230, 200, 50)
            pygame.draw.rect(screen, (70, 130, 180), open_folder_btn, border_radius=15)
            pygame.draw.rect(screen, (200, 200, 200), open_folder_btn, 3, border_radius=15)
            folder_btn_text = font_button.render("Папка с модами", True, (255, 255, 255))
            screen.blit(folder_btn_text, (open_folder_btn.x + (open_folder_btn.width - folder_btn_text.get_width())//2, open_folder_btn.y + 10))

        warning_y = window_y + window_height + 20
        warning_text1 = font_mods_warning.render("Внимание! Моды являются модификацией игрового кода.", True, (255, 50, 50))
        warning_text2 = font_mods_warning.render("Перед их скачиванием проверяйте мод на вирусы!", True, (255, 50, 50))
        screen.blit(warning_text1, (WIN_W // 2 - warning_text1.get_width() // 2, warning_y))
        screen.blit(warning_text2, (WIN_W // 2 - warning_text2.get_width() // 2, warning_y + 25))

    elif game_state == "CUSTOM":
        screen.fill((0, 0, 0))

        custom_title = font_title.render("Custom Night", True, (255, 255, 255))
        screen.blit(custom_title, (WIN_W//2 - custom_title.get_width()//2, 50))

        for i, name in enumerate(custom_characters):
            x, y = char_positions[i]
            level = custom_levels[name]

            face_map = {
                "Toy Bonnie": ["toy_bonnie_face", "toy_bonnie_face2", "toy_bonnie_face3"],
                "Toy Chica": ["toy_chica_face", "toy_chica_face2", "toy_chica_face3"],
                "Withered Foxy": ["withered_foxy_face", "withered_foxy_face2", "withered_foxy_face3"],
                "Puppet": ["puppet_face"],
                "Balloon Boy": ["bb_face", "bb_face2", "bb_face3", "bb_face4"],
                "Withered Bonny": ["WitheredBonnyFace"],
            }

            if name in face_map:
                faces = face_map[name]
                if name == "Balloon Boy":
                    face_idx = 0 if level <= 2 else (1 if level <= 6 else (2 if level <= 12 else 3))
                elif name != "Puppet":
                    face_idx = 0 if level <= 2 else (1 if level <= 6 else 2)
                else:
                    face_idx = 0

                face_key = faces[min(face_idx, len(faces) - 1)]
                if face_key in imgs:
                    face_img = imgs[face_key]
                    screen.blit(face_img, (x - face_img.get_width() // 2, y - face_img.get_height() // 2 - 30))

            screen.blit(font_button.render(name, True, (255, 255, 255)), (x - font_button.size(name)[0] // 2, y + 60))

            pygame.draw.rect(screen, (100, 100, 100), custom_rects_left[name])
            pygame.draw.rect(screen, (200, 200, 200), custom_rects_left[name], 2)
            screen.blit(font_button.render("<", True, (255, 255, 255)), (custom_rects_left[name].x + 8, custom_rects_left[name].y + 5))

            level_text = pygame.font.SysFont("Arial", 28, bold=True).render(str(level), True, (255, 255, 0))
            level_rect = custom_level_rects[name]
            screen.blit(level_text, (level_rect.x + (level_rect.width - level_text.get_width()) // 2, 
                                    level_rect.y + (level_rect.height - level_text.get_height()) // 2))

            pygame.draw.rect(screen, (100, 100, 100), custom_rects_right[name])
            pygame.draw.rect(screen, (200, 200, 200), custom_rects_right[name], 2)
            screen.blit(font_button.render(">", True, (255, 255, 255)), (custom_rects_right[name].x + 8, custom_rects_right[name].y + 5))

        pygame.draw.rect(screen, (50, 150, 50), rect_start_custom)
        pygame.draw.rect(screen, (200, 200, 200), rect_start_custom, 3)
        screen.blit(font_button.render("START", True, (255, 255, 255)), 
                   (rect_start_custom.x + (rect_start_custom.width - font_button.size("START")[0])//2, rect_start_custom.y + 10))

    elif game_state == "JUMPSCARE":
        screen.fill((0, 0, 0))
        frames = jumpscares.get(active_js_bot)

        if frames and js_frame_index < len(frames):
            screen.blit(frames[js_frame_index][0], (0, 0))
            js_frame_index += 1
        else:
            if active_js_bot == "Withered Foxy":
                game_state = "FOXY_SEQUENCE"
                foxy_sequence_start = pygame.time.get_ticks()
                black_screen_alpha = foxy_sound_played = foxy_sound_end = 0
            else:
                game_state = "GAMEOVER"

    elif game_state == "FOXY_SEQUENCE":
        screen.fill((0, 0, 0))
        now = pygame.time.get_ticks()
        elapsed = now - foxy_sequence_start

        if elapsed < 600:
            black_screen_alpha = (elapsed / 600.0) * 255
        else:
            black_screen_alpha = 255
            if not foxy_sound_played:
                if elapsed >= 1600:
                    play_sound(foxy_line1_sound)
                    foxy_sound_played = True
                    foxy_sound_end = now + int((foxy_line1_sound.get_length() * 1000 if foxy_line1_sound else 0) + 300)

        if foxy_sound_played and now >= foxy_sound_end:
            fade_out_elapsed = now - foxy_sound_end
            if fade_out_elapsed < 600:
                black_screen_alpha = 255 - (fade_out_elapsed / 600.0) * 255
            else:
                game_state = "MENU"
                play_sound(menu_music, -1)
                menu_music_start_time = pygame.time.get_ticks()
                beat_detector.reset()

        black_surf = pygame.Surface((WIN_W, WIN_H))
        black_surf.fill((0, 0, 0))
        black_surf.set_alpha(int(black_screen_alpha))
        screen.blit(black_surf, (0, 0))

    elif game_state == "PUPPET_DANCE":
        screen.fill((0, 0, 0))

        if puppet_dance_frames and js_frame_index < len(puppet_dance_frames):
            screen.blit(puppet_dance_frames[js_frame_index][0], (0, 0))
            js_frame_index += 1
        else:
            active_js_bot = "Puppet"
            game_state = "JUMPSCARE"
            js_frame_index = 0
            stop_all_sounds()
            play_sound(jumpscare_sound)

    elif game_state == "SIX_AM_ANIMATION":
        screen.fill((0, 0, 0))

        if not six_am_sound_playing:
            play_sound(six_am_theme)
            six_am_sound_playing = True

        if six_am_frames and six_am_frame_index < len(six_am_frames):
            now = pygame.time.get_ticks()
            elapsed = now - six_am_animation_start
            cum_time = 0

            for i, (surf, dur) in enumerate(six_am_frames):
                if elapsed < cum_time + dur:
                    six_am_frame_index = i
                    screen.blit(surf, (0, 0))
                    break
                cum_time += dur
            else:
                stop_sound(six_am_theme)
                if not is_custom_night:
                    current_night = min(6, current_night + 1)
                    if current_night == 6:
                        is_custom_unlocked = True
                    save_progress()
                game_state = "MENU"
                play_sound(menu_music, -1)
                menu_music_start_time = pygame.time.get_ticks()
                beat_detector.reset()
                six_am_sound_playing = False
        else:
            screen.blit(font_main.render("6 AM", True, (255, 255, 255)), (WIN_W//2 - font_main.size("6 AM")[0]//2, WIN_H//2 - 50))

            if pygame.time.get_ticks() - six_am_animation_start >= 3000:
                stop_sound(six_am_theme)
                if not is_custom_night:
                    current_night = min(6, current_night + 1)
                    if current_night == 6:
                        is_custom_unlocked = True
                    save_progress()
                game_state = "MENU"
                play_sound(menu_music, -1)
                menu_music_start_time = pygame.time.get_ticks()
                beat_detector.reset()
                six_am_sound_playing = False

    elif game_state == "GAMEOVER":
        screen.fill((0, 0, 0))

        screen.blit(font_main.render("ВЫ УМЕРЛИ", True, (255, 0, 0)), (WIN_W//2 - font_main.size("ВЫ УМЕРЛИ")[0]//2, WIN_H//2 - 50))
        press_text = font_button.render("Нажмите любую кнопку для продолжения", True, (255, 255, 255))
        screen.blit(press_text, (WIN_W//2 - press_text.get_width()//2, WIN_H//2 + 50))

    pygame.display.flip()

save_progress()
pygame.quit()
