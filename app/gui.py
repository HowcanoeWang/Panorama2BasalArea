"""
############################################################################
Panorama2BasalArea Beta 0.1: Calculate forest BA values from spherical
(panorama) images by manual tree selection.

Author: Howcanoe WANG

GUI class structure:
-- Pano2BA()
 |-- class MenuBar(pack='top')
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

from tkinter import Tk, Button, Menubutton, Menu, Canvas, Scrollbar, Label, Frame
from tkinter.messagebox import askokcancel
from tkinter.ttk import Treeview
from PIL import Image
from PIL.ImageTk import PhotoImage


class Pano2BA(Tk):

    saved = False

    def __init__(self):
        Tk.__init__(self)

        self.title('Panorama2BA')
        self.config(bg='white')
        self.protocol("WM_DELETE_WINDOW", self.quit_save_confirm)
        self.wm_state('zoomed')  # maximize windows

        self.w = self.winfo_width()
        self.h = self.winfo_height()

        # =====================
        #  creating components
        # =====================
        self.MenuBar = MenuBar(self)

        self.left_frame = Frame(self)
        self.img_label = Label(self.left_frame, text="Image Management Panel")
        self.img_table = Treeview(self.left_frame, show="headings", columns=('Image Name', 'BAF', 'In', 'BA'))

        self.btn_frame = Frame(self.left_frame)
        self.add_img_btn = Button(self.btn_frame, text="Add img(s)", command=self.add_img)
        self.del_img_btn = Button(self.btn_frame, text="Del img(s)", command=self.del_img)

        self.right_frame = Frame(self)
        self.tree_label = Label(self.right_frame, text="Tree Management Panel")
        self.tree_table = Treeview(self.right_frame, show="headings", columns=('No.', 'Width', 'State'))
        self.del_tree_btn = Button(self.right_frame, text="Del tree(s)")

        self.ScrolledCanvas = ScrolledCanvas(self)

        # ====================
        #  Components configs
        # ====================
        self.add_img_btn.config(bg='white')
        self.del_img_btn.config(bg='white')
        self.del_tree_btn.config(bg='white')

        self.img_table.column('Image Name', width=150, anchor='center')
        self.img_table.column('BAF', width=50, anchor='center')
        self.img_table.column('In', width=50, anchor='center')
        self.img_table.column('BA', width=50, anchor='center')
        self.img_table.heading('Image Name', text='Image Name')
        self.img_table.heading('BAF', text='BAF')
        self.img_table.heading('In', text='In')
        self.img_table.heading('BA', text='BA')

        self.tree_table.column('No.', width=50, anchor='center')
        self.tree_table.column('Width', width=50, anchor='center')
        self.tree_table.column('State', width=50, anchor='center')
        self.tree_table.heading('No.', text='No.')
        self.tree_table.heading('Width', text='Width')
        self.tree_table.heading('State', text='State')

        # ====================
        #  packing components
        # ====================
        self.MenuBar.pack(side='top', fill='x')

        self.left_frame.pack(side='left', fill='y')
        self.img_label.pack(side='top', fill='x')
        self.img_table.pack(side='top', fill='y', expand='yes')
        self.btn_frame.pack(side='top', fill='x')
        self.add_img_btn.pack(side='left', fill='x', expand='yes')
        self.del_img_btn.pack(side='right', fill='x', expand='yes')

        self.right_frame.pack(side='right', fill='y')
        self.tree_label.pack(side='top', fill='both')
        self.del_tree_btn.pack(side='bottom', fill='x')
        self.tree_table.pack(side='top', fill='y', expand='yes')

        self.ScrolledCanvas.pack(side='top', fill='both', expand='yes')

    def add_img(self):
        pass

    def del_img(self):
        pass

    def quit_save_confirm(self):
        if not self.saved:
            ans = askokcancel('Verfy exit', "Really quit?")
            if ans:
                self.quit()
        else:
            self.quit()


class MenuBar(Frame):

    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.pack()
        menubar = Frame(self)
        menubar.config(bg='white')
        menubar.pack(side='top', fill='x')

        fbutton = Menubutton(menubar, text='File', underline=0)
        fbutton.pack(side='left')
        file = Menu(fbutton, tearoff=False)
        file.add_command(label='New', command=self.new_project, underline=0)
        file.add_command(label='Open', command=self.open_project, underline=1)
        file.add_command(label='Save', command=self.save_project, underline=1)
        fbutton.config(menu=file, bg='white')

        cbutton = Menubutton(menubar, text='Export', underline=0, state='disabled')
        cbutton.pack(side='left')
        export = Menu(cbutton, tearoff=False)
        export.add_command(label='Default BAF', command=self.default_baf_export, underline=0)
        export.add_command(label='BAF sequence', command=self.sequence_baf_export, underline=0)
        cbutton.config(menu=export, bg='white')

        self.cbutton = cbutton
        self.fbutton = fbutton

    def new_project(self):
        pass

    def open_project(self):
        pass

    def save_project(self):
        pass

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


if __name__ == '__main__':
    root = Pano2BA()
    root.mainloop()