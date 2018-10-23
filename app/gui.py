# -*- coding:utf-8 -*-
"""
############################################################################
Panorama2BasalArea Beta 0.1: Calculate forest BA values from spherical
(panorama) images by manual tree selection.

Author: Howcanoe WANG

GUI class structure:
-- Pano2BA()
 |-- class MenuBar(pack='top')
 |-- self.progressbar(pack='bottom')
 |-- self.left_frame(pack='left')
 | |-- self.img_table(pack='top')
 | |-- self. btn_frame(pack='bottom')
 |   |-- self.add_img_btn(pack='left')
 |   |-- self.del_img_btn(pack='right')
 |-- self.right_frame(pack='right')
 | |-- self.tree_table(pack='right')
 |-- class ScrolledCanvas(pack='top')

############################################################################
"""
import os
from tkinter import Tk, Button, Menubutton, Menu, Canvas, Scrollbar, Label, Frame
from tkinter.simpledialog import askstring, askfloat
from tkinter.filedialog import asksaveasfilename, askopenfilename, askdirectory
from tkinter.messagebox import askokcancel, showwarning, askyesno, askyesnocancel
from tkinter.ttk import Treeview, Progressbar
from PIL import Image, ImageDraw
from PIL.ImageTk import PhotoImage
from PIL.ImageOps import equalize
from db import DataBase
from numpy import ones
from ba import plot_ba_calculator, max_baf


class Pano2BA(Tk):

    saved = True
    title_name = 'Panorama2BA'
    img_info = {'img_id': [], 'img_dir': [], 'img_name': [], 'width': [], 'height': [], 'baf': [], 'in_num': [], 'ba': []}
    tree_info = {'tree_id': [], 'left': [], 'right': [], 'width': [], 'state': []}

    def __init__(self):
        Tk.__init__(self)

        self.update_title()
        self.config(bg='white')
        self.protocol("WM_DELETE_WINDOW", self.quit_save_confirm)
        self.wm_state('zoomed')  # maximize windows

        self.w = self.winfo_width()
        self.h = self.winfo_height()

        # =====================
        #  creating components
        # =====================
        self.MenuBar = MenuBar(self)

        self.progressbar = Progressbar(self, orient='horizontal', length=100, mode='determinate')

        self.left_frame = Frame(self)
        self.img_label = Label(self.left_frame, text="Image Management Panel")
        self.img_table = Treeview(self.left_frame, show="headings", columns=('Image Name', 'BAF', 'In', 'BA'))
        self.img_table_bar = Scrollbar(self.left_frame)

        self.btn_frame = Frame(self.left_frame)
        self.add_img_btn = Button(self.btn_frame, text="Add img(s)", state='disabled', command=self.add_img)
        self.del_img_btn = Button(self.btn_frame, text="Del img(s)", state='disabled', command=self.del_img)

        self.right_frame = Frame(self)
        self.tree_label = Label(self.right_frame, text="Tree Management Panel")
        self.tree_table = Treeview(self.right_frame, show="headings", columns=('No.', 'Width', 'State'))
        self.tree_table_bar = Scrollbar(self.right_frame)
        self.del_tree_btn = Button(self.right_frame, text="Del tree(s)", state='disabled')

        self.ScrolledCanvas = ScrolledCanvas(self)

        # ====================
        #  Components configs
        # ====================
        self.add_img_btn.config(bg='white')
        self.del_img_btn.config(bg='white')
        self.del_tree_btn.config(bg='white')

        self.img_table.column('Image Name', width=130, anchor='center')
        self.img_table.column('BAF', width=40, anchor='center')
        self.img_table.column('In', width=40, anchor='center')
        self.img_table.column('BA', width=40, anchor='center')
        self.img_table.heading('Image Name', text='Image Name')
        self.img_table.heading('BAF', text='BAF')
        self.img_table.heading('In', text='In')
        self.img_table.heading('BA', text='BA')

        self.img_table_bar.config(command=self.img_table.yview, bg='white')
        self.img_table.config(yscrollcommand=self.img_table_bar.set)

        self.tree_table.column('No.', width=40, anchor='center')
        self.tree_table.column('Width', width=50, anchor='center')
        self.tree_table.column('State', width=45, anchor='center')
        self.tree_table.heading('No.', text='No.')
        self.tree_table.heading('Width', text='Width')
        self.tree_table.heading('State', text='State')

        self.tree_table_bar.config(command=self.tree_table.yview, bg='white')
        self.tree_table.config(yscrollcommand=self.tree_table_bar.set)

        self.bind('<Control-n>', self.MenuBar.new_project)
        self.bind('<Control-o>', self.MenuBar.open_project)
        self.bind('<Control-s>', self.MenuBar.save_project)
        self.img_table.bind('<ButtonRelease-1>', self.open_img_project)

        # connect to the control of Scrolled Canvas
        self.bind('<space>', self.ScrolledCanvas.open_create_tree_mode)
        self.bind('<KeyPress-Shift_L>', self.ScrolledCanvas.press_shift)
        self.bind('<KeyRelease-Shift_L>', self.ScrolledCanvas.release_shift)

        self.img_table.bind('<Button-3>', self.change_baf)
        self.img_table.bind('<Button-2>', self.change_baf_all)

        # ====================
        #  packing components
        # ====================
        self.MenuBar.pack(side='top', fill='x')

        self.progressbar.pack(side='bottom', fill='x')

        self.left_frame.pack(side='left', fill='y')
        self.img_label.pack(side='top', fill='x')
        self.btn_frame.pack(side='bottom', fill='x')
        self.add_img_btn.pack(side='left', fill='x', expand='yes')
        self.del_img_btn.pack(side='right', fill='x', expand='yes')
        self.img_table_bar.pack(side='right', fill='y')
        self.img_table.pack(side='top', fill='y', expand='yes')

        self.right_frame.pack(side='right', fill='y')
        self.tree_label.pack(side='top', fill='both')
        self.del_tree_btn.pack(side='bottom', fill='x')
        self.tree_table_bar.pack(side='right', fill='y')
        self.tree_table.pack(side='top', fill='y', expand='yes')

        self.ScrolledCanvas.pack(side='top', fill='both', expand='yes')

    def make_unsaved(self):
        self.saved = False
        self.update_title()

    def update_title(self):
        if self.saved:
            title_suffix = ''
        else:
            title_suffix = '* (Not saved)'

        full_title = self.title_name + title_suffix
        self.title(full_title)

    def quit_save_confirm(self):

        def _do_quit():
            self.quit()
            if os.path.exists('~default.sqlite'):
                db.conn.close()
                os.remove('~default.sqlite')

        if not self.saved:
            ans = askokcancel('Warning', "Changes not saved, continue quit and drop all changes?")
            if ans:
                _do_quit()
        else:
            _do_quit()

    def update_progress(self, value):
        # value is between 0 and 100
        self.progressbar['value'] = value
        self.progressbar.update()

    def add_img(self):
        mode = askyesnocancel('Add mode selection', 'Add images from folder? (Choose no to just add a single image)')
        if mode is not None:
            if mode:  # add by folder
                folder_name = askdirectory(title='Choose an image folder')
                if folder_name != '':  # select a folder
                    ask_keyword = True
                    while ask_keyword:
                        keyword_string = askstring(title='Input include keywords',
                                                   prompt="support image type:(*.jpg, *.jpeg, *.png)\n"
                                                          "leave empty or type '*' to add all images,\n"
                                                          "keywords should split by ';' or space ' ',"
                                                          "'-' before a word to exclude this word\n===============\n"
                                                          "e.g. 'cor; rua -19' means "
                                                          "add images have 'cor' OR 'rua' but do not contain '19'")
                        if keyword_string is not None:  # input a string
                            keyword_string = keyword_string.replace('；', ';')
                            keyword_string = keyword_string.replace(' ', ';')
                            if keyword_string == '' or keyword_string == '*':  # input all images
                                img_dir_list, img_name_list = self._get_all_image_dirs(folder_name, '*')
                            else:
                                keywords = keyword_string.split(';')
                                img_dir_list, img_name_list = self._get_all_image_dirs(folder_name, keywords)

                            satisfy = askyesnocancel('Import confirm', 'Import all the following images? [Yes] to add, '
                                                                       '[No] to re-input keywords, '
                                                                       '[Cancel] to stop adding\n'+str(img_name_list))
                            if satisfy is None:  # stop adding
                                ask_keyword = False
                            else:
                                if satisfy:  # confirm to add
                                    ask_keyword = False
                                    length = len(img_dir_list)
                                    for i, img_dir in enumerate(img_dir_list):
                                        db.add_img(img_dir)
                                        self.update_progress(int(100 * i / length))
                                    self.refresh_img_table()
                                    self.open_img_project()
                                    self.make_unsaved()
                                    self.update_progress(100)
                        else:  # cancel adding
                            ask_keyword = False
            else:  # add single img
                img_dir = askopenfilename(title='Choose an image', filetypes=[('JPEG', '.jpeg, .jpg'), ('PNG', '.png')])
                if img_dir != '':
                    db.add_img(img_dir)
                    self.update_progress(50)
                    self.progressbar.update()
                    self.refresh_img_table()
                    self.open_img_project()
                    self.update_progress(100)
                    self.make_unsaved()

    @staticmethod
    def _get_all_image_dirs(folder_name, keywords='*'):
        img_dir_list = []
        img_name_list = []
        g = os.walk(folder_name)
        for path, dir_list, file_list in g:
            for file_name in file_list:
                # check whether it is a image file
                pick = False
                for suffix in ['.jpg', '.jpeg', '.JPG', '.JPEG', '.png']:
                    if suffix in file_name:
                        pick = True
                if not pick:
                    continue

                if keywords == '*':  # add all images
                    img_dir = os.path.join(path, file_name)
                    img_dir_list.append(img_dir)
                    img_name_list.append(file_name)
                else:
                    include = False
                    exclude = False
                    for key in keywords:
                        if '-' in key:  # exclude keywords
                            ex_key = key[1:]
                            if ex_key in file_name:
                                exclude = True
                        else:  # include keyword
                            if key in file_name:
                                include = True
                    if include and not exclude:
                        img_dir = os.path.join(path, file_name)
                        img_dir_list.append(img_dir)
                        img_name_list.append(file_name)

        return img_dir_list, img_name_list

    def del_img(self):
        selections = self.img_table.selection()
        length = len(selections)

        rm_img_id_list = []
        rm_img_name_list = []
        for str_img_id in selections:
            img_id = int(str_img_id)
            img_table_row = self.img_info['img_id'].index(img_id)
            img_name = self.img_info['img_name'][img_table_row]
            rm_img_id_list.append(img_id)
            rm_img_name_list.append(img_name)

        self.update_progress(20)
        confirm = askyesno('warning', 'Are you sure to remove the following images?\n' +
                           str(rm_img_name_list) + '\nall tree data in these image will also get lost')
        if confirm:
            for i, img_id in enumerate(rm_img_id_list):
                db.rm_img(img_id)
                steps = int(70 * i / length)
                self.update_progress(20 + steps)
            self.refresh_img_table()
            self.update_progress(95)
            self.open_img_project()
            self.make_unsaved()
            self.update_progress(100)
        else:  # cancel remove
            self.update_progress(100)

    def change_baf(self, event=None):
        if self.del_img_btn['state'] == 'normal':  # have data in img_table
            baf = askfloat('Change BAF', 'Input the BAF value (float, e.g. 2.0) changing to:')
            if baf is not None:
                self.update_progress(50)
                db.edit_img_baf(self.ScrolledCanvas.img_id, baf)
                self.local_refresh_img_table(baf)
                self.refresh_tree_table()
                self.ScrolledCanvas.open_img(reload=False)
                self.update_progress(100)
                self.make_unsaved()
                
    def change_baf_all(self, event=None):
        if self.del_img_btn['state'] == 'normal':  # have data in img_table
            if not self.saved:
                asksave = askyesnocancel("Warning", "You changes have not been saved, save it? \n"
                                                    "[Cancel] to cancel changing all BAFs, \n"
                                                    "[No] to changing all BAFs without saving current changes")
                print(asksave)
                if asksave is None:
                    return
                if asksave:  # == True
                    self.MenuBar.save_project()

            baf = askfloat('Change all BAFs', 'Input the BAF value (float, e.g. 2.0) changing all the images to:')
            if baf is not None:
                confirm2 = askyesno("Warning", "Confirm changing all BAF to value " +
                                    str(baf) + '?\nThis operation can not undo.')
                if confirm2:
                    db.edit_img_baf_all(baf)
                    self.refresh_img_table()
                    self.refresh_tree_table()
                    self.ScrolledCanvas.open_img(reload=False)
                    self.make_unsaved()

    def del_tree(self, event=None):
        pass
    
    def local_refresh_img_table(self, baf):
        # update img_table information
        selections = self.img_table.selection()
        if len(selections) == 1:  # not multiple selection
            img_id = int(selections[0])
            img_table_row =  self.img_info['img_id'].index(img_id)
            in_tree_num = self.tree_info['state'].count('in')
            ba = plot_ba_calculator(baf, in_tree_num)
            self.img_info['baf'][img_table_row] = baf
            self.img_info['in_num'][img_table_row] = in_tree_num
            self.img_info['ba'][img_table_row] = ba

            # update img_table
            values = [self.img_info['img_name'][img_table_row],
                      self.img_info['baf'][img_table_row],
                      self.img_info['in_num'][img_table_row],
                      self.img_info['ba'][img_table_row]]
            self.img_table.item(img_id, values=values)

    def refresh_img_table(self):
        # clear table info
        self.img_table.delete(*self.img_table.get_children())
        # get image info
        self.img_info = db.get_img_info()
        length = len(self.img_info['img_id'])
        if length > 0:  # have img data
            self.del_img_btn.config(state='normal')
            for i in range(length):
                img_values = [self.img_info['img_name'][i], self.img_info['baf'][i],
                              self.img_info['in_num'][i], self.img_info['ba'][i]]
                self.img_table.insert('', 'end', iid=str(self.img_info['img_id'][i]), values=img_values)
            self.img_table.selection_set(str(self.img_info['img_id'][0]))
        else:  # no img data, empty project
            self.del_img_btn.config(state='disabled')
            self.refresh_tree_table()
            self.ScrolledCanvas.initialize(clean_canvas=True)

    def refresh_tree_table(self):
        # clear table info
        self.tree_table.delete(*app.tree_table.get_children())
        # get new tree info
        self.tree_info = db.get_tree_info(self.ScrolledCanvas.img_id)
        length = len(self.tree_info['tree_id'])
        if length > 0:  # tree exist
            self.del_tree_btn.config(state='normal')
            for i in range(length):
                # here start counting tree number (display in tree_table) from 1
                tree_values = [i+1, self.tree_info['width'][i], self.tree_info['state'][i]]
                # but the actual tree index start from 0 in software
                self.tree_table.insert('', 'end', iid=str(self.tree_info['tree_id'][i]), values=tree_values)
        else:
            self.del_tree_btn.config(state='disabled')

    def open_img_project(self, event=None, force_fresh=False):
        if self.del_img_btn['state'] == 'normal':  # ensure it is not an empty list
            selections = self.img_table.selection()
            if len(selections) == 1:  # not multiple selection
                img_id = int(selections[0])
                img_table_row = self.img_info['img_id'].index(img_id)
                # check if click on the older one
                new_img_id = self.img_info['img_id'][img_table_row]
                if new_img_id != self.ScrolledCanvas.img_id or force_fresh:  # click not the same
                    self.ScrolledCanvas.img_id = self.img_info['img_id'][img_table_row]
                    self.ScrolledCanvas.img_dir = self.img_info['img_dir'][img_table_row]
                    self.ScrolledCanvas.baf = self.img_info['baf'][img_table_row]
                    self.ScrolledCanvas.img_width = self.img_info['width'][img_table_row]
                    self.ScrolledCanvas.img_height = self.img_info['height'][img_table_row]
                    self.refresh_tree_table()
                    self.update_progress(30)
                    self.ScrolledCanvas.open_img(reload=True)
                    self.update_progress(100)


class MenuBar(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.pack()
        self.menubar = Frame(self)
        self.menubar.config(bg='white')
        self.menubar.pack(side='top', fill='x')

        self.fbutton = Menubutton(self.menubar, text='File', underline=0)
        self.fbutton.pack(side='left')
        self.file = Menu(self.fbutton, tearoff=False)
        self.file.add_command(label='New', command=self.new_project, underline=0)
        self.file.add_command(label='Open', command=self.open_project, underline=1)
        self.file.add_command(label='Save', command=self.save_project, underline=1, state='disabled')
        self.fbutton.config(menu=self.file, bg='white')

        self.cbutton = Menubutton(self.menubar, text='Export', underline=0, state='disabled')
        self.cbutton.pack(side='left')
        self.export = Menu(self.cbutton, tearoff=False)
        self.export.add_command(label='Default BAF', command=self.default_baf_export, underline=0)
        self.export.add_command(label='BAF sequence', command=self.sequence_baf_export, underline=0)
        self.cbutton.config(menu=self.export, bg='white')

    def new_project(self, event=None):
        ans = True
        if not app.saved:
            ans = askyesnocancel('Warning', 'Changes not saved, save current changes[Y], discard changes[N], or cancel?')

        if ans is None:  # cancel
            return
        elif ans:  # save changes
            self.save_project()

        project_dir = asksaveasfilename(title='New project', defaultextension=".sqlite", initialdir='.',
                                        filetypes=[('Pano2ba project', '.sqlite')])
        if project_dir != '':
            print(project_dir)
            if project_dir[-7:] == '.sqlite':
                app.add_img_btn.config(state='normal')
                app.del_img_btn.config(state='disabled')
                app.title_name = project_dir[:20] + '...' + project_dir[-30:]
                app.update_title()
                app.update_progress(20)

                if os.path.exists(project_dir):
                    os.remove(project_dir)
                app.update_progress(50)

                db.create_db(project_dir)
                if os.path.exists('~default.sqlite'):
                    os.remove('~default.sqlite')
                app.update_progress(70)

                app.img_table.delete(*app.img_table.get_children())
                app.tree_table.delete(*app.tree_table.get_children())
                app.ScrolledCanvas.initialize(clean_canvas=True)

                self.file.entryconfigure('Save', state="normal")
                app.update_progress(100)

    def open_project(self, event=None):
        ans = True
        if not app.saved:
            ans = askyesnocancel('Warning',
                                 'Changes not saved, save current changes[Y], discard changes[N], or cancel?')

        if ans is None:  # cancel
            return
        elif ans:  # save changes
            self.save_project()

        project_dir = askopenfilename(title='Open project', initialdir='.', filetypes=[('Pano2ba project', '.sqlite')])
        if project_dir != '':
            former_db_path = db.db_path
            db.change_db(project_dir)
            # check if is the pano2ba project db
            db.curs.execute("SELECT name FROM sqlite_master WHERE type='table';")
            app.update_progress(5)
            if db.curs.fetchall() == [('ImageInfo',), ('TreeInfo',)]:
                app.add_img_btn.config(state='normal')
                app.title_name = project_dir[:20] + '...' + project_dir[-30:]
                app.update_title()
                app.update_progress(10)

                if os.path.exists('~default.sqlite'):
                    os.remove('~default.sqlite')
                app.update_progress(15)

                # loading img_info
                app.refresh_img_table()
                app.update_progress(20)

                app.open_img_project(force_fresh=True)
                app.update_progress(100)
            else:
                db.change_db(former_db_path)
                app.update_progress(100)
                showwarning('Open Errors', 'This sqlite file is not pano2BA project database')

    def save_project(self, event=None):
        if app.title_name != 'Panorama2BA':
            app.update_progress(20)
            db.commit()
            app.update_progress(70)
            app.saved = True
            app.update_title()
            app.update_progress(100)

    def default_baf_export(self):
        pass

    def sequence_baf_export(self):
        pass


class ScrolledCanvas(Frame):
    add_tree = False
    add_tree_lock = False
    zoom_ratio = 1
    mouse_in_canvas = False
    shift_hold = False
    move_point = False

    moving = {'fixed_p': [0, 0], 'line': 'line_id', 'move_p': 'point_id',
              'text': 'text_id', 'tree_row': 0}
    shape_ids = {'point1': [], 'line': [], 'point2': [], 'text': [], 'canvas_img': None}  # default, point1 is left, point2 is right

    # record current img
    img_id = -1
    img_dir = ''
    baf = 2
    img_width = 1000
    img_height = 800
    save_image = None  # preprocess photos = PIL.Image()
    save_photo = None  # zoomed photo shows in canvas = tk.PhotoImage()

    def __init__(self, parent=None):
        Frame.__init__(self, parent)

        self.canvas = Canvas(self, relief='sunken')
        self.vbar = Scrollbar(self)
        self.hbar = Scrollbar(self, orient='horizontal')

        self.canvas.config(borderwidth=0, bg='white')
        self.vbar.config(command=self.canvas.yview, bg='white')  # scroll steps
        self.hbar.config(command=self.canvas.xview, bg='white')
        self.canvas.config(yscrollcommand=self.vbar.set)  # canvas steps
        self.canvas.config(xscrollcommand=self.hbar.set)
        self.canvas.bind('<ButtonPress-1>', self.left_click)
        self.canvas.bind('<B1-Motion>', self.hold_move_mouse)
        self.canvas.bind('<Motion>', self.move_mouse)
        self.canvas.bind('<ButtonRelease-1>', self.left_loose)
        self.canvas.bind('<MouseWheel>', self.xbar_scroll)
        self.canvas.bind('<Control-MouseWheel>', self.zoom)
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)

        self.vbar.pack(side='right', fill='y')
        self.hbar.pack(side='bottom', fill='x')
        self.canvas.pack(side='top', fill='both', expand='yes')

        imarray = ones((10, 10, 3)) * 255
        im = Image.fromarray(imarray.astype('uint8')).convert("RGBA")
        photo_im = PhotoImage(im)
        self.shape_ids['canvas_img'] = self.canvas.create_image(0, 0, image=photo_im, anchor='nw')

    # ========================
    #  functions used outside
    # ========================
    def initialize(self, clean_canvas=False):
        # functions used to
        self.add_tree = False
        self.add_tree_lock = False
        self.zoom_ratio = 1
        self.mouse_in_canvas = False
        self.shift_hold = False
        self.move_point = False

        # clear canvas trees record
        self._clear_canvas_all_trees()
        self.shape_ids['point1'] = []
        self.shape_ids['point2'] = []
        self.shape_ids['line'] = []
        self.shape_ids['text'] = []

        if clean_canvas:
            self.img_id = -1
            self.img_dir = ''
            self.baf = 2
            self.img_width = 1000
            self.img_height = 800
            self.save_image = None
            self.save_photo = None

            imarray = ones((10, 10, 3)) * 255
            im = Image.fromarray(imarray.astype('uint8')).convert("RGBA")
            self.save_photo = PhotoImage(im)
            self._update_img()

    def open_img(self, reload=True):
        # step0: clear canvas
        # step1: load image and image equalization
        # step2: draw dealt image
        # step3: draw trees and update self.shapes_ids; init moving and other ctrl params
        self.initialize(clean_canvas=False)
        app.update_progress(45)

        # step 0
        if reload:
            self._preprocess_img()
            app.update_progress(60)
            self._resize_img()
            app.update_progress(70)
            self._update_img()
        else:
            self._resize_img()
            self._update_img()

        self._change_canvas_position(0, self.save_photo.height() / 2)
        # step 1
        app.update_progress(80)

        # step 3: draw trees
        tree_num = len(app.tree_info['tree_id'])
        for tree_row in range(tree_num):
            x1, y1 = app.tree_info['left'][tree_row]
            x2, y2 = app.tree_info['right'][tree_row]
            if app.tree_info['state'][tree_row] == 'out':
                line = self.canvas.create_line(x1, y1, x2, y2, fill='red', width=3)
            else:
                line = self.canvas.create_line(x1, y1, x2, y2, fill='blue', width=3)
            point1 = self.canvas.create_oval(x1 - 5, y1 - 5, x1 + 5, y1 + 5, fill='yellow', outline='black')
            point2 = self.canvas.create_oval(x2 - 5, y2 - 5, x2 + 5, y2 + 5, fill='yellow', outline='black')
            text_x = (x1 + x2) / 2
            text_y = (y1 + y2) / 2
            text = self.canvas.create_text(text_x, text_y, text=str(tree_row+1), fill='yellow', font=('Times', '12', 'bold'))

            self.shape_ids['point1'].append(point1)
            self.shape_ids['point2'].append(point2)
            self.shape_ids['line'].append(line)
            self.shape_ids['text'].append(text)

            progress = 20 * (tree_row / tree_num)
            app.update_progress(80 + progress)

    def open_create_tree_mode(self, event):
        # press 'space' changing to adding tree mode
        if app.del_img_btn['state'] == 'normal':  # ensure have img data
            if not self.add_tree:  # not in add tree mode
                self.add_tree = True
                print('creating mode open')
                if self.mouse_in_canvas:
                    self.config(cursor='tcross')
            else:
                if not self.add_tree_lock:  # not in the second tree
                    self.add_tree = False
                    print('creating mode close')
                    self.config(cursor='arrow')

    def tree_center(self, tree_id):
        pass

    # =======================
    #  functions used inside
    # =======================

    # --------------
    #  mouse events
    # --------------
    def left_click(self, event):
        if self.add_tree:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            app.make_unsaved()
            if not self.add_tree_lock:  # click for the first time
                number = len(self.shape_ids['point1'])

                line = self.canvas.create_line(x, y, x, y, fill='red', width=3)
                point1 = self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill='yellow', outline='black')
                point2 = self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill='yellow', outline='black')
                text = self.canvas.create_text(x, y, text=str(number + 1), fill='yellow', font=('Times', '12', 'bold'))

                self.moving['fixed_p'] = [x, y]
                self.moving['line'] = line
                self.moving['move_p'] = point2
                self.moving['text'] = text

                self.shape_ids['point1'].append(point1)
                self.shape_ids['point2'].append(point2)
                self.shape_ids['line'].append(line)
                self.shape_ids['text'].append(text)

                self.add_tree_lock = True
            else:  # click for the second time
                x0, y0 = self.moving['fixed_p']
                self._update_shape_info(x, y)
                self.add_tree_lock = False
                self.add_tree = False
                self.config(cursor='arrow')

                if not self.shift_hold:  # horizontal lock
                    y = y0

                self._update_tree_infos(self.img_id, x0, y0, x, y)

    def move_mouse(self, event):
        if self.add_tree_lock:  # draw lines follow mouse, only works when clicking the second point
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            self._update_shape_info(x, y)

    def hold_move_mouse(self, event):
        # only activated when press left and not loose
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if not self.add_tree:  # make sure not in adding tree mode
            if not self.move_point:  # find new points
                id_touched = event.widget.find_closest(x, y, halo=5)
                if id_touched:  # except canvas empty get nothing
                    # not touch the line and text item
                    if id_touched[0] in self.shape_ids['point1'] or id_touched[0] in self.shape_ids['point2']:
                        [center_x, center_y] = self._get_shape_center(id_touched[0])
                        if (center_x - x) ** 2 + (center_y - y) ** 2 <= 25:  # make sure touch in points
                            # find which tree record it belongs to
                            self._pick_moving_ids(id_touched[0])
                            self._update_shape_info(x, y)
                            self.move_point = True
            else:  # is moving former points, keep updating is enough
                self._update_shape_info(x, y)

    def left_loose(self, event):
        # update tree info if in edit mode
        if self.move_point:  # finish moving
            x0, y0 = self.moving['fixed_p']
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            self._update_tree_infos(app.tree_info['tree_id'][self.moving['tree_row']], x0, y0, x, y, mode='edit')
            self.move_point = False
            app.make_unsaved()

    def on_enter(self, event):
        self.mouse_in_canvas = True
        if self.add_tree:
            self.config(cursor='tcross')

    def on_leave(self, event):
        self.mouse_in_canvas = False
        self.config(cursor='arrow')

    def press_shift(self, event):
        if not self.shift_hold:
            self.shift_hold = True
            print(self.shift_hold)

    def release_shift(self, event):
        self.shift_hold = False
        print(self.shift_hold)

    def xbar_scroll(self, event):
        scroll = -1 if event.delta > 0 else 1
        self.canvas.xview_scroll(scroll, 'units')

    def zoom(self, event):
        pass

    # ------------------
    #  reused functions
    # ------------------
    def _update_tree_infos(self, tree_img_id, x0, y0, x, y, mode='add'):
        # functions to update img_table and tree_table when adding and editing tree points
        # x0, y0 is the fixed points position
        if mode == 'add':
            # consider zoom_ratio
            tree_id, width, baf_max = db.add_tree(img_id=tree_img_id,
                                                  lx=x0 / self.zoom_ratio, ly=y0 / self.zoom_ratio,
                                                  rx=x / self.zoom_ratio, ry=y / self.zoom_ratio, return_value=True)
            if baf_max >= self.baf:
                state = 'in'
            else:
                state = 'out'

            # add records to tree_table
            app.tree_info['tree_id'].append(tree_id)
            app.tree_info['left'].append([x0, y0])
            app.tree_info['right'].append([x, y])
            app.tree_info['width'].append(width)
            app.tree_info['state'].append(state)

            length = len(app.tree_info['tree_id'])

            if app.del_tree_btn['state'] == 'disabled':  # tree exist
                app.del_tree_btn.config(state='normal')

            tree_values = [length, width, state]
            app.tree_table.insert('', 'end', iid=str(tree_id), values=tree_values)

        else:  # mode=='edit'
            tree_row = self.moving['tree_row']
            if app.tree_info['left'][tree_row] == [x0, y0]:  # change the right(point2)
                app.tree_info['right'][tree_row] = [x, y]
                width, baf_max = db.edit_tree(tree_id=tree_img_id,
                                              lx=x0 / self.zoom_ratio, ly=y0 / self.zoom_ratio,
                                              rx=x / self.zoom_ratio, ry=y / self.zoom_ratio, return_value=True)
            else:  # change the left
                app.tree_info['left'][tree_row] = [x, y]
                width, baf_max = db.edit_tree(tree_id=tree_img_id,
                                              lx=x / self.zoom_ratio, ly=y / self.zoom_ratio,
                                              rx=x0 / self.zoom_ratio, ry=y0 / self.zoom_ratio, return_value=True)

            if baf_max >= self.baf:
                state = 'in'
            else:
                state = 'out'

            app.tree_info['width'][tree_row] = width
            app.tree_info['state'][tree_row] = state

            tree_values = [tree_row + 1, width, state]
            app.tree_table.item(str(app.tree_info['tree_id'][tree_row]), values=tree_values)
            
        app.local_refresh_img_table(self.baf)

    def _update_shape_info(self, x, y):
        # when adding and dragging tree points, line and points follow mouse
        x0, y0 = self.moving['fixed_p']
        line = self.moving['line']
        move_p = self.moving['move_p']
        text = self.moving['text']

        if not self.shift_hold:  # horizontal lock
            y = y0
        tree_width = db.length_calculator(x0, y0, x, y)
        baf_max = max_baf(self.img_width, tree_width)

        text_x = (x0 + x) / 2
        text_y = (y0 + y) / 2
        self.canvas.coords(line, [x0, y0, x, y])
        self.canvas.coords(move_p, [x - 5, y - 5, x + 5, y + 5])
        self.canvas.coords(text, [text_x, text_y])

        # change line colors
        if baf_max >= self.baf:
            # in tree
            self.canvas.itemconfigure(line, fill='blue')
        else:
            # out tree
            self.canvas.itemconfigure(line, fill='red')

    def _get_shape_center(self, shape_id):
        # return the tree edge points (oval) center coordinate as a fixed point
        x1, y1, x2, y2 = self.canvas.coords(shape_id)
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        return [center_x, center_y]

    def _pick_moving_ids(self, shape_id):
        # functions to update self.moving dictionary
        if shape_id in self.shape_ids['point1']:
            row_num = self.shape_ids['point1'].index(shape_id)
            line_id = self.shape_ids['line'][row_num]
            fixed_id = self.shape_ids['point2'][row_num]
            text = self.shape_ids['text'][row_num]
            self.moving['line'] = line_id
            self.moving['move_p'] = shape_id
            self.moving['fixed_p'] = self._get_shape_center(fixed_id)
            self.moving['tree_row'] = row_num
            self.moving['text'] = text
        if shape_id in self.shape_ids['point2']:
            row_num = self.shape_ids['point2'].index(shape_id)
            line_id = self.shape_ids['line'][row_num]
            fixed_id = self.shape_ids['point1'][row_num]
            text = self.shape_ids['text'][row_num]
            self.moving['line'] = line_id
            self.moving['move_p'] = shape_id
            self.moving['fixed_p'] = self._get_shape_center(fixed_id)
            self.moving['tree_row'] = row_num
            self.moving['text'] = text

    def _zoom_in(self):
        pass

    def _zoom_out(self):
        pass

    def _refresh_shapes(self):
        pass

    def _clear_canvas_one_trees(self, tree_row):
        # clear canvas
        self.canvas.delete(self.shape_ids['point1'][tree_row])
        self.canvas.delete(self.shape_ids['point2'][tree_row])
        self.canvas.delete(self.shape_ids['line'][tree_row])
        self.canvas.delete(self.shape_ids['text'][tree_row])

        # todo: refresh app.tree_table but not redraw

    def _clear_canvas_all_trees(self):
        for i in range(len(self.shape_ids['point1'])):
            self._clear_canvas_one_trees(i)

    def _change_canvas_position(self, center_x, center_y):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        print(canvas_height, canvas_width)
        img_width = self.save_photo.width()
        img_height = self.save_photo.height()
        print(img_width, img_height)

        x = (center_x - 0.5 * canvas_width) / img_width
        y = (center_y - 0.5 * canvas_height) / img_height

        final_x = min(max(0, x), 1)
        final_y = min(max(0, y), 1)

        self.canvas.xview_moveto(final_x)
        self.canvas.yview_moveto(final_y)

    def _update_img(self):
        self.canvas.itemconfig(self.shape_ids['canvas_img'], image=self.save_photo)
        width = self.save_photo.width()
        height = self.save_photo.height()
        self.canvas.config(scrollregion=(0, 0, width, height))

    def _preprocess_img(self):
        image = Image.open(self.img_dir)
        image = equalize(image)
        # draw center reference line
        draw = ImageDraw.Draw(image)
        draw.line([0, image.size[1] / 2, image.size[0], image.size[1] / 2], fill=(255, 255, 0))

        self.save_image = image

    def _resize_img(self):
        width, height = self.save_image.size
        if self.zoom_ratio < 1.0:
            filter = Image.ANTIALIAS
        else:
            filter = Image.BICUBIC

        img_zoom = self.save_image.resize((int(width * self.zoom_ratio),
                                           int(height * self.zoom_ratio)), filter)
        self.save_photo = PhotoImage(img_zoom)

    def _update_canvas_img(self, bg_img):
        pass


if __name__ == '__main__':
    app = Pano2BA()
    db = DataBase('~default.sqlite')
    app.mainloop()