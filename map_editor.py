import traceback
import sys
import os
from functools import partial

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1' #hiding pygame greeting console output

import pygame
import json
from engine import *
import tkinter
import tkinter.filedialog
import tkinter.messagebox as mb
from tkinter import scrolledtext as stxt
from tkinter import ttk
import random
import time
import shutil
import zipfile
import threading
import copy

def show_exception_and_exit(exc_type, exc_value, tb):
    text = traceback.format_exc()
    show_error(text = text)

sys.excepthook = show_exception_and_exit
sys.unraisablehook = show_exception_and_exit #configuring python, so it wouldn`t just crash when a error occures

args = sys.argv

def show_error(title = 'Ooops!', text = 'ERROR'):
    top = tkinter.Tk()
    top.title(title)
    top.withdraw()
    mb.showerror(title, text) #function to show python tracebacks
    top.destroy()
    
try:
    a = open('map_editor/config.json', 'r')
    setts = json.loads(a.read())
    a.close()

    a = open(setts['blk_file_path'], 'r')
    blk_data = json.loads(a.read())
    a.close()
    
    a = open(setts['ent_file_path'], 'r', encoding = "UTF-8")
    ent_data = json.loads(a.read())
    a.close()

    a = open(setts['help_file_path'], 'r', encoding = "UTF-8")
    TXT_HELP = a.read()
    a.close()

    a = open(setts['lang_file'], 'r', encoding = "UTF-8")
    lang = json.loads(a.read())
    a.close()
except:
    text = traceback.format_exc()
    show_error(text = text)


IDMAP = {} #id map contains block data according to is ID. this was made to optimise world data
ENTMAP = {} #same map but for entities
TEXTURES = {} #textures data
ENT_TEXTURES = {}
ENTITY = [] #entity list
WIRES = [] #wires list

for key, value in blk_data.items():
    IDMAP[int(value['id'])] = value

for key, value in ent_data.items():
    ENTMAP[int(value['id'])] = value

WIDTH = setts['WIDTH']
HEIGHT = setts['HEIGHT'] #screen size in pixels
W_w = setts['world_size'] #map size
W_h = W_w
ENT_COUNTER = 0

T_SIZE = setts['texture_size'] #variable than defines texture size. T_SIZE can change during program work, but T_SIZE_ORIG can`t
T_SIZE_ORIG = setts['texture_size']

X0, Y0 = 0,0

CAM_X = 0
CAM_Y = 0 #camera position

def merge_dicts(dictOne, dictTwo):
    dictThree = dictOne.copy()
    dictThree.update(dictTwo)
    return dictThree

def open_file(title = 'Открытие'):
    top = tkinter.Tk()
    top.title(title) #function for beautiful GUI file opening
    top.withdraw()
    file_name = tkinter.filedialog.askopenfilename(parent=top)
    top.destroy()
    return file_name

def save_file(title = 'Открытие'):
    top = tkinter.Tk()
    top.title(title)
    top.withdraw() #function for beautiful GUI file saving
    file_name = tkinter.filedialog.asksaveasfilename(parent=top)
    top.destroy()
    return file_name

def compile_map(name): #the heart of CMF system, the compiler
    print(lang['compiler']['start'].format(time.ctime()[11:19]))
    
    try:
        os.mkdir('maps_raw/' + name)
    except:
        shutil.rmtree('maps_raw/' + name) #check if folder with same name exists, then delete it
        os.mkdir('maps_raw/' + name)
        
    prefix = 'maps_raw/' + name + '/' #defining prefix
        
    FILES = []

    print(lang['compiler']['dir_copy'].format(time.ctime()[11:19]))
    
    for key, value in TEXTURES.items():
        path = key
        try:
            if path != False:
                os.makedirs(prefix + '/'.join(path.split('/')[0:-1]))
                print('\t' + prefix + '/'.join(path.split('/')[0:-1])) #copying all directories hierarhy
        except:
            pass

    for x in range(W_w):
        for y in range(W_h):
            j = ent.get(x, y)
            if type(j) != int:
                if j['name'] != 'ent_noname':
                    for key, value in j.items():
                        try:
                            if os.path.isfile(str(value)):
                                os.makedirs(prefix + '/'.join(value.split('/')[0:-1]))
                                print('\t' + prefix + '/'.join(value.split('/')[0:-1]))
                        except:
                            pass
                        
                    for key, value in j['attributes'].items():
                        try:
                            if os.path.isfile(str(value)):
                                os.makedirs(prefix + '/'.join(value.split('/')[0:-1])) #copying all directories hierarhy
                                print('\t' + prefix + '/'.join(value.split('/')[0:-1]))
                        except:
                            pass

    for key, value in ent_data.items():
        try:
            os.makedirs(prefix + '/'.join(value['image'].split('/')[0:-1])) #copying all directories hierarhy
        except:
            pass

    print(lang['compiler']['file_copy'].format(time.ctime()[11:19]))

    for key, value in TEXTURES.items():
        path = key
        try:
            shutil.copy(str(path), prefix + path)
            print('\t' + path + ' > ' + prefix + path) #the code below cheking all data for files and then copying it
            FILES.append(path)
        except:
            print(lang['compiler']['failed_copy'] + prefix + path)

    for x in range(W_w):
        for y in range(W_h):
            j = ent.get(x, y)
            if type(j) != int:
                if j['name'] != 'ent_noname':
                    for key, value in j.items():
                        try:
                            shutil.copy(str(value), prefix + str(value))
                            print('\t' + str(value) + ' > ' + prefix + str(value))
                            FILES.append(prefix + str(value))
                        except:
                            pass

                    for key, value in j['attributes'].items():
                        try:
                            shutil.copy(str(value), prefix + str(value))
                            print('\t' + str(value) + ' > ' + prefix + str(value))
                            FILES.append(prefix + str(value))
                        except:
                            pass
                    
    for key, value in ent_data.items():
        if os.path.isfile(value['image']):
            FILES.append(value['image'])
            shutil.copy(str(value['image']), prefix + str(value['image']))

    print(lang['compiler']['blocks_copy'].format(time.ctime()[11:19]))
    shutil.copy(setts['blk_file_path'], prefix + 'blocks.json') #writing main map data to file
    FILES.append(prefix + 'blocks.json')
    
    print(lang['compiler']['map_patch'].format(time.ctime()[11:19]))
    a = open(prefix + 'world.json', 'w')
    FILES.append(prefix + 'world.json')

    PLPS = []

    x, y = 0, 0
    for x in range(W_w):
        for y in range(W_h):
            if type(ent.get(x, y)) != int:
                if ent.get(x, y)['func'] != False:
                    if ent.get(x, y)['func'] == 'spawnpoint': #defining player`s spawn positions
                        PLPS.append([x, y])

    ENTITY = []

    for x in range(W_w):
        for y in range(W_h):
            unit = ent.get(x,y)
            if type(unit) != int:
                if unit['name'] != 'ent_noname': #defining all map entities
                    ENTITY.append(unit)

    idmap_ = {}

    for key, value in IDMAP.items():
        idmap_[int(key)] = value
    
    data = {
        'player_pos':'none',
        'world':world.arr,
        'idmap':idmap_,
        'world_size':W_w, #patching all map data to this dictionary
        'entity':ENTITY,
        'player_pos':PLPS,
        'ent_data':ent_data,
        'wire':WIRES,
        'cam':[CAM_X, CAM_Y]
    }

    json.dump(data, a, separators=(',', ':')) #and dumping it to JSON
    a.close()

    arh = zipfile.ZipFile('maps/' + name + '.cmf', 'w')
    
    for root, dirs, files in os.walk('maps_raw/'+name): #copying all defined files
        for file in files:
            print(lang['compiler']['added'] + ''.join(os.path.join(root, file).split(name)[1][1:]))
            arh.write(prefix + ''.join(os.path.join(root, file).split(name)[1][1:]),  arcname=''.join(os.path.join(root, file).split(name)[1][1:]))

    arh.close()

    print(lang['compiler']['done'].format(time.ctime()[11:19]))

def load_map(out = False): #function to load CMF files
    global world, IDMAP, TEXTURES, blk_data, W_w, W_h, WIRES, CAM_X, CAM_Y, ent

    ent.fill(0) #clearing all entities
    
    path = open_file() #get the path of CMF
    if path != '':
        name = path.split('/')[-1].split('.')[0] #defining the map name
        arh = zipfile.ZipFile(path, 'r') #opening zip (yes, CMF is actually a zip)
        try:
            os.mkdir('maps_raw/' + name)
        except:
            shutil.rmtree('maps_raw/' + name) #if a folder with this name already exist, delete it
            os.mkdir('maps_raw/' + name)

        prefix = 'maps_raw/' + name + '/' #defining prefix for all file paths in map
            
        for file_info in arh.infolist():
            if out:
                print(lang['loader']['exctracted']+file_info.filename) #exctracting map files in temporary folder
            try:
                arh.extract(file_info.filename, 'maps_raw/'+name)
            except:
                pass

        a = open(prefix + 'world.json', 'r') #reading main map data
        data = json.loads(a.read())
        a.close()

        try:
            W_w, W_h = data['world_size'], data['world_size'] #defining world size
        except:
            print(lang['loader']['world_size_failed'])
            W_w, W_h = 128, 128

        world = arr2.arr2(W_w, W_h, 0) #recreating the world
        world.arr = data['world']
        ent = arr2.arr2(W_w, W_h, ent_data['ent_noname'])
        
        for j in data['entity']:
            ent.put(j['pos_x'], j['pos_y'], j) #loading entities

        a = open(prefix + 'blocks.json', 'r') #reding map blocks info
        blk_data = json.loads(a.read())
        a.close()

        for key, value in blk_data.items():
            if value['image'] != False:
                TEXTURES[prefix + value['image']] = image(value['image']) #defining blocks textures

        for key, value in blk_data.items():
            if value['image'] != False:
                unit = value
                unit['image'] = prefix + value['image'] #defining blocks id map
                IDMAP[int(value['id'])] = unit
            else:
                IDMAP[int(value['id'])] = value

        try:
            WIRES = data['wire']
        except:
            print(lang['loader']['wire_failed']) #loading wire data
            WIRES = []

        try:
            CAM_X, CAM_Y = data['cam'] #loading camera position info
        except:
            print(lang['loader']['camera_failed'])

        pygame.display.set_caption(setts['TITLE'] + ' - ' + name + '.cmf')

def load_map_by_file(path): #outdated function that loads map by given path
    global world, IDMAP, TEXTURES, blk_data, W_w, W_h, ent
    if os.path.isfile(path):
        name = 'maps_raw/' + os.getcwd().join(path.split(os.getcwd())[1:])[1:].split('.')[0]

        arh = zipfile.ZipFile(path, 'r')
        try:
            os.mkdir(name)
        except:
            shutil.rmtree(name)
            os.mkdir(name)

        prefix = 'maps_raw/' + os.getcwd().join(path.split(os.getcwd())[1:])[1:].split('.')[0] + '/'
            
        for file_info in arh.infolist():
            #print(file_info.filename)
            try:
                arh.extract(file_info.filename, name)#+file_info.filename.split('/')[-1])
            except:
                pass

        a = open(prefix + 'world.json', 'r')
        data = json.loads(a.read())
        a.close()

        W_w, W_h = data['world_size'], data['world_size']

        world.arr = data['world']
        ent = arr2.arr2(W_w, W_h, ent_data['ent_noname'])

        for j in data['entity']:
            ent.put(j['pos_x'], j['pos_y'], j)

        a = open(prefix + 'blocks.json', 'r')
        blk_data = json.loads(a.read())
        a.close

        for key, value in blk_data.items():
            if value['image'] != False:
                TEXTURES[prefix + value['image']] = image(value['image'])

        for key, value in blk_data.items():
            if value['image'] != False:
                unit = value
                unit['image'] = prefix + value['image']
                IDMAP[int(value['id'])] = unit
            else:
                IDMAP[int(value['id'])] = value

def cam(x, y):
    global CAM_X, CAM_Y
    CAM_X, CAM_Y = x, y

def fg(ID):
    global fg_block         #some "commands" for old console
    fg_block = ID  

def bg(ID):
    global bg_block
    bg_block = ID

def console(): #old console thread function
    while c_loop:
        com = str(input('Python >>> '))
        try:
            exec(com, globals())
        except Exception as ex:
            text = traceback.format_exc()
            show_error(text = text)

def block(x, y, ID):
    try:
        world.put(x, y, ID)
    except:
        pass
    
def image(path): #returns pygame surface image
    try:
        return pygame.image.load(path)
    except:
        print(lang['misc']['image_failed'].format(path))

def invert(var):
    if var:
        return False
    elif not var:
        return True

def get_block(ID):
    try:
        return IDMAP[ID]
    except:
        print(lang['misc']['block_failed'].format(ID))

def get_image(ID):
    try:
        return TEXTURES[get_block(ID)['image']]
    except:
        return EMO

def exist(key, dic):
    try:
        dic[key]
        return True
    except:
        return False

def get_ent_image(ID):
    try:
        return ENT_TEXTURES[get_entity(ID)['image']]
    except:
        return EMO

def get_entity(ID):
    try:
        return ENTMAP[ID]
    except:
        pass

def draw(): #main render function
    x, y = 0, 0
    for x in range(SCR_X):
        for y in range(SCR_Y):
            if CAM_X + x >= 0 and CAM_X + x < W_w and CAM_Y + y >= 0 and CAM_Y + y < W_h:
                if world.get(CAM_X + x, CAM_Y + y) != setts['nodraw_id']:
                    map_layer.blit(pygame.transform.scale(get_image(world.get(CAM_X + x, CAM_Y + y)), (T_SIZE, T_SIZE)), (X0 + x*T_SIZE, Y0 + y*T_SIZE)) #render block texture
            y += 1
        x += 1

def draw_entity(): #entity render
    x, y = 0, 0
    for x in range(SCR_X):
        for y in range(SCR_Y):
            try:
                unit = ent.get(CAM_X + x, CAM_Y + y)
                if unit['name'] != 'ent_noname':
                    info_layer.blit(Consolas.render(unit['attributes']['name'], False, (255,255,255)), (X0 + x*T_SIZE, Y0 + y*T_SIZE - 20))
                    
                    if unit['func'] == 'texture_resizable':
                        map_layer.blit(pygame.transform.scale(image(unit['attributes']['image']), (T_SIZE*unit['attributes']['size_x'], T_SIZE*unit['attributes']['size_y'])),(unit['attributes']['pad_x'] + X0 + x*T_SIZE, unit['attributes']['pad_y'] + Y0 + y*T_SIZE))
                        pygame.draw.rect(info_layer, (255,255,255), (X0 + x*T_SIZE, Y0 + y*T_SIZE, T_SIZE, T_SIZE), 2)

                    elif unit['func'] == 'npc':
                        map_layer.blit(pygame.transform.scale(image(unit['attributes']['skin']), (T_SIZE, T_SIZE)), (X0 + x*T_SIZE, Y0 + y*T_SIZE))

                    elif unit['func'] == 'snd_ambient':
                        pygame.draw.circle(info_layer, (0,38,255), (X0 + x*T_SIZE + T_SIZE//2, Y0 + y*T_SIZE + T_SIZE//2), unit['attributes']['radius']*T_SIZE, 2)
                        map_layer.blit(pygame.transform.scale(get_ent_image(ent.get(CAM_X + x, CAM_Y + y)['id']), (T_SIZE, T_SIZE)), (X0 + x*T_SIZE, Y0 + y*T_SIZE))
                        info_layer.blit(Consolas.render(unit['attributes']['sound_file'].split('/')[-1], False, (0, 38, 255)), (X0 + x*T_SIZE, Y0 + y*T_SIZE - 40))

                    elif unit['func'] == 'snd_point':
                        pygame.draw.circle(info_layer, (0,38,255), (X0 + x*T_SIZE + T_SIZE//2, Y0 + y*T_SIZE + T_SIZE//2), unit['attributes']['radius']*T_SIZE, 2)
                        map_layer.blit(pygame.transform.scale(get_ent_image(ent.get(CAM_X + x, CAM_Y + y)['id']), (T_SIZE, T_SIZE)), (X0 + x*T_SIZE, Y0 + y*T_SIZE))
                        info_layer.blit(Consolas.render(unit['attributes']['sound_file'].split('/')[-1], False, (0, 38, 255)), (X0 + x*T_SIZE, Y0 + y*T_SIZE - 40))
                        
                    else:
                        map_layer.blit(pygame.transform.scale(get_ent_image(ent.get(CAM_X + x, CAM_Y + y)['id']), (T_SIZE, T_SIZE)), (X0 + x*T_SIZE, Y0 + y*T_SIZE))

            except:
                continue
            y += 1
        x += 1


def draw_blk_choose(): #function to draw blocks preview
    x, y = 0, 0
    for x in range(WIDTH//(T_SIZE_ORIG+5)):
        for y in range(HEIGHT//(T_SIZE_ORIG+5)):
            #print(x, y)
            if blk_arr.get(x, y) != False:
                pygame.draw.rect(screen, (50,50,50), (x*(T_SIZE_ORIG+5), 45 + y*(T_SIZE_ORIG+5), 30,30))
                screen.blit(get_image(blk_arr.get(x, y)), (x*(T_SIZE_ORIG+5)+5, 45 + y*(T_SIZE_ORIG+5)+5))
                if [ax, ay] == [x, y]:
                    pygame.draw.rect(screen, (200,200,200), (x*(T_SIZE_ORIG+5)+5, 50 + y*(T_SIZE_ORIG+5), 20,20), 2)

                m_uni = get_block(m_unit)

                pygame.draw.rect(screen, (70,70,70), (mx+8, my+8, len(m_uni['name'] + '({})'.format(m_uni['id']))*setts['font_size']//1.8+2, setts['font_size']+2))
                name_text = Consolas.render(m_uni['name'] + '({})'.format(m_uni['id']), False, (255,255,255))
                screen.blit(name_text, (mx+10, my+10))
                    
            y += 1
        x += 1

def draw_ent_choose(): #function to draw entity preview
    x, y = 0, 0
    for x in range(WIDTH//(T_SIZE_ORIG+5)):
        for y in range(HEIGHT//(T_SIZE_ORIG+5)):
            if ent_arr.get(x, y)['name'] != 'ent_noname':
                pygame.draw.rect(screen, (50,50,50), (x*(T_SIZE_ORIG+5), 45 + y*(T_SIZE_ORIG+5), 30,30))
                screen.blit(get_ent_image(ent_arr.get(x, y)['id']), (x*(T_SIZE_ORIG+5)+5, 45 + y*(T_SIZE_ORIG+5)+5))
                
                if [ax, ay] == [x, y]:
                    pygame.draw.rect(screen, (200,200,200), (x*(T_SIZE_ORIG+5)+5, 50 + y*(T_SIZE_ORIG+5), 20,20), 2)

                m_uni = m_unit

                pygame.draw.rect(screen, (70,70,70), (mx+8, my+8, len(m_uni['name'] + '({})'.format(m_uni['id']))*setts['font_size']//1.8+2, setts['font_size']+2))

                if exist("desc", m_uni):
                    pygame.draw.rect(screen, (70,70,70), (mx+8, my+24, (len(m_uni['desc']) + 1.5)*setts['font_size']//1.8+2, setts['font_size']+2))
                    desc_text = Consolas.render(m_uni['desc'], False, (255,255,255))
                    screen.blit(desc_text, (mx+10, my+10+setts['font_size']))
                
                name_text = Consolas.render(m_uni['name'] + '({})'.format(m_uni['id']), False, (255,255,255))
                screen.blit(name_text, (mx+10, my+10))
                    
            y += 1
        x += 1

def help_window():
    root = tkinter.Tk()
    root.title(lang['windows']['help'])
    root.geometry('600x500')

    txt = stxt.ScrolledText(root, width = 70, height = 30, wrap = 'word')
    txt.place(x = 10, y = 10)
    txt.insert(1.0, TXT_HELP)
    txt['state'] = 'disable'
    
    root.mainloop()

#help_window()

def property_editor(unit): #entity property editor
    global ax1, ay1, ent
    def appl():
        for var in ENTRYS:
            dic = unit
            DATA[var] = globals()[var].get()
            #print(DATA[var])

            for key, value in DATA.items():
                try:
                    DATA[key] = int(value)
                except:
                    DATA[key] = str(value)
            
            for key, value in DATA.items():
                DATA1['_'.join(key.split('_')[2:])] = value

        unit2 = copy.deepcopy(unit)
        unit2['attributes'] = copy.deepcopy(DATA1)

        for a in ENTITY:
            if a['pos_x'] == unit['pos_x'] and a['pos_y'] == unit['pos_y'] and a['name'] == unit['name']:
                ENTITY.remove(a)
                ENTITY.append(unit2)
        
        ent.put(ax1, ay1, unit2)
        #print(ent.get(ax1,ay1)['attributes'])

        root.destroy()

    def default():
        attrs = copy.deepcopy(ent_data[unit['name']]['attributes'])
        for key, value in attrs.items():
            exec('var_entry_{}.delete(0, tkinter.END)'.format(key))
            exec('var_entry_{}.insert(0, value)'.format(key))

    #print(unit)
    dic = {}
    
    attrs = unit['attributes']
    #print(attrs)

    LEN = 0
    TXTS = [0]
    DATA = {}
    DATA1 = {}
    
    for key, value in attrs.items():
        LEN += 1
        TXTS.append(len(key))

    MAX = max(TXTS)
    axx1, ayy1 = ax1, ay1
    
    root = tkinter.Tk()
    root.geometry('{}x{}'.format(10 + MAX*11 + 10 + 200 + 30,LEN*40 + 60))
    root.title(unit['name'] + ' ({},{})'.format(axx1, ayy1))
    root.resizable(width=False, height=False)

    if LEN == 0:
        root.geometry('300x200')
        a = tkinter.Label(text = lang['misc']['ent_noattrs'])
        a.place(x = 50, y = 50)
    else:

        ENTRYS = []

        y = 20

        for key, value in attrs.items():
            wired = False
            wired_to = {'pos_x':0, 'pos_y':0, "attr":'none'}
            for wire in WIRES:
                if wire[0]['pos_x'] == unit['pos_x'] and wire[0]['pos_y'] == unit['pos_y'] and wire[0]['attr'] == key:
                    wired = True
                    wired_to = wire

            if not wired:
                globals()['var_entry_' + key] = tkinter.Entry(width = 40)
                exec('var_entry_{}.place(x={},y={})'.format(key, MAX*7 + 20, y))
                exec('var_entry_{}.insert(0, value)'.format(key))
            else:
                globals()['var_wirelabel_{}'.format(key)] = tkinter.Label(root, fg = 'red', text='Wired to {} ({}, {})({})'.format(ent.get(wired_to[1]['pos_x'], wired_to[1]['pos_y'])['attributes']['name'], wired_to[1]['pos_x'], wired_to[1]['pos_y'], wired_to[1]['attr']))
                exec('var_wirelabel_{}.place(x = {}, y = {})'.format(key, MAX*7+20, y))
                globals()['var_wirelabel_{}_1'.format(key)] = tkinter.Label(root, fg = 'red', text = '({})'.format(ent.get(wired_to[1]['pos_x'], wired_to[1]['pos_y'])['attributes'][wired_to[1]['attr']]))
                exec('var_wirelabel_{}_1.place(x = {}, y = {})'.format(key, MAX*7+20, y+15))


            globals()['var_label_' + key] = tkinter.Label(text = key + ':')
            exec('var_label_{}.place(x={},y={})'.format(key, 10, y))
            ENTRYS.append('var_entry_{}'.format(key))
            y += 40

        if unit['attributes']['name'] == '0':
            exec('var_entry_name.delete(0, tkinter.END)')
            exec('var_entry_name.insert(0, "{}")'.format('entity_{}'.format(ENT_COUNTER)))

        apply = tkinter.Button(root, text = 'Apply', command = appl)
        apply.place(x = 10, y = y)

        cancel = tkinter.Button(root, text = 'Default', command = default)
        cancel.place(x = 60, y = y)
        
    root.mainloop()

def view_vars():
    print(pretty_out.box(pretty_out.listing(VARS)))

pygame.init()
pygame.mixer.init()
if setts['fullscreen']:
    screen = pygame.display.set_mode((0,0),pygame.RESIZABLE)
else:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
map_layer = pygame.Surface((WIDTH, HEIGHT))
pygame.display.set_caption(setts['TITLE'])
pygame.display.set_icon(image('map_editor/icon.png'))
clock = pygame.time.Clock()

Consolas = pygame.font.Font('map_editor/consolas.ttf', setts['font_size'])

info_layer = pygame.Surface((WIDTH, HEIGHT))
info_layer.set_colorkey(setts['colorkey'])

for key, value in blk_data.items():
    if value['image'] != False:
        TEXTURES[value['image']] = image(value['image']) #patching textures info

for key, value in ent_data.items():
    if value['image'] != False:
        ENT_TEXTURES[value['image']] = image(value['image'])
        
SCR_X = WIDTH//T_SIZE  #screen size in blocks
SCR_Y = HEIGHT//T_SIZE

world = worldgen.CaveChunk(W_w, W_h, W_w*W_h*3, 3, 1, 2, 3) #generating default world
blk_arr = arr2.arr2(WIDTH//(T_SIZE_ORIG+5), HEIGHT//(T_SIZE_ORIG+5), False)
ent_arr = arr2.arr2(WIDTH//(T_SIZE_ORIG+5), HEIGHT//(T_SIZE_ORIG+5), ent_data['ent_noname'])
ent = arr2.arr2(W_w, W_h, ent_data['ent_noname'])

EMO = image('map_editor/missing.png') #loading emo-texture for replacing undefined images

x, y = 0, 0
for key, value in blk_data.items():
    x += 1
    if x == WIDTH // (T_SIZE+10):
        x = 0
        y += 1
        if y == HEIGHT // (T_SIZE+10):
            y = 0
            break
    blk_arr.put(x, y, value['id'])             #loading entities and blocks to 2d arrays for preview menus

x, y = 0, 0
for key, value in ent_data.items():
    x += 1
    if x == WIDTH // (T_SIZE+10):
        x = 0
        y += 1
        if y == HEIGHT // (T_SIZE+10):
            y = 0
            break

    ent_arr.put(x, y, value)

running = True
c_loop = True

fg_drawing = False
bg_drawing = False
blk_choose = False #some state variables
ent_choose = False
tool_choose = False

full_view = False

fg_block = 3
bg_block = 2

brackets = image('map_editor/block_br_black.png')
brackets_wrong = image('map_editor/wrong.png')

ax, ay = CAM_X, CAM_Y
ax1, ay1 = ax, ay
mx, my = 0, 0

MOVE = '' 

move_right = False
move_left = False  #variables to describe camera movement
move_up = False
move_down = False

WMOD = False

LINE_POS1 = [0,0]
LINE_POS2 = [0,0]
line_c = 0

RECT_POS1 = [0,0]
RECT_POS2 = [0,0]
rect_c = 0

C_CENTER = [0,0]  #variables to describe primitives drawing (circle, rect and line)
C_RADIUS = 0
C_WIDTH = 1
c_c = 0

C_POS_ORIG = []
T_SIZE_1 = 20
SCR_SCALE_1 = []

move_counter = 0
move_speed = setts['move_speed']

m_unit = 0
fg_ent = False
VARS = {}

ON_WIRE = False

TEST_ARR = [[4,4,4,4],
            [4,2,2,4],
            [4,2,2,4],
            [4,4,4,4]]

full_counter = 0

map_rect = pygame.rect.Rect((0,0, SCR_X*T_SIZE, SCR_Y*T_SIZE))
map_r = pygame.rect.Rect((0,0,WIDTH,HEIGHT-T_SIZE_ORIG*2))

#threading.Thread(target=console).start()

if len(args) > 1:
    if os.path.isfile(args[1]):
        load_map_by_file(args[1])
        #T_SIZE = WIDTH//W_w
        #full_view = True

def comp(): #compilation window
    def f():
        global NAM
        NAM = a.get()
        root.destroy()
        compile_map(NAM)
        
    NAM = 'noname'
    root = tkinter.Tk()
    root.geometry("300x60")
    root.title(lang['windows']['compiler'])
    root.resizable(width=False, height=False)
    a = tkinter.Entry(root)
    a.place(x = 20, y = 21)
    b = tkinter.Label(root, text = lang['gui']['map_name'])
    b.place(x = 20, y = 0)
    c = tkinter.Button(root, command = f, text = lang['gui']['compile'])
    c.place(x = 150, y = 20)
    root.mainloop()

def set_wire_mode():
    global WMOD
    if WMOD:
        WMOD = False
    elif not WMOD:
        WMOD = True

def wire_editor(unit): #wiring menu
    global ON_WIRE, ax1, ay1

    def on_wire(unit, key):
        global ON_WIRE
        #print(key) #wiring first entity(input)
        ON_WIRE = copy.deepcopy({'pos_x':ax1, 'pos_y':ay1, 'attr':key})
        root.destroy()

    def on_wire2(unit, key):
        global ON_WIRE
        #print(key)  #wiring second entity(output)
        WIRES.append([ON_WIRE, {'pos_x':ax1, 'pos_y':ay1, 'attr':key}])
        ON_WIRE = False
        root.destroy()

    def unwire(wired_to):
        WIRES.remove(wired_to)
        root.destroy()
    
    if ON_WIRE == False:
        dic = {}
    
        attrs = unit['attributes']
        #print(attrs)

        LEN = 0
        TXTS = [0]
        DATA = {}
        DATA1 = {}
        
        for key, value in attrs.items():
            LEN += 1
            TXTS.append(len(key))

        #print(TXTS)

            
        MAX = max(TXTS)
        axx1, ayy1 = ax1, ay1
        
        root = tkinter.Tk()
        root.geometry('{}x{}'.format(10 + MAX*11 + 10 + 200 + 30,LEN*40+30))
        root.title(unit['name'] + ' ({},{})'.format(axx1, ayy1))
        root.resizable(width=False, height=False)

        if LEN == 0: #if entitys attributes list is empty, show this message
            root.geometry('300x200')                                        
            a = tkinter.Label(text = lang['misc']['ent_noattrs'])
            a.place(x = 50, y = 50)
        else:

            BUTTONS = []

            y = 20

            for key, value in attrs.items():
                wired = False
                wired_to = {'pos_x':0, 'pos_y':0, "attr":'none'}
                for wire in WIRES:
                    if wire[0]['pos_x'] == unit['pos_x'] and wire[0]['pos_y'] == unit['pos_y'] and wire[0]['attr'] == key:
                        wired = True
                        wired_to = wire

                if not wired:
                    globals()['var_button_' + key] = tkinter.Button(width = 30, text = 'Wire (input)',command = partial(on_wire, unit, key))
                    exec('var_button_{}.place(x={},y={})'.format(key, MAX*7 + 20, y))
                else:
                    globals()['var_button_' + key + '_1'] = tkinter.Button(width = 30,fg = 'red', text = 'Unwire',command = partial(unwire, wired_to))
                    exec('var_button_{}_1.place(x={},y={})'.format(key, MAX*7 + 20, y))
                    
                globals()['var_label_' + key] = tkinter.Label(text = key)
                exec('var_label_{}.place(x={},y={})'.format(key, 10, y))
                BUTTONS.append('var_button_{}'.format(key))
                y += 40


            root.mainloop()
    else:
        dic = {}
    
        attrs = unit['attributes']
        #print(attrs)

        LEN = 0
        TXTS = [0]
        DATA = {}
        DATA1 = {}
        
        for key, value in attrs.items():
            LEN += 1
            TXTS.append(len(key))

        #print(TXTS)

            
        MAX = max(TXTS)
        axx1, ayy1 = ax1, ay1
        
        root = tkinter.Tk()
        root.geometry('{}x{}'.format(10 + MAX*11 + 10 + 200 + 30,LEN*40+30))
        root.title(unit['name'] + ' ({},{})'.format(axx1, ayy1))
        root.resizable(width=False, height=False)

        if LEN == 0:
            root.geometry('300x200')
            a = tkinter.Label(text = lang['gui']['ent_noattrs'])
            a.place(x = 50, y = 50)
        else:

            BUTTONS = []

            y = 20

            for key, value in attrs.items():
                wired = False
                wired_to = {'pos_x':0, 'pos_y':0, "attr":'none'}
                for wire in WIRES:
                    if wire[0]['pos_x'] == unit['pos_x'] and wire[0]['pos_y'] == unit['pos_y'] and wire[0]['attr'] == key:
                        wired = True
                        wired_to = wire

                if not wired:
                    globals()['var_button_' + key] = tkinter.Button(width = 30, text = 'Wire (output)',command = partial(on_wire2, unit, key))
                    exec('var_button_{}.place(x={},y={})'.format(key, MAX*7 + 20, y))
                else:
                    globals()['var_button_' + key + '_1'] = tkinter.Button(width = 30, fg = 'red',text = 'Unwire',command = partial(unwire, wired_to))
                    exec('var_button_{}_1.place(x={},y={})'.format(key, MAX*7 + 20, y))
                    
                globals()['var_label_' + key] = tkinter.Label(text = key)
                exec('var_label_{}.place(x={},y={})'.format(key, 10, y))
                BUTTONS.append('var_button_{}'.format(key))
                y += 40

            root.mainloop()

def map_menu(): #generator properties window
    global world
    def f():
        global world, W_w, W_h, ent
        blk = list(map(int, ent_grass.get().split(',')))
        world = worldgen.CaveChunk(int(ent_size.get()), int(ent_size.get()), int(ent_moves.get()), blk[0], blk[1], blk[2], int(ent_smt.get()))
        W_w = int(ent_size.get())
        W_h = int(ent_size.get())
        ent = arr2.arr2(W_w, W_h, ent_data['ent_noname'])
        root.destroy()

    def g():
        global world, W_w, W_h, ent
        blk = list(map(int, ent_grass2.get().split(',')))
        world = worldgen.TunnelChunk(int(ent_size2.get()), int(ent_size2.get()), int(ent_moves2.get()), int(ent_tun.get()), blk[0], blk[1], blk[2], int(ent_smt2.get()))
        W_w = int(ent_size2.get())
        W_h = int(ent_size2.get())
        ent = arr2.arr2(W_w, W_h, ent_data['ent_noname'])
        root.destroy()

    def h():
        global world, W_w, W_h, ent
        world = arr2.arr2(int(ent_size3.get()), int(ent_size3.get()), int(ent_grass3.get()))
        W_w = int(ent_size3.get())
        W_h = int(ent_size3.get())
        ent = arr2.arr2(W_w, W_h, ent_data['ent_noname'])
        root.destroy()
    
    root = tkinter.Tk()
    root.geometry("300x230")
    root.title(lang['windows']['generator'])
    root.resizable(width=False, height=False)

    tabs = ttk.Notebook(root)

    tab_cave = ttk.Frame(tabs)
    tabs.add(tab_cave, text = lang['generator']['cavechunk'])

    tab_tunnel = ttk.Frame(tabs)
    tabs.add(tab_tunnel, text=lang['generator']['tunnelchunk'])

    tab_flat = ttk.Frame(tabs)
    tabs.add(tab_flat, text=lang['generator']['flat'])

    tabs.pack(expand=1, fill="both")
    
    l_size = tkinter.Label(tab_cave, text = lang['generator']['world_size'])
    l_size.place(x = 20, y = 10)
    ent_size = tkinter.Entry(tab_cave)
    ent_size.place(x = 130, y = 10)
    l_moves = tkinter.Label(tab_cave, text = lang['generator']['gen_moves'])
    l_moves.place(x = 20, y = 40)
    ent_moves = tkinter.Entry(tab_cave)
    ent_moves.place(x = 130, y = 40)
    l_grass = tkinter.Label(tab_cave, text = lang['generator']['gen_blocks'])
    l_grass.place(x = 20, y = 70)
    ent_grass = tkinter.Entry(tab_cave)
    ent_grass.place(x = 130, y = 70)
    l_smt= tkinter.Label(tab_cave, text = lang['generator']['smooth'])
    l_smt.place(x = 20, y = 100)
    ent_smt = tkinter.Entry(tab_cave)
    ent_smt.place(x = 130, y = 100)
    gen = tkinter.Button(tab_cave, text = lang['generator']['generate'], command = f)  #DONT LOOK HERE
    gen.place(x = 20, y = 130)

    l_size2 = tkinter.Label(tab_tunnel, text = lang['generator']['world_size'])        #THIS CODE DOES NOT EXIST
    l_size2.place(x = 20, y = 10)                   
    ent_size2 = tkinter.Entry(tab_tunnel)
    ent_size2.place(x = 130, y = 10)
    l_moves2 = tkinter.Label(tab_tunnel, text = lang['generator']['gen_moves'])
    l_moves2.place(x = 20, y = 40)
    ent_moves2 = tkinter.Entry(tab_tunnel)
    ent_moves2.place(x = 130, y = 40)
    l_grass2 = tkinter.Label(tab_tunnel, text = lang['generator']['gen_blocks'])
    l_grass2.place(x = 20, y = 70)
    ent_grass2 = tkinter.Entry(tab_tunnel)
    ent_grass2.place(x = 130, y = 70)
    l_tun= tkinter.Label(tab_tunnel, text = lang['generator']['tunnel_num'])
    l_tun.place(x = 20, y = 100)
    ent_tun = tkinter.Entry(tab_tunnel)
    ent_tun.place(x = 130, y = 100)
    l_smt2= tkinter.Label(tab_tunnel, text = lang['generator']['smooth'])
    l_smt2.place(x = 20, y = 130)
    ent_smt2 = tkinter.Entry(tab_tunnel)
    ent_smt2.place(x = 130, y = 130)

    gen2 = tkinter.Button(tab_tunnel, text = lang['generator']['generate'], command = g)
    gen2.place(x = 20, y = 160)

    l_size3 = tkinter.Label(tab_flat, text = lang['generator']['world_size'])
    l_size3.place(x = 20, y = 10)
    ent_size3 = tkinter.Entry(tab_flat)
    ent_size3.place(x = 130, y = 10)
    l_grass3 = tkinter.Label(tab_flat, text = lang['generator']['fill_block'])
    l_grass3.place(x = 20, y = 40)
    ent_grass3 = tkinter.Entry(tab_flat)
    ent_grass3.place(x = 130, y = 40)

    gen3 = tkinter.Button(tab_flat, text = lang['generator']['generate'], command = h)
    gen3.place(x = 20, y = 70)

    root.mainloop()

gui_layer = pygame.Surface((WIDTH, HEIGHT))
gui_layer.set_colorkey((69,69,69))
gui = GUI(gui_layer, 60, screen)
gui.colorkey = (69,69,69)

gui.draw.button(1, pos = (20,HEIGHT-30), scale=(100,20), size = 15, text = lang['gui']['load_map'], border_width = 2, function = load_map)

gui.draw.button(2, pos = (140,HEIGHT-30), scale=(100,20), size=15, text=lang['gui']['compile'], border_width=2, function = comp)

gui.draw.button(3, pos = (260,HEIGHT-30), scale=(100,20), size=15, text=lang['gui']['worldgen'], border_width=2, function = map_menu)

gui.draw.button(4, pos = (380, HEIGHT-30), scale=(100,20), size=15, text=lang['gui']['wiremode'], border_width=2, function= set_wire_mode)

while running:
    clock.tick(setts['FPS'])
    move_counter += 1
    screen.fill((0,0,0))
    info_layer.fill(setts['colorkey'])

    SCR_X = WIDTH//T_SIZE
    SCR_Y = HEIGHT//T_SIZE - 2 #recalculating this variables to allow dynamic resizing

    map_rect_ = pygame.Rect((0,0,SCR_X*T_SIZE,SCR_Y*T_SIZE))

    blk_prefix = get_block(fg_block)['name'].split('_')[0]

    if WMOD:
        gui.units[4]['fg'] = (255,0,0) #coloring "wiring mode" button
    else:
        gui.units[4]['fg'] = (0,0,0)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEMOTION:
            if map_rect.collidepoint(event.pos):
                mx, my = event.pos #defining mouse position

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                move_left = True
            elif event.key == pygame.K_d:
                move_right = True
            elif event.key == pygame.K_w: #camera movement
                move_up = True
            elif event.key == pygame.K_s:
                move_down = True

            if event.key == pygame.K_b:
                blk_choose = invert(blk_choose)

            if event.key == pygame.K_m:
                full_view = invert(full_view)
                if full_view:
                    C_POS_ORIG = [CAM_X, CAM_Y]
                    T_SIZE_1 = T_SIZE
                    CAM_X, CAM_Y = 0, 0
                    T_SIZE = min([HEIGHT//W_h, WIDTH//W_w]) #global map mode
                    SCR_SCALE_1 = [SCR_X, SCR_Y]
                    if T_SIZE == 0:
                        T_SIZE += 1

                    draw()
                    draw_entity()

                elif not full_view:
                    CAM_X, CAM_Y = C_POS_ORIG
                    T_SIZE = T_SIZE_1

            if event.key == pygame.K_l:
                line_c += 1
                if line_c == 1:
                    LINE_POS1 = [ax1, ay1]
                elif line_c == 2:
                    line_c = 0
                    LINE_POS2 = [ax1, ay1]
                    
                    points = point_engine.get_line(LINE_POS1[0], LINE_POS1[1], LINE_POS2[0], LINE_POS2[1]) #line
                    
                    for a in points:
                        try:
                            if a[0] >= 0 and a[0] < W_w and a[1] >= 0 and a[1] < W_h:
                                world.put(a[0], a[1], fg_block)
                        except:
                            pass

            if event.key == pygame.K_r:
                rect_c += 1
                if rect_c == 1:
                    RECT_POS1 = [ax1, ay1]
                elif rect_c == 2:
                    rect_c = 0
                    RECT_POS2 = [ax1, ay1]

                    points = point_engine.get_rect(RECT_POS1[0], RECT_POS1[1], RECT_POS2[0], RECT_POS2[1]) #rect

                    for a in points:
                        try:
                            if a[0] >= 0 and a[0] < W_w and a[1] >= 0 and a[1] < W_h:
                                world.put(a[0], a[1], fg_block)
                        except:
                            pass
            if event.key == pygame.K_c:
                c_c += 1
                if c_c == 1:
                    C_CENTER = [ax1, ay1]
                elif c_c == 2:
                    C_RADIUS = point_engine.way(C_CENTER, (ax1, ay1))
                    c_c = 0

                    points = point_engine.get_hollow_circle(C_CENTER[0], C_CENTER[1], C_RADIUS, C_WIDTH) #circle

                    for a in points:
                        try:
                            if a[0] >= 0 and a[0] < W_w and a[1] >= 0 and a[1] < W_h:
                                world.put(int(a[0]), int(a[1]), fg_block)
                        except:
                            pass

            if event.key == pygame.K_e:
                ent_choose = invert(ent_choose) #switching to entity list

            if event.key == pygame.K_DOWN:
                fg_block, bg_block = bg_block, fg_block #swapping blocks

            if event.key == pygame.K_p:
                if ent.get(ax1, ay1)['name'] != 'ent_noname':
                    try:
                        if fg_ent['attributes'] == {}:
                            print()
                            print(pretty_out.box(pretty_out.listing(ent.get(ax1, ay1)))) #block or entity info output
                        else:
                            dic = copy.deepcopy(ent.get(ax1, ay1))
                            del dic['attributes']
                            print()
                            print(pretty_out.box(pretty_out.listing(dic)))
                            print(lang['misc']['attributes'])
                            print(pretty_out.box(pretty_out.listing(ent.get(ax1, ay1)['attributes'])))
                    except:
                        pass
                else:
                    try:
                        print()
                        print(pretty_out.box(pretty_out.listing(get_block(m_unit))))
                    except:
                        pass
            if event.key == pygame.K_j:
                TEST_ARR = worldgen.room(30, 20, walls = [{12:100}, {10:100}, {11:100}, {9:100}], floor = [{8:50}, {13:1}]) #broken room generator
                
            if event.key == pygame.K_INSERT:
                world.paste(ax1, ay1, TEST_ARR)

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                move_left = False
            if event.key == pygame.K_d:
                move_right = False
            if event.key == pygame.K_w:  #camera movement
                move_up = False
            if event.key == pygame.K_s:
                move_down = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            #print(fg_ent)
            if event.button == 1 and map_r.collidepoint(event.pos):
                if blk_choose:
                    fg_block = m_unit
                    fg_ent = False
                    blk_choose = False
                
                elif ent_choose:
                    fg_ent = copy.deepcopy(ent_data[m_unit['name']])
                    ent_choose = False
                
                elif tool_choose:
                    pass

                elif full_view:
                    C_POS_ORIG = ax, ay
        
                else:
                    if fg_ent == False:
                        fg_drawing = True
                    else:
                        if ax1 >= 0 and ax1 < W_w and ay1 >= 0 and ay1 < W_h:
                            ENT_COUNTER += 1
                            enti = copy.deepcopy(ent_data[fg_ent['name']])
                            enti['pos_x'] = ax1
                            enti['pos_y'] = ay1
                            ent.put(ax1, ay1, enti)

            if event.button == 2 and map_r.collidepoint(event.pos):
                try:
                    if ent.get(ax1, ay1)['name'] == 'ent_noname':
                        fg_block = m_unit
                    else:
                        if not WMOD:
                            property_editor(ent.get(ax1, ay1))
                        else:
                            wire_editor(ent.get(ax1, ay1))
                            #print(WIRES)
                except:
                    pass
                
            if event.button == 3 and map_r.collidepoint(event.pos):
                if blk_choose:
                    bg_block = m_unit
                    blk_choose = False
                    
                elif ent_choose:
                    pass
                
                elif tool_choose:
                    pass

                elif ON_WIRE != False:
                    ON_WIRE = False
                    
                else:
                    if fg_ent == False:
                        bg_drawing = True
                    else:
                        if ax1 >= 0 and ax1 < W_w and ay1 >= 0 and ay1 < W_h:
                            ent.put(ax1, ay1, ent_data['ent_noname'])
                
            if event.button == 4 and map_r.collidepoint(event.pos):
                if c_c == 1:
                    C_WIDTH += 1
                
                else:
                    if T_SIZE > 1:
                        T_SIZE -= 1
                        #X0 = (WIDTH - T_SIZE*SCR_X)
                        #Y0 = (HEIGHT - T_SIZE*SCR_Y)

            if event.button == 5 and map_r.collidepoint(event.pos):
                if c_c == 1:
                    C_WIDTH -= 1
                else:
                    T_SIZE += 1
                    #X0 = (WIDTH - T_SIZE*SCR_X)
                    #Y0 = (HEIGHT - T_SIZE*SCR_Y)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                fg_drawing = False
            if event.button == 3:
                bg_drawing = False
    
    if blk_choose:
        ax, ay = (mx)//(T_SIZE_ORIG+5), (my-50)//(T_SIZE_ORIG+5) #some maths
        m_unit = blk_arr.get(ax, ay)
        pygame.draw.rect(screen, (255,255,255), (ax,ay,30,30), 2)
    elif ent_choose:
        ax, ay = (mx)//(T_SIZE_ORIG+5), (my-50)//(T_SIZE_ORIG+5)
        m_unit = ent_arr.get(ax, ay)
        pygame.draw.rect(screen, (255,255,255), (ax,ay,30,30), 2)
    elif tool_choose:
        pass
    else:
        ax, ay = mx//T_SIZE, my//T_SIZE
        ax1, ay1 = CAM_X + mx//T_SIZE, CAM_Y + my//T_SIZE
        try:
            m_unit = world.get(ax1, ay1)
        except:
            pass

    
    if move_counter*round(T_SIZE_ORIG/T_SIZE, 2) >= move_speed:
        move_counter = 0
        if move_up:
            CAM_Y -= 1
        if move_down:#camera movement
            CAM_Y += 1
        if move_right:
            CAM_X += 1
        if move_left:
            CAM_X -= 1

    if fg_drawing:
        try:
            if ax1 >= 0 and ax1 < W_w and ay1 >= 0 and ay1 < W_h:
                world.put(ax1, ay1, fg_block)
        except:
            pass

    if bg_drawing:
        try:
            if ax1 >= 0 and ax1 < W_w and ay1 >= 0 and ay1 < W_h:
                world.put(ax1, ay1, bg_block)
        except:
            pass
        
    if blk_choose:
        screen.fill((128,128,128))
        pygame.draw.rect(screen, (64,64,64), (0,0,WIDTH,40))
        screen.blit(Consolas.render(lang['misc']['blk_choose'], False, (255,255,255)), (20,15))
        draw_blk_choose()
        
    elif ent_choose:
        screen.fill((128,128,128))
        pygame.draw.rect(screen, (64,64,64), (0,0,WIDTH,40))
        screen.blit(Consolas.render(lang['misc']['ent_choose'], False, (255,255,255)), (20,15))
        draw_ent_choose()
    
    elif tool_choose:
        pass
    
    
    else:
        map_layer.fill((50,50,50))
    
        draw()
            
        draw_entity()

        pygame.draw.rect(info_layer, (50,50,50), (WIDTH - 50 - 10, HEIGHT - (HEIGHT-50-10), 45, 35))
        info_layer.blit(get_image(bg_block), (WIDTH - 40, HEIGHT - (HEIGHT-70)))

        if full_view:
            pygame.draw.rect(info_layer, (255,0,0), (C_POS_ORIG[0]*T_SIZE, C_POS_ORIG[1]*T_SIZE, SCR_SCALE_1[0]*T_SIZE, SCR_SCALE_1[1]*T_SIZE), 2)
        
        if bg_drawing:
            if not blk_choose and not ent_choose and not tool_choose:
                pygame.draw.rect(info_layer, (200,200,200), (WIDTH - 40, HEIGHT - (HEIGHT-70), T_SIZE_ORIG, T_SIZE_ORIG), 2)
                
        info_layer.blit(get_image(fg_block), (WIDTH - 55, HEIGHT - (HEIGHT-65)))
        
        if fg_drawing:
            if not blk_choose and not ent_choose and not tool_choose:
                pygame.draw.rect(info_layer, (200,200,200), (WIDTH - 55, HEIGHT - (HEIGHT-65), T_SIZE_ORIG, T_SIZE_ORIG), 2)
                
        pygame.draw.rect(info_layer, (30,30,30), (WIDTH - 50 - 10, HEIGHT - (HEIGHT-50-10), 45, 35), 2)
        
        cx, cy = CAM_X + SCR_X//2, CAM_Y + SCR_Y//2
        scal = round(T_SIZE_ORIG/T_SIZE, 2)
        info_layer.blit(Consolas.render(lang['gui']['cam_pos'].format(cx, cy), False, (255,255,255)), (20,20))
        info_layer.blit(Consolas.render(lang['gui']['map_size'].format(W_w, W_h), False, (255,255,255)), (20,35))
        info_layer.blit(Consolas.render(lang['gui']['scale'].format(scal), False, (255,255,255)), (20,50))
        
        if fg_ent != False:
            info_layer.blit(Consolas.render(lang['gui']['ent_mode'], False, (255,0,0)), (WIDTH//2,35))
        if full_view != False:
            info_layer.blit(Consolas.render(lang['gui']['full_view'], False, (255,0,0)), (WIDTH//3,35))

        if line_c == 1:
            pygame.draw.rect(info_layer, (255,0,0), ((LINE_POS1[0] - CAM_X)*T_SIZE, (LINE_POS1[1] - CAM_Y)*T_SIZE, T_SIZE, T_SIZE), 3)
            
            pygame.draw.line(info_layer, (255,255,255), ((LINE_POS1[0] - CAM_X)*T_SIZE + T_SIZE//2, (LINE_POS1[1] - CAM_Y)*T_SIZE + T_SIZE//2),
                             ((ax)*T_SIZE + T_SIZE//2, (ay)*T_SIZE + T_SIZE//2), 2)
            
            pygame.draw.rect(info_layer, (255,0,0), ((ax)*T_SIZE, (ay)*T_SIZE, T_SIZE, T_SIZE), 3)
            
        if rect_c == 1:
            delta_x = abs(ax1 - RECT_POS1[0])
            delta_y = abs(ay1 - RECT_POS1[1])
            
            x1, y1 = RECT_POS1
            x2, y2 = ax1, ay1

            tx, ty = (ax1-CAM_X)*T_SIZE, (ay1-CAM_Y)*T_SIZE
            
            if x2 > x1 and y2 > y1:
                x1, y1, x2, y2 = x1, y1, x2+1, y2+1
                tx, ty = (ax1-CAM_X+1)*T_SIZE, (ay1-CAM_Y+1)*T_SIZE
            
            if x2 > x1 and y2 < y1:
                x1, y1, x2, y2 = x1, y2, x2+1, y1
                tx, ty = (ax1-CAM_X+1)*T_SIZE, (ay1-CAM_Y)*T_SIZE
                
            if x2 < x1 and y2 < y1:
                x1, y1, x2, y2 = x2, y2, x1, y1
                tx, ty = (ax1-CAM_X)*T_SIZE, (ay1-CAM_Y-1)*T_SIZE
                
            if y2 > y1 and x2 < x1:
                x1, y1, x2, y2 = x2, y1, x1, y2+1
                tx, ty = (ax1-CAM_X+1)*T_SIZE, (ay1-CAM_Y-1)*T_SIZE
                
            pygame.draw.rect(info_layer, (255,0,0), ((x1-CAM_X)*T_SIZE, (y1-CAM_Y)*T_SIZE, (x2-x1)*T_SIZE, (y2-y1)*T_SIZE), 3)
            info_layer.blit(Consolas.render(f'{delta_x+1},{delta_y+1}', False, (255,0,0)), (tx, ty))

        if c_c == 1:
            pygame.draw.circle(info_layer, (255,0,0), ((C_CENTER[0] - CAM_X)*T_SIZE, (C_CENTER[1] - CAM_Y)*T_SIZE), 4, 2)
            pygame.draw.circle(info_layer, (255,0,0), ((C_CENTER[0] - CAM_X)*T_SIZE, (C_CENTER[1] - CAM_Y)*T_SIZE), C_RADIUS*T_SIZE, 2)
            pygame.draw.circle(info_layer, (255,0,0), ((C_CENTER[0] - CAM_X)*T_SIZE, (C_CENTER[1] - CAM_Y)*T_SIZE), (C_RADIUS - C_WIDTH)*T_SIZE, 2)

        if ON_WIRE != False:
            pygame.draw.line(info_layer, (255,0,0), ((ON_WIRE['pos_x'] - CAM_X)*T_SIZE + T_SIZE//2, (ON_WIRE['pos_y'] - CAM_Y)*T_SIZE + T_SIZE//2), (ax*T_SIZE+T_SIZE//2, ay*T_SIZE+T_SIZE//2), 2)

        for wire in WIRES:
            pos1 = ((wire[0]['pos_x'] - CAM_X)*T_SIZE + T_SIZE//2, (wire[0]['pos_y'] - CAM_Y)*T_SIZE + T_SIZE//2)
            pos2 = ((wire[1]['pos_x'] - CAM_X)*T_SIZE + T_SIZE//2, (wire[1]['pos_y'] - CAM_Y)*T_SIZE + T_SIZE//2)

            pygame.draw.line(info_layer, (200,0,0), pos1, pos2, 2)
            pygame.draw.circle(info_layer, (200,0,0), pos1, 3)
            pygame.draw.circle(info_layer, (200,0,0), pos2, 3)

            if ent.get(wire[0]['pos_x'], wire[0]['pos_y'])['name'] == 'ent_noname' or ent.get(wire[1]['pos_x'], wire[1]['pos_y'])['name'] == 'ent_noname':
                WIRES.remove(wire)  #check if one of wired entitys invalid, then remove the wire
                continue

            else:
                ent_in = copy.deepcopy(ent.get(wire[0]['pos_x'], wire[0]['pos_y']))
                ent_out = copy.deepcopy(ent.get(wire[1]['pos_x'], wire[1]['pos_y']))
                
                ent_in['attributes'][wire[0]['attr']] = ent_out['attributes'][wire[1]['attr']]
                ent.put(wire[0]['pos_x'], wire[0]['pos_y'], ent_in)
                
        #pygame.draw.rect(info_layer, (255,255,255), (ax*T_SIZE, ay*T_SIZE, get_image(fg_block).get_width(), get_image(fg_block).get_height()), 1)
            
        screen.blit(map_layer, (0,0))
        if ax1 >= 0 and ax1 < W_w and ay1 >= 0 and ay1 < W_h:
            screen.blit(pygame.transform.scale(brackets, (T_SIZE, T_SIZE)), (ax*T_SIZE, ay*T_SIZE))
        else:
            screen.blit(pygame.transform.scale(brackets_wrong, (T_SIZE, T_SIZE)), (ax*T_SIZE, ay*T_SIZE))

        pygame.draw.rect(info_layer, (255,0,0), ((0-CAM_X)*T_SIZE, (0-CAM_Y)*T_SIZE, W_w*T_SIZE, W_h*T_SIZE), 2)
            
        screen.blit(info_layer, (0,0))
        pygame.draw.rect(screen, (64,64,64), (0, HEIGHT-40, WIDTH, 40))
        gui.render()
        
    C_RADIUS = point_engine.way(C_CENTER, (ax1, ay1))
    map_rect.bottomright = (SCR_X*T_SIZE, SCR_Y*T_SIZE)
    
    pygame.display.flip()

pygame.quit()
