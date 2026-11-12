from PIL import Image, ImageDraw, ImageFont
import math, os, subprocess, wave, struct

W, H, FPS, SECONDS = 180, 320, 12, 30
FRAMES = FPS * SECONDS
OUT = "output"
os.makedirs(OUT, exist_ok=True)

NIGHT = (13, 20, 43)
MID = (28, 43, 72)
WATER = (30, 65, 91)
GOLD = (247, 190, 94)
WHITE = (238, 231, 207)
SKIN = (190, 132, 91)
ROBE = (119, 91, 66)
MESSENGER = (220, 211, 178)

def clamp(v, lo=0, hi=255): return max(lo, min(hi, int(v)))
def mix(a, b, t): return tuple(clamp(x + (y-x)*t) for x,y in zip(a,b))

def person(d, x, y, robe, skin, pose="stand", limp=False, glow=False):
    # Compact 16-bit-style character sprite; x,y is top-left of head.
    if glow:
        d.rectangle((x-5,y-4,x+16,y+35), fill=(75,83,99))
    d.rectangle((x+2,y,x+9,y+7), fill=skin)
    d.rectangle((x+1,y-2,x+10,y), fill=(48,35,31))
    d.rectangle((x+3,y+2,x+4,y+3), fill=(24,24,28))
    d.rectangle((x+7,y+2,x+8,y+3), fill=(24,24,28))
    d.rectangle((x+1,y+8,x+11,y+23), fill=robe)
    d.rectangle((x,y+10,x+12,y+13), fill=robe)
    if pose == "wrestle":
        d.line((x+2,y+11,x-5,y+6), fill=skin, width=3)
        d.line((x+10,y+11,x+18,y+5), fill=skin, width=3)
    elif pose == "touch":
        d.line((x+2,y+11,x-3,y+17), fill=skin, width=3)
        d.line((x+10,y+11,x+15,y+20), fill=skin, width=3)
    else:
        d.line((x+2,y+11,x-2,y+19), fill=skin, width=3)
        d.line((x+10,y+11,x+14,y+18), fill=skin, width=3)
    if limp:
        d.line((x+4,y+23,x+1,y+31), fill=robe, width=4)
        d.line((x+8,y+23,x+13,y+30), fill=robe, width=4)
    else:
        d.line((x+4,y+23,x+3,y+31), fill=robe, width=4)
        d.line((x+8,y+23,x+10,y+31), fill=robe, width=4)
    d.rectangle((x,y+30,x+5,y+32), fill=(37,30,28))
    d.rectangle((x+8,y+30,x+13,y+32), fill=(37,30,28))

def make_frame(i):
    t = i / FPS
    sunrise = max(0, min(1, (t-20)/9))
    img = Image.new("RGB", (W,H), mix(NIGHT, (235,153,91), sunrise))
    d = ImageDraw.Draw(img)
    # Sky bands and distant hills
    for y in range(0,190,8):
        c = mix(NIGHT, (246,179,111), sunrise * max(0,(y-80)/130))
        d.rectangle((0,y,W,y+7), fill=c)
    # Stars fade as dawn arrives
    for k in range(34):
        sx=(k*47+13)%W; sy=(k*29+17)%145
        if sunrise < 0.75 and (k*7+i)%4 != 0:
            d.rectangle((sx,sy,sx+1,sy+1), fill=(226,224,199))
    moon_alpha = 1-sunrise
    if moon_alpha > .15:
        d.ellipse((132,28,151,47), fill=mix((232,224,190), mix(NIGHT,(246,179,111),sunrise), 1-moon_alpha))
    d.polygon([(0,174),(30,143),(61,172),(100,139),(139,174),(180,146),(180,222),(0,222)], fill=mix((29,43,67),(119,91,87),sunrise))
    # River with animated pixel ripples
    d.rectangle((0,205,W,H), fill=mix((22,53,79),(91,123,133),sunrise))
    for k in range(19):
        yy=214+(k*13)%100
        xx=(k*31+i*2)%W
        d.rectangle((xx,yy,xx+9+(k%4)*3,yy+1), fill=mix((77,120,140),(218,183,135),sunrise*.6))
    # Riverbank reeds
    for x in (8,18,163,173):
        d.line((x,224,x-2,202), fill=(73,104,79), width=2)
        d.line((x,215,x+5,207), fill=(73,104,79), width=2)

    if t < 5:
        # Jacob approaches the riverbank.
        jx = int(20 + t*5)
        person(d,jx,181,ROBE,SKIN)
        d.rectangle((108,212,128,214), fill=(153,132,106))
    elif t < 21:
        # The mysterious encounter and struggle through the night.
        bob = int(math.sin(i*.8)*2)
        person(d,68,177+bob,ROBE,SKIN,"wrestle")
        person(d,91,174-bob,MESSENGER,(218,185,151),"wrestle",glow=True)
        d.rectangle((79,207,84,210), fill=(226,191,115))
        if i % 6 < 3:
            d.rectangle((56,168,58,170), fill=(244,206,133))
            d.rectangle((116,165,118,167), fill=(244,206,133))
        if 18 <= t < 21:
            d.rectangle((64,201,70,204), fill=(232,190,119))
    elif t < 24:
        # The touch and moment of transformation.
        person(d,69,178,ROBE,SKIN,"touch")
        person(d,94,173,MESSENGER,(218,185,151),"touch",glow=True)
        pulse = (i % 4)
        d.rectangle((76-pulse,198-pulse,87+pulse,209+pulse), outline=(255,230,156), width=2)
    else:
        # Jacob walks into the sunrise, changed and limping.
        jx = int(66 + (t-24)*3)
        person(d,jx,178,ROBE,SKIN,"stand",limp=True)
        d.rectangle((jx-4,213,jx+19,215), fill=(222,178,122))

    # Story captions, large enough for a phone screen.
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 9)
    except: font = ImageFont.load_default()
    if t < 4:
        caption = "A NIGHT THAT CHANGED JACOB"
    elif t < 12:
        caption = "HE WRESTLED THROUGH THE NIGHT"
    elif t < 20:
        caption = "I WILL NOT LET YOU GO..."
    elif t < 24:
        caption = "YOUR NAME WILL BE ISRAEL"
    else:
        caption = "HE WALKED AWAY CHANGED"
    box = d.textbbox((0,0),caption,font=font)
    tw = box[2]-box[0]
    d.rectangle((4,8,W-4,27), fill=(8,13,28))
    d.text(((W-tw)//2,12),caption,font=font,fill=WHITE)
    if t > 26:
        ref = "GENESIS 32:22-32"
        d.rectangle((35,287,145,305), fill=(8,13,28))
        rb=d.textbbox((0,0),ref,font=font); rw=rb[2]-rb[0]
        d.text(((W-rw)//2,291),ref,font=font,fill=(255,221,158))
    return img.resize((540,960), Image.Resampling.NEAREST)

for n in range(FRAMES):
    make_frame(n).save(f"{OUT}/frame_{n:04d}.png")

# Gentle original ambient pad, synthesized locally (no third-party music).
rate=22050
with wave.open(f"{OUT}/ambient.wav","w") as wav:
    wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(rate)
    for n in range(rate*SECONDS):
        sec=n/rate
        fade=min(1,sec/2,(SECONDS-sec)/2)
        chord=(math.sin(2*math.pi*110*sec)+.55*math.sin(2*math.pi*164.81*sec)+.35*math.sin(2*math.pi*220*sec))
        sample=int(2400*fade*chord/1.9)
        wav.writeframesraw(struct.pack("<h",sample))

subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",f"{OUT}/frame_%04d.png","-i",f"{OUT}/ambient.wav","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-b:a","96k","-shortest","-movflags","+faststart","-vf","scale=540:960","jacob-pixel-animation.mp4"],check=True)
print("Created jacob-pixel-animation.mp4")
