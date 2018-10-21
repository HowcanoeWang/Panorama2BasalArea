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
from tkinter.simpledialog import askstring
from tkinter.filedialog import asksaveasfilename, askopenfilename, askdirectory
from tkinter.messagebox import askokcancel, showwarning, askyesno, askyesnocancel
from tkinter.ttk import Treeview, Progressbar
# from PIL import Image
# from PIL.ImageTk import PhotoImage
from db import DataBase


class Pano2BA(Tk):

    saved = True
    title_name = 'Panorama2BA'
    img_info = {}
    tree_info = {}
    img_id = 0

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

        self.tree_table.column('No.', width=50, anchor='center')
        self.tree_table.column('Width', width=50, anchor='center')
        self.tree_table.column('State', width=50, anchor='center')
        self.tree_table.heading('No.', text='No.')
        self.tree_table.heading('Width', text='Width')
        self.tree_table.heading('State', text='State')

        self.tree_table_bar.config(command=self.tree_table.yview, bg='white')
        self.tree_table.config(yscrollcommand=self.tree_table_bar.set)

        self.bind('<Control-n>', MenuBar.new_project)
        self.bind('<Control-o>', MenuBar.open_project)
        self.bind('<Control-s>', MenuBar.save_project)
        self.img_table.bind('<ButtonRelease-1>', self.open_img_project)

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
                                                          "add images have 'cor' and 'rua' but not contain '19'")
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
                                    self.saved = False
                                    self.update_title()
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
                    self.saved = False
                    self.update_progress(100)
                    self.update_title()

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
        for table_id in selections:
            img_id = self.img_info['img_id'][int(table_id)]
            img_name = self.img_info['img_name'][int(table_id)]
            rm_img_id_list.append(img_id)
            rm_img_name_list.append(img_name)

        self.update_progress(20)
        confirm = askyesno('warning', 'Are you sure to remove the following images?\n' +
                           str(rm_img_name_list) + '\nall tree data in these image will also get lost')
        if confirm:
            for i, img_id in enumerate(rm_img_id_list):
                db.rm_img(img_id)
                steps = int(80 * i / length)
                self.update_progress(20 + steps)
            self.refresh_img_table()
            self.saved = False
            self.update_title()
            self.update_progress(100)
        else:  # cancel remove
            self.update_progress(100)

    def change_baf(self):
        pass

    def del_tree(self):
        pass

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
                self.img_table.insert('', 'end', iid=str(i), values=img_values)
            self.img_table.selection_set('0')

            self.img_id = self.img_info['img_id'][0]
            self.refresh_tree_table()
        else:  # no img data, empty project
            self.del_img_btn.config(state='disabled')

    def refresh_tree_table(self):
        # clear table info
        self.tree_table.delete(*app.tree_table.get_children())
        # get new tree info
        self.tree_info = db.get_tree_info(self.img_id)
        length = len(self.tree_info['tree_id'])
        if length > 0:  # tree exist
            self.del_tree_btn.config(state='normal')
            for i in range(length):
                tree_values = [i, self.tree_info['width'][i], self.tree_info['state'][i]]
                self.tree_table.insert('', 'end', iid=str(i), values=tree_values)
        else:
            self.del_tree_btn.config(state='disabled')

    def open_img_project(self, event):
        if self.del_img_btn['state'] == 'normal':  # ensure it is not an empty list
            selections = self.img_table.selection()
            if len(selections) == 1:  # not multiple selection
                self.img_id = self.img_info['img_id'][int(selections[0])]
                self.refresh_tree_table()


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

    def new_project(self):
        project_dir = asksaveasfilename(title='New project', defaultextension=".sqlite", initialdir='.',
                                        filetypes=[('Pano2ba project', '.sqlite')])
        if project_dir != '':
            print(project_dir)
            if project_dir[-7:] == '.sqlite':
                app.add_img_btn.config(state='normal')
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

                self.file.entryconfigure(2, state="normal")
                app.update_progress(100)

    def open_project(self):
        project_dir = askopenfilename(title='Open project', initialdir='.', filetypes=[('Pano2ba project', '.sqlite')])
        if project_dir != '':
            former_db_path = db.db_path
            db.change_db(project_dir)
            # check if is the pano2ba project db
            db.curs.execute("SELECT name FROM sqlite_master WHERE type='table';")
            app.update_progress(20)
            if db.curs.fetchall() == [('ImageInfo',), ('TreeInfo',)]:
                app.add_img_btn.config(state='normal')
                app.title_name = project_dir[:20] + '...' + project_dir[-30:]
                app.update_title()
                app.update_progress(50)

                if os.path.exists('~default.sqlite'):
                    os.remove('~default.sqlite')
                app.update_progress(70)
                # loading img_info
                app.refresh_img_table()
                app.update_progress(100)
            else:
                db.change_db(former_db_path)
                app.update_progress(100)
                showwarning('Open Errors', 'This sqlite file is not pano2BA project database')

    def save_project(self):
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

        self.vbar.pack(side='right', fill='y')
        self.hbar.pack(side='bottom', fill='x')
        self.canvas.pack(side='top', fill='both', expand='yes')

    # ========================
    #  functions used outside
    # ========================
    def open_img(self, img_id):
        pass

    def tree_center(self, tree_id):
        pass

    # =======================
    #  functions used inside
    # =======================
    def _open_create_tree_mode(self):
        pass

    def _refresh_tree_info(self):
        pass

    def _redraw_shapes(self):
        pass

    # --------------
    #  mouse events
    # --------------
    def left_click(self, event):
        pass

    def _pick_moving_ids(self, shape_id):
        pass

    def move_mouse(self, event):
        pass

    def _update_one_shape(self, x, y):
        pass

    def left_loose(self, event):
        pass

    def mouse_wheel(self, event):
        pass

    def _zoom_in(self):
        pass

    def _zoom_out(self):
        pass

    def _zoom_img(self):
        pass

    def _refresh_shapes(self):
        pass

    def _change_canvas_position(self):
        pass

    def _strength_img(self, img_id):
        pass

    def _update_canvas_img(self, bg_img):
        pass


if __name__ == '__main__':
    app = Pano2BA()
    db = DataBase('~default.sqlite')
    app.mainloop()