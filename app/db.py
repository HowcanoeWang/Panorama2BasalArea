import os
import sqlite3
from math import sqrt
from PIL import Image
from ba import plot_ba_calculator, max_baf, in_tree_pixel


class DataBase:

    db_path = 'test.sqlite'

    def __init__(self, db_path='test.sqlite'):
        if not os.path.exists(db_path):
            self.create_db(db_path)
        else:  # open a table
            self.conn = sqlite3.connect(db_path)
            self.curs = self.conn.cursor()

    def create_db(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.curs = self.conn.cursor()

        self.curs.execute('''
            CREATE TABLE ImageInfo (
                img_id INT NOT NULL PRIMARY KEY,
                img_dir CHAR(256) NOT NULL,
                img_name CHAR(64) NOT NULL, 
                width INT NOT NULL, 
                height INT NOT NULL, 
                default_baf REAL NOT NULL DEFAULT 2,
                mode INT NOT NULL DEFAULT 0)''')
        self.curs.execute('''
            CREATE TABLE TreeInfo (
                tree_id INT NOT NULL PRIMARY KEY,
                img_id INT NOT NULL,
                lx REAL NOT NULL,
                ly REAL NOT NULL,
                rx REAL NOT NULL,
                ry REAL NOT NULL,
                max_baf REAL NOT NULL,
                    FOREIGN KEY (img_id) REFERENCES ImageInfo(img_id))''')
        self.curs.execute('''
            CREATE TABLE ClickInfo (
                click_id INT NOT NULL PRIMARY KEY,
                img_id INT NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                baf REAL NOT NULL,
                    FOREIGN KEY (img_id) REFERENCES ImageInfo(img_id))''')
        self.conn.commit()
        self.db_path = db_path


    def change_db(self, db_path):
        self.conn.close()
        self.conn = sqlite3.connect(db_path)
        self.curs = self.conn.cursor()
        self.db_path = db_path

    def update_db(self):
        # add a ref.ball mode here, fit to previous database
        self.curs.execute('''
            CREATE TABLE IF NOT EXISTS ClickInfo (
                click_id INT NOT NULL PRIMARY KEY,
                img_id INT NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                baf REAL NOT NULL,
                    FOREIGN KEY (img_id) REFERENCES ImageInfo(img_id))''')
        try:
            self.curs.execute('''
                ALTER TABLE ImageInfo ADD COLUMN mode INT NOT NULL DEFAULT 0''')
        except:
            pass

        self.commit()

    def add_img(self, img_path, mode=0):
        im = Image.open(img_path)
        width, height = im.size
        img_name_ext = os.path.basename(img_path)
        img_name = os.path.splitext(img_name_ext)[0]

        self.curs.execute('select MAX(img_id) from ImageInfo')
        max_id = self.curs.fetchone()[0]
        if max_id is None:
            img_id = 0
        else:
            img_id = max_id + 1

        self.curs.execute('insert into ImageInfo values (?,?,?,?,?,?,?)',
                          (img_id, img_path, img_name, width, height, 2, mode))

    def rm_img(self, img_id):
        self.curs.execute('delete from ImageInfo where img_id = ?', [img_id])
        self.curs.execute('delete from TreeInfo where img_id = ?', [img_id])

    def edit_img_mode(self, img_id, mode=0):
        self.curs.execute('update ImageInfo set mode = ? where img_id = ?', [mode, img_id])

    def edit_img_baf(self, img_id, baf):
        self.curs.execute('update ImageInfo set default_baf = ? where img_id = ?', [baf, img_id])

    def edit_img_baf_all(self, baf):
        self.curs.execute('update ImageInfo set default_baf = ?', [baf])

    def get_img_info(self):
        self.curs.execute('select img_id, img_dir, img_name, width, height, default_baf, mode from ImageInfo')
        img_info = {'img_id': [], 'img_dir': [], 'img_name': [],
                    'width': [], 'height': [], 'baf': [], 'mode':[], 'in_num': [], 'ba': []}
        for r in self.curs.fetchall():
            img_info['img_id'].append(r[0])
            img_info['img_dir'].append(r[1])
            img_info['img_name'].append(r[2])
            img_info['width'].append(r[3])
            img_info['height'].append(r[4])
            img_info['baf'].append(r[5])
            img_info['mode'].append(r[6])

        for i, img_id in enumerate(img_info['img_id']):
            baf = img_info['baf'][i]
            mode = img_info['mode'][i]
            if mode == 0:
                self.curs.execute('select tree_id from TreeInfo where img_id = ? and max_baf >= ?', [img_id, baf])
                in_num = len(self.curs.fetchall())
            else:
                self.curs.execute(('select click_id from ClickInfo where img_id = ? and baf = ?'), [img_id, baf])
                in_num = len(self.curs.fetchall())

            ba = plot_ba_calculator(baf, in_num)
            img_info['in_num'].append(in_num)
            img_info['ba'].append(ba)

        return img_info

    def get_img_info_baf_range(self, baf_list):
        img_info_all = {'img_id':[], 'img_name':[], 'baf_num_ba':[]}
        self.curs.execute('select img_id from ImageInfo')

        img_info_all['img_id'] = [r[0] for r in self.curs.fetchall()]

        for img_id in img_info_all['img_id']:
            self.curs.execute('select img_name from ImageInfo where img_id = ?', [img_id])
            img_info_all['img_name'].append(self.curs.fetchone()[0])
            baf_num_ba = []
            for baf in baf_list:
                self.curs.execute('select tree_id from TreeInfo where img_id =? and max_baf >= ?', [img_id, baf])
                in_num = len(self.curs.fetchall())
                ba = plot_ba_calculator(baf, in_num)
                baf_num_ba.append(ba)
                #baf_num_ba.append(in_num)

            img_info_all['baf_num_ba'].append(baf_num_ba)

        return img_info_all

    def add_tree(self, img_id, lx, ly, rx, ry, return_value=False):
        self.curs.execute('select MAX(tree_id) from TreeInfo')
        max_id = self.curs.fetchone()[0]
        if max_id is None:
            tree_id = 0
        else:
            tree_id = max_id + 1

        self.curs.execute('select width from ImageInfo where img_id = ?', [img_id])
        img_width = self.curs.fetchone()[0]
        baf_max = self.max_baf_calculator(lx, ly, rx, ry, img_width)

        self.curs.execute('insert into TreeInfo values (?,?,?,?,?,?,?)',
                          (tree_id, img_id, lx, ly, rx, ry, baf_max))
        width = self.length_calculator(lx, ly, rx, ry)
        if return_value:
            return tree_id, width, baf_max  # same order as get_tree_info

    def add_click(self, img_id,  x, y, return_value=False):
        self.curs.execute('select MAX(click_id) from ClickInfo')
        max_id = self.curs.fetchone()[0]
        if max_id is None:
            click_id = 0
        else:
            click_id = max_id + 1

        self.curs.execute('select default_baf from ImageInfo where img_id = ?', [img_id])
        baf = self.curs.fetchone()[0]

        self.curs.execute('select width from ImageInfo where img_id = ?', [img_id])
        img_width = self.curs.fetchone()[0]

        diameter_pixel = int(in_tree_pixel(baf, img_width))

        self.curs.execute('insert into ClickInfo values (?,?,?,?,?)', [click_id, img_id, x, y, baf])

        if return_value:
            return click_id, diameter_pixel

    def rm_tree(self, tree_id):
        self.curs.execute('delete from TreeInfo where tree_id = ?', [tree_id])

    def rm_click(self, click_id):
        self.curs.execute('delete from ClickInfo where click_id = ?', [click_id])

    def edit_tree(self, tree_id, lx, ly, rx, ry, return_value=False):
        self.curs.execute('select img_id from TreeInfo where tree_id = ?', [tree_id])
        img_id = self.curs.fetchone()[0]
        self.curs.execute('select width from ImageInfo where img_id = ?', [img_id])
        img_width = self.curs.fetchone()[0]

        width = self.length_calculator(lx, ly, rx, ry)
        baf_max = self.max_baf_calculator(lx, ly, rx, ry, img_width)

        self.curs.execute('update TreeInfo set lx = ?, ly = ?, rx = ?, ry = ?, max_baf = ? where tree_id = ?',
                          [lx, ly, rx, ry, baf_max, tree_id])
        if return_value:
            return width, baf_max

    def edit_click(self, click_id, x, y, return_value=False):
        self.curs.execute('update ClickInfo set x=?, y=? where click_id = ?', [x, y, click_id])

    def get_tree_info(self, img_id):
        self.curs.execute('select default_baf from ImageInfo where img_id = ?', [img_id])
        default_baf = self.curs.fetchone()

        tree_info = {'tree_id': [], 'left': [], 'right': [], 'width': [], 'state': []}

        if default_baf is not None:
            default_baf = default_baf[0]
            self.curs.execute('select tree_id, lx, ly, rx, ry, max_baf from TreeInfo where img_id = ?', [img_id])

            for ti in self.curs.fetchall():
                tree_info['tree_id'].append(ti[0])
                tree_info['left'].append([ti[1], ti[2]])
                tree_info['right'].append([ti[3], ti[4]])
                tree_info['width'].append(self.length_calculator(ti[1], ti[2], ti[3], ti[4]))
                if ti[5] >= default_baf:
                    state = 'in'
                else:
                    state = 'out'
                tree_info['state'].append(state)

        return tree_info

    def get_click_info(self, img_id):
        self.curs.execute('select default_baf from ImageInfo where img_id = ?', [img_id])
        default_baf = self.curs.fetchone()

        self.curs.execute('select width from ImageInfo where img_id = ?', [img_id])
        img_width = self.curs.fetchone()[0]

        diameter_pixel = int(in_tree_pixel(default_baf[0], img_width))

        click_info = {'click_id':[], 'x':[], 'y':[], 'width':[], 'state':[]}

        if default_baf is not None:
            default_baf = default_baf[0]
            self.curs.execute('select click_id, x, y from ClickInfo where img_id = ? AND baf=?', [img_id, default_baf])

            for ci in self.curs.fetchall():
                click_info['click_id'].append(ci[0])
                click_info['x'].append(ci[1])
                click_info['y'].append(ci[2])
                click_info['width'].append(diameter_pixel)
                click_info['state'].append('in')

        return click_info


    def get_tree_info_all(self):
        self.curs.execute('select img_id, tree_id, lx, ly, rx, ry, max_baf from TreeInfo order by img_id')
        tree_info_all = {'img_id':[], 'tree_id':[], 'width':[], 'max_baf':[]}
        for item in self.curs.fetchall():
            tree_info_all['img_id'].append(item[0])
            tree_info_all['tree_id'].append(item[1])
            tree_info_all['width'].append(self.length_calculator(item[2], item[3], item[4], item[5]))
            tree_info_all['max_baf'].append(item[6])

        return tree_info_all

    def get_click_info_all(self):
        self.curs.execute('select img_id, click_id, x, y, baf from ClickInfo order by img_id, baf')
        click_info_all = {'img_id':[], 'click_id':[], 'x':[], 'y':[], 'baf':[]}
        for item in self.curs.fetchall():
            click_info_all['img_id'].append(item[0])
            click_info_all['click_id'].append(item[1])
            click_info_all['x'].append(item[2])
            click_info_all['y'].append(item[3])
            click_info_all['baf'].append((item[4]))

        return click_info_all

    def commit(self):
        self.conn.commit()

    def max_baf_calculator(self, lx, ly, rx, ry, img_width):
        diameter_pixel = self.length_calculator(lx, ly, rx, ry)
        baf_max = max_baf(img_width, diameter_pixel)
        return baf_max

    @staticmethod
    def length_calculator(lx, ly, rx, ry):
        return int(sqrt((lx - rx) ** 2 + (ly - ry) ** 2))


if __name__ == '__main__':
    # testing
    if os.path.exists('test.sqlite'):
        os.remove('test.sqlite')
    db = DataBase()
    # testing add img
    db.add_img(r'..\images\examples\COR R1 S00 0 16.JPG')
    db.add_img(r'..\images\examples\COR R1 S00 1 16.JPG')
    # testing remove img
    db.rm_img(0)
    # testing add img to discontinuous img_id
    db.add_img(r'..\images\examples\COR R1 S12 0 16.JPG')
    db.add_img(r'..\images\examples\COR R1 S12 1 16.JPG')
    # testing edit baf info without trees
    db.edit_img_baf(img_id=1, baf=3)
    # try to update non exist img
    db.edit_img_baf(0, 3.4)
    # add trees to test
    db.add_tree(img_id=1, lx=360, ly=720, rx=658, ry=720)
    db.add_tree(img_id=1, lx=360, ly=720, rx=358, ry=720)  # lx < rx
    db.add_tree(img_id=2, lx=390, ly=720, rx=458, ry=770)  # not horizontal
    db.add_tree(img_id=2, lx=380, ly=720, rx=489, ry=720)
    db.add_click(img_id=1, x=300, y=500)
    db.add_click(img_id=1, x=500, y=765)
    db.add_click(img_id=2, x=5640, y=725)
    # test delete tree
    db.rm_tree(tree_id=0)
    db.rm_click(click_id=1)
    # test update tree info
    db.edit_tree(tree_id=3, lx=240, ly=430, rx=261, ry=430)
    db.edit_click(click_id=2, x=430, y=370)
    # test getting info from db for gui.py
    print(db.get_img_info())
    print(db.get_tree_info(img_id=2))
    print(db.get_click_info(img_id=2))
    # testing edit baf info and change tree info at the same time
    db.edit_img_baf(img_id=2, baf=300)
    print(db.get_tree_info(img_id=2))
    print(db.get_click_info(img_id=2))
    db.commit()