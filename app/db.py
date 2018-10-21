import os
import sqlite3
from math import sqrt
from PIL import Image
from ba import plot_ba_calculator, max_baf


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
                default_baf REAL NOT NULL DEFAULT 2)''')
        self.curs.execute('''
            CREATE TABLE TreeInfo (
                tree_id INT NOT NULL PRIMARY KEY,
                img_id INT NOT NULL,
                lx INT NOT NULL,
                ly INT NOT NULL,
                rx INT NOT NULL,
                ry INT NOT NULL,
                max_baf REAL NOT NULL,
                    FOREIGN KEY (img_id) REFERENCES ImageInfo(img_id))''')
        self.conn.commit()
        self.db_path = db_path

    def change_db(self, db_path):
        self.conn.close()
        self.conn = sqlite3.connect(db_path)
        self.curs = self.conn.cursor()
        self.db_path = db_path

    def add_img(self, img_path):
        im = Image.open(img_path)
        width, height = im.size
        img_name_ext = os.path.basename(img_path)
        img_name = os.path.splitext(img_name_ext)[0]

        self.curs.execute('select MAX(img_id) from ImageInfo')
        max_id = self.curs.fetchall()[0][0]
        if max_id is None:
            img_id = 0
        else:
            img_id = max_id + 1

        self.curs.execute('insert into ImageInfo values (?,?,?,?,?,?)',
                          (img_id, img_path, img_name, width, height, 2))

    def rm_img(self, img_id):
        self.curs.execute('delete from ImageInfo where img_id = ?', [img_id])
        self.curs.execute('delete from TreeInfo where img_id = ?', [img_id])

    def edit_img_baf(self, img_id, baf):
        self.curs.execute('update ImageInfo set default_baf = ? where img_id = ?', [baf, img_id])

    def get_img_info(self):
        self.curs.execute('select img_id, img_name, width, height, default_baf from ImageInfo')
        img_info = {'img_id': [], 'img_name': [], 'width': [], 'height': [], 'baf': [], 'in_num': [], 'ba': []}
        for r in self.curs.fetchall():
            img_info['img_id'].append(r[0])
            img_info['img_name'].append(r[1])
            img_info['width'].append(r[2])
            img_info['height'].append(r[3])
            img_info['baf'].append(r[4])

        for img_id, baf in zip(img_info['img_id'], img_info['baf']):
            self.curs.execute('select tree_id from TreeInfo where img_id = ? and max_baf >= ?', [img_id, baf])
            in_num = len(self.curs.fetchall())
            ba = plot_ba_calculator(baf, in_num)
            img_info['in_num'].append(in_num)
            img_info['ba'].append(ba)

        return img_info

    def add_tree(self, img_id, lx, ly, rx, ry):
        self.curs.execute('select MAX(tree_id) from TreeInfo')
        max_id = self.curs.fetchall()[0][0]
        if max_id is None:
            tree_id = 0
        else:
            tree_id = max_id + 1

        self.curs.execute('select width from ImageInfo where img_id = ?', [img_id])
        img_width = self.curs.fetchall()[0][0]
        baf_max = self._tree_calculator(lx, ly, rx, ry, img_width)

        self.curs.execute('insert into TreeInfo values (?,?,?,?,?,?,?)',
                          (tree_id, img_id, lx, ly, rx, ry, baf_max))

    def rm_tree(self, tree_id):
        self.curs.execute('delete from TreeInfo where tree_id = ?', [tree_id])

    def edit_tree(self, tree_id, lx, ly, rx, ry):
        self.curs.execute('select img_id from TreeInfo where tree_id = ?', [tree_id])
        img_id = self.curs.fetchall()[0][0]
        self.curs.execute('select width from ImageInfo where img_id = ?', [img_id])
        img_width = self.curs.fetchall()[0][0]

        baf_max = self._tree_calculator(lx, ly, rx, ry, img_width)

        self.curs.execute('update TreeInfo set lx = ?, ly = ?, rx = ?, ry = ?, max_baf = ? where tree_id = ?',
                          [lx, ly, rx, ry, baf_max, tree_id])

    def get_tree_info(self, img_id):
        self.curs.execute('select default_baf from ImageInfo where img_id = ?', [img_id])
        default_baf = self.curs.fetchall()[0][0]

        self.curs.execute('select tree_id, lx, ly, rx, ry, max_baf from TreeInfo where img_id = ?', [img_id])
        tree_info = {'tree_id': [], 'left': [], 'right': [], 'width': [], 'state': []}
        for ti in self.curs.fetchall():
            tree_info['tree_id'].append(ti[0])
            tree_info['left'].append([ti[1], ti[2]])
            tree_info['right'].append([ti[3], ti[4]])
            tree_info['width'].append(self._length_calculator(ti[1], ti[2], ti[3], ti[4]))
            if ti[5] >= default_baf:
                state = 'in'
            else:
                state = 'out'
            tree_info['state'].append(state)

        return tree_info

    def commit(self):
        self.conn.commit()

    def _tree_calculator(self, lx, ly, rx, ry, img_width):
        diameter_pixel = self._length_calculator(lx, ly, rx, ry)
        baf_max = max_baf(img_width, diameter_pixel)
        return baf_max

    @staticmethod
    def _length_calculator(lx, ly, rx, ry):
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
    # test delete tree
    db.rm_tree(tree_id=0)
    # test update tree info
    db.edit_tree(tree_id=3, lx=240, ly=430, rx=261, ry=430)
    # test getting info from db for gui.py
    print(db.get_img_info())
    print(db.get_tree_info(img_id=2))
    # testing edit baf info and change tree info at the same time
    db.edit_img_baf(img_id=2, baf=300)
    print(db.get_tree_info(img_id=2))
    db.commit()