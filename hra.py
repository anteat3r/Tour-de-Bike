import pygame
import pygame.gfxdraw
import math
import random
from fyzika import Vector, Bike, BIKE_LENGTH, WHEEL_RADIUS

pygame.init()

import fyzika
fyzika.GRAVITY = Vector(0, 0.2)

obrazovka_sirka = 1920
obrazovka_vyska = 1080
screen = pygame.display.set_mode((obrazovka_sirka, obrazovka_vyska))
pygame.display.set_caption("Tour de Bike")

barva_nebe = (135, 206, 235)
barva_trava = (0, 154, 23)

fyzika.krok = 10
fyzika.obtiznost_mapy = 10000 # nizsi cislo = tezsi
fyzika.obrazovka_vyska = obrazovka_vyska

def nahrat_obrazky(kolo):
    global pomer
    obrazky = []
    
    for i in range(14):
        if i < 10:
            img = pygame.image.load(f"img/{kolo}/kolo000{i}.png").convert_alpha()
        else:
            img = pygame.image.load(f"img/{kolo}/kolo00{i}.png").convert_alpha()
        img_sirka = img.get_width()
        img_vyska = img.get_height()
        pomer = BIKE_LENGTH / img_sirka
        img = pygame.transform.smoothscale(img, (img_sirka * pomer, img_vyska * pomer))
        obrazky.append(img)
    return obrazky

def blit_rotate_bottom_left(surf, image, bottom_left_pos, angle):
    global maska_kola, kolo_pos
    offset_y = pomer * 80

    image_rect = image.get_rect()
    width, height = image_rect.size
    offset_center_to_bl = pygame.math.Vector2(-width / 2, height / 2 - offset_y)  # upraveno zde
    rotated_offset = offset_center_to_bl.rotate(-angle)
    rotated_center = (bottom_left_pos[0] - rotated_offset.x, bottom_left_pos[1] - rotated_offset.y)
    rotated_image = pygame.transform.rotozoom(image, angle, 1.0)
    new_rect = rotated_image.get_rect(center=rotated_center)
    maska_kola = pygame.mask.from_surface(rotated_image)
    kolo_pos = (new_rect.left, new_rect.top)

    surf.blit(rotated_image, new_rect.topleft)

def vykresli_text(surf, text, barva, pozice, zarovnat="left", velikost=50, font="Arial"):
    font = pygame.font.SysFont(font, velikost)
    text_surface = font.render(text, True, barva)
    text_rect = text_surface.get_rect()
    if zarovnat == "left":
        text_rect.topleft = pozice
    elif zarovnat == "center":
        text_rect.center = pozice
    elif zarovnat == "right":
        text_rect.topright = pozice
    surf.blit(text_surface, text_rect)

class EnergetickyPredmet(pygame.sprite.Sprite):
    def __init__(self, x, y, obrazek, pridavek_energie):
        super().__init__()
        self.svet_x = x
        self.svet_y = y
        self.pridavek_energie = pridavek_energie
        self.image = obrazek
        self.mask = pygame.mask.from_surface(self.image)

    def vykresli(self, screen, kamera_x, kamera_y):
        screen.blit(self.image, (self.svet_x - kamera_x, self.svet_y - kamera_y))

    def get_mask(self):
        return self.mask
    
    def get_position(self):
        return int(self.svet_x), int(self.svet_y)
    
class Mince(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.svet_x = x
        self.svet_y = y
        self.image = mince_img
        self.mask = pygame.mask.from_surface(self.image)

    def vykresli(self, screen, kamera_x, kamera_y):
        screen.blit(self.image, (self.svet_x - kamera_x, self.svet_y - kamera_y))

    def get_mask(self):
        return self.mask

    def get_position(self):
        return int(self.svet_x), int(self.svet_y)

def vykresli_ui(screen, km, energie, kolo_x, rychlost, cas):
    vykresli_text(screen, f"Ujeto: {round(km/1000,1)} km", (0, 0, 0), (22, 20))

    pygame.draw.rect(screen, (50, 50, 50), (20, 90, 250, 40))
    if energie > 0:
        pygame.draw.rect(screen, (255, 215, 0), (20, 90, 2.5 * energie, 40))
    pygame.draw.rect(screen, (0, 0, 0), (20, 90, 250, 40), 2)

    screen.blit(tachometr_img, (50, 650))

    sekundy = cas // 1000
    minuty = sekundy // 60
    hodiny = minuty // 60
    sekundy = sekundy % 60
    minuty = minuty % 60

    vykresli_text(screen, f"{hodiny}:{minuty}:{sekundy}", (255, 255, 255), (252, 970), zarovnat="center", velikost=30)

    stred_x = 250
    stred_y = 845
    delka_rucicky = 170
    uhel = -220 + (abs(rychlost) / 70) * 262
    uhel_rad = math.radians(uhel)
    konec_x = stred_x + delka_rucicky * math.cos(uhel_rad)
    konec_y = stred_y + delka_rucicky * math.sin(uhel_rad)
    pygame.draw.line(screen, (255, 0, 0), (stred_x, stred_y), (konec_x, konec_y), 6)

    if energie_predmety:
        predmety_vpravo = []
        for predmet in energie_predmety:
            if predmet.svet_x > kolo_x:
                predmety_vpravo.append(predmet)

        nejblizsi = None
        nejmensi_vzdalenost = None

        for predmet in predmety_vpravo:
            rozdil = predmet.svet_x - kolo_x
            if nejmensi_vzdalenost is None or rozdil < nejmensi_vzdalenost:
                nejblizsi = predmet
                nejmensi_vzdalenost = rozdil

        if nejblizsi:
            vzdalenost = nejblizsi.svet_x - kolo_x
            vykresli_text(screen, f"{round(vzdalenost/1000,1)} km →", (0, 0, 0), (obrazovka_sirka - 20, 20), zarovnat="right")

def vykresli_teren(screen, kamera_x, kamera_y, kaminky):
    smazat_kaminky = []
    for x in kaminky:
        if x < kamera_x - 2 * obrazovka_sirka or x > kamera_x + obrazovka_sirka + 2 * obrazovka_sirka:
            smazat_kaminky.append(x)
    for x in smazat_kaminky:
        del kaminky[x]
    vyska_travy = 50
    barva_hlina = (120, 72, 0)
    barva_kamen = (80, 60, 40)

    body_trava = [[0, obrazovka_vyska]]
    body_hlina = [[0, obrazovka_vyska+ vyska_travy]]
    body_hrana = []
    x_svet = kamera_x - (kamera_x % fyzika.krok)

    x = x_svet
    while True:
        x_obrazovka = x - kamera_x - fyzika.krok
        if x_obrazovka > obrazovka_sirka + fyzika.krok:
            break
        y = fyzika.generace_bod(x) - kamera_y
        body_trava.append([x_obrazovka, y])
        perp_vec = (Vector(body_trava[-1][0], body_trava[-1][1]) - Vector(body_trava[-2][0], body_trava[-2][1])).perpendicular()
        if perp_vec.y < 0:
            perp_vec.x *= -1
            perp_vec.y *= -1
        
        hlina_vec = Vector(x_obrazovka, y) + perp_vec * vyska_travy
        body_hlina.append([hlina_vec.x, hlina_vec.y])
        body_hrana.append((x_obrazovka, y))
        x += fyzika.krok

    body_trava.append([obrazovka_sirka, fyzika.generace_bod(kamera_x + obrazovka_sirka + fyzika.krok) - kamera_y])
    body_trava.append([obrazovka_sirka, obrazovka_vyska])

    body_hlina.append([obrazovka_sirka, fyzika.generace_bod(kamera_x + obrazovka_sirka + fyzika.krok) + vyska_travy - kamera_y])
    body_hlina.append([obrazovka_sirka, obrazovka_vyska])

    pygame.gfxdraw.filled_polygon(screen, body_trava, barva_trava)
    pygame.gfxdraw.filled_polygon(screen, body_hlina, barva_hlina)

    x = int(x_svet)
    while x < kamera_x + obrazovka_sirka + fyzika.krok:
        if x not in kaminky:
            y = fyzika.generace_bod(x)
            y_hlina = y + vyska_travy
            segment_kaminky = []
            for _ in range(10):
                kaminek_x = random.randint(x, x + fyzika.krok)
                polomer = random.randint(1, 4)
                kaminek_y = random.randint(int(y_hlina+30), int(y_hlina + obrazovka_vyska+30))
                segment_kaminky.append((kaminek_x, kaminek_y, polomer))
            kaminky[x] = segment_kaminky
        x += fyzika.krok

    for _, kaminky_segment in kaminky.items():
        for kaminek_x, kaminek_y, polomer in kaminky_segment:
            if kamera_x < kaminek_x < kamera_x + obrazovka_sirka and int(kaminek_y - kamera_y) < obrazovka_vyska:
                pygame.draw.circle(screen, barva_kamen, (int(kaminek_x - kamera_x), int(kaminek_y - kamera_y)),polomer)


    pygame.draw.lines(screen, (0, 0, 0), False, body_hrana, 2)



def vykresli_kolo(kolo, camera, rafek_img, kolo_img):
    global rafek_mask_front, rafek_mask_rear, rafek_pos_front, rafek_pos_rear
    rafek_rear_rot = pygame.transform.rotozoom(rafek_img, (kolo.rear_wheel.get_position().x / (WHEEL_RADIUS)) * (-180 / math.pi), 1.0)
    rafek_mask_rear = pygame.mask.from_surface(rafek_rear_rot)
    rafek_front_rot = pygame.transform.rotozoom(rafek_img, (kolo.front_wheel.get_position().x / (WHEEL_RADIUS)) * (-180 / math.pi), 1.0)
    rafek_mask_front = pygame.mask.from_surface(rafek_front_rot)

    rafek_rect_rear = rafek_rear_rot.get_rect(center=(int(kolo.rear_wheel.position.x - camera.x), int(kolo.rear_wheel.position.y - camera.y)))
    rafek_pos_rear = (rafek_rect_rear.left, rafek_rect_rear.top)
    rafek_rect_front = rafek_front_rot.get_rect(center=(int(kolo.front_wheel.position.x - camera.x), int(kolo.front_wheel.position.y - camera.y)))
    rafek_pos_front = (rafek_rect_front.left, rafek_rect_front.top)

    screen.blit(rafek_rear_rot, rafek_rect_rear.topleft)
    screen.blit(rafek_front_rot, rafek_rect_front.topleft)

    center = kolo.rear_axel.position
    blit_rotate_bottom_left(screen, kolo_img, (int(center.x - camera.x), int(center.y - camera.y)), (-180 / math.pi) * math.atan2(kolo.front_axel.position.y - kolo.rear_axel.position.y, kolo.front_axel.position.x - kolo.rear_axel.position.x))

def vykresli_mraky(screen, kamera_x, kamera_y, mraky):
    for m in mraky:
        x = int(m["x"] - kamera_x * m["parallax"])
        y = int(m["y"] - kamera_y * m["parallax"])
        img = pygame.transform.smoothscale(mrak_img, (int(mrak_img.get_width() * m["velikost"]), int(mrak_img.get_height() * m["velikost"])))
        if x < -img.get_width():
            m["x"] += obrazovka_sirka * 2 + img.get_width()
            x = int(m["x"] - kamera_x * m["parallax"])
        elif x > obrazovka_sirka + img.get_width():
            m["x"] -= obrazovka_sirka * 2 + img.get_width()
            x = int(m["x"] - kamera_x * m["parallax"])
        screen.blit(img, (x, y))

banan_img = pygame.image.load("img/banan.png").convert_alpha()
k = 70 / banan_img.get_width()
banan_img = pygame.transform.smoothscale(banan_img, (int(banan_img.get_width() * k), int(banan_img.get_height() * k)))
banan_energie = 30

tycinka_img = pygame.image.load("img/tycinka.png").convert_alpha()
k = 120 / tycinka_img.get_width()
tycinka_img = pygame.transform.smoothscale(tycinka_img, (int(tycinka_img.get_width() * k), int(tycinka_img.get_height() * k)))
tycinka_energie = 50

kure_img = pygame.image.load("img/kure.png").convert_alpha()
k = 85 / kure_img.get_width()
kure_img = pygame.transform.smoothscale(kure_img, (int(kure_img.get_width() * k), int(kure_img.get_height() * k)))
kure_energie = 100

energie_predmety = pygame.sprite.Group()

mince_img = pygame.image.load("img/mince.png").convert_alpha()
k = 60 / mince_img.get_width()
mince_img = pygame.transform.smoothscale(mince_img, (int(mince_img.get_width() * k), int(mince_img.get_height() * k)))

mince_predmety = pygame.sprite.Group()
vzadelnost_minci = 500
prachy = 0

rafek_img = pygame.image.load("img/rafek.png").convert_alpha()
rafek_img = pygame.transform.smoothscale(rafek_img, (WHEEL_RADIUS * 2, WHEEL_RADIUS * 2))

tachometr_img = pygame.image.load("img/tachometr.png").convert_alpha()
tachometr_img = pygame.transform.smoothscale(tachometr_img, (400, 400))

obloha_img = pygame.image.load("img/obloha.png").convert_alpha()
obloha_img = pygame.transform.smoothscale(obloha_img, (obrazovka_sirka, obrazovka_vyska))

mrak_img = pygame.image.load("img/mrak.png").convert_alpha()
mrak_img = pygame.transform.smoothscale(mrak_img, (mrak_img.get_width() // 2, mrak_img.get_height() // 2))

ztrata_energie = 0.05
rust_vzdalenosti = 200

# TODO: main menu, nastaveni, ulozeni a nacteni hry, vylepseni kola, ruzne mapy
# TODO: hudba, zvuk
# TODO: credity - ondra = fyzika, antialiasing, rosta - bug fix kaminku


def main(kolo, vybrane_jidlo):
    global prachy
    ram_obrazky = nahrat_obrazky(kolo)

    mraky = []
    for vrstva in range(3):
        parallax = 0.15 + 0.2 * vrstva
        for i in range(2):
            x = random.randint(0, obrazovka_sirka * 2)
            y = vrstva * 10 - random.randint(70, 80)
            velikost = 0.7 + 0.3 * random.random()
            mraky.append({
                "x": x,
                "y": y,
                "parallax": parallax,
                "velikost": velikost,
                "vrstva": vrstva
            })

    kaminky = {}
    start_cas = pygame.time.get_ticks()
    bezi = True
    clock = pygame.time.Clock()
    
    kolo = Bike(Vector(obrazovka_sirka / 2, fyzika.generace_bod(obrazovka_sirka / 2)-200))

    km_ujet = 0
    vzdalenost_predmetu = 1000
    kolikaty_banan = 0

    #energie_predmety.add(EnergetickyPredmet(1500, fyzika.generace_bod(1500)-190, tycinka_img, tycinka_energie))
    #energie_predmety.add(EnergetickyPredmet(1400, fyzika.generace_bod(1400)-190, kure_img, kure_energie))

    if vybrane_jidlo == 0:
        jidlo_img = banan_img
        jidlo_energie = banan_energie
    elif vybrane_jidlo == 1:
        jidlo_img = tycinka_img
        jidlo_energie = tycinka_energie
    elif vybrane_jidlo == 2:
        jidlo_img = kure_img
        jidlo_energie = kure_energie
    else:
        jidlo_img = banan_img
        jidlo_energie = banan_energie

    mince_predmety.empty()
    posledni_mince = 0

    camera = Vector(0, 0)

    while bezi:
        screen.blit(obloha_img, (0, 0))
        vykresli_mraky(screen, camera.x, camera.y, mraky)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        kolo.tick()
        vykresli_kolo(kolo, camera, rafek_img, ram_obrazky[int(kolo.animace_index)])
        camera = fyzika.lerp(camera, kolo.rear_axel.position - Vector(-BIKE_LENGTH / 2 + obrazovka_sirka/2, obrazovka_vyska/1.5), 0.1)

        vykresli_teren(screen, camera.x, camera.y, kaminky)

        while kolo.rear_axel.position.x + obrazovka_sirka >= posledni_mince + vzadelnost_minci:

            posledni_mince += vzadelnost_minci

            je_blizko = False
            for energie_predmet in energie_predmety.copy():
                if abs(posledni_mince - energie_predmet.svet_x) < 10:
                    je_blizko = True
                    break

            if not je_blizko:
                mince_predmety.add(Mince(posledni_mince, fyzika.generace_bod(posledni_mince)-random.randint(100,250)))

        for mince in mince_predmety.copy():
            mince.vykresli(screen, camera.x, camera.y)
            if abs(mince.svet_x - kolo.rear_axel.position.x) < 400:
                mince_mask = mince.get_mask()
                mince_pos = (int(mince.svet_x - camera.x), int(mince.svet_y - camera.y))
                kolo_masky = [(maska_kola, kolo_pos), (rafek_mask_rear, rafek_pos_rear),(rafek_mask_front, rafek_pos_front)]
                for mask, pos in kolo_masky:
                    offset = (mince_pos[0] - pos[0], mince_pos[1] - pos[1])
                    if mask.overlap(mince_mask, offset):
                        prachy += 1
                        mince_predmety.remove(mince)

        for predmet in energie_predmety.copy():
            predmet.vykresli(screen, camera.x, camera.y)
            if abs(predmet.svet_x - kolo.rear_axel.position.x) < 400:
                predmet_mask = predmet.get_mask()
                predmet_pos = (int(predmet.svet_x - camera.x), int(predmet.svet_y - camera.y))
                kolo_masky = [(maska_kola, kolo_pos), (rafek_mask_rear, rafek_pos_rear),(rafek_mask_front, rafek_pos_front)]
                for mask, pos in kolo_masky:
                    offset = (predmet_pos[0] - pos[0], predmet_pos[1] - pos[1])
                    if mask.overlap(predmet_mask, offset):
                        kolo.energie = min(kolo.energie + predmet.pridavek_energie, 100)
                        print(f"+ {predmet.pridavek_energie} energie")
                        energie_predmety.remove(predmet)
                        break

        if kolo.rear_axel.get_position().x > vzdalenost_predmetu:
            kolikaty_banan += 1
            vzdalenost_predmetu += rust_vzdalenosti * kolikaty_banan
            nova_predmet_x = kolo.rear_axel.get_position().x + vzdalenost_predmetu
            energie_predmety.add(EnergetickyPredmet(nova_predmet_x, fyzika.generace_bod(nova_predmet_x) - 150, jidlo_img, jidlo_energie))

        km_ujet = kolo.rear_axel.get_position().x

        kolo.energie -= ztrata_energie
        if kolo.energie < -10:
            energie_predmety.empty()
            bezi = False

        rychlost = kolo.rear_wheel.get_speed().x
        vykresli_ui(screen, km_ujet, kolo.energie, kolo.rear_axel.get_position().x, rychlost, pygame.time.get_ticks() - start_cas)

        vykresli_text(screen, f"Money: {prachy}", (255, 215, 0), (22, 360), velikost=50)

        fps = clock.get_fps()
        vykresli_text(screen, f"FPS: {int(fps)}", (0, 0, 0), (20, 150), velikost=100)

        pygame.display.flip()
        clock.tick(60)

