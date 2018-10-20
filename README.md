# Panorama2BasalArea
Calculate forest BA values from spherical(panorama) images by manual tree selection.

## Main functions:
1. project management based on sqlite database.
1. import single image and all images in one folder (and its child folders) whose name contain given keywords
1. image photo brightness equalization to show more details in overexposed and underexposed regions
1. image zoom in and out to get more details
1. tree management
    * add trees
    * edit trees
    * delete trees
1. export result excel files

## Operations
### 1. Project management
1. `File` > `New`: create a new project
1. `File` > `open`: open a former project
1. `File` > `save`: save changes to current project
1. `File` > `export`: export results to a excel file

### 2. Image management
1. `Add img`: add spherical image to this project
    Dialog: Add by folder? [Yes/No/Cancel]
    * `Yes`: select folder first, then type keywords in image name need to import.
        * `*`or leaving blank ` ` is importing all images (default)
        * keywords need split by `;`
    * `No`: select a single spherical image to import
1. `Del img`: remove the selected image from this project
    **Warning**: this operation will also delete all tree records in this image as well.
1. `left-click` on image name: show this image and its trees information
1. `double-click` on image name: change default BAF value of this image (default is 2)
1. `triple-click` on image name: change all images' default BAF values at once.

### 3. Tree management
1. Add trees
    1. `ctrl` + `mousewhell`: zoom images to proper size
    1. Press `N` switching to adding tree mode (cursor will change to +)
    1. `left-click` to add the first point of tree boundary
    1. `move` to another boundary, `left-click` for another boundary point
        * if the line between two points color is **red**, currently is **out** tree
        * if line color is **blue**, it is a **in** tree
        * default, the line is locked to be horizontal
        * press `shift` to unlock and create lines for leaned trees
2. Edit trees
    1. `left-click` the tree record, the image will center this tree line
    1. drag the boundary point to change position (hold `shift` for leaned tree)
3. Delete trees
    1. select the tree record and press `delete`
    1. a delete confirmation dialog will appear

### 4. Other Shortcuts
1. `mousewheel`: scroll image vertically
1. `alt` + `mousewheel`: scroll image horizontally

## Updates
All the previous functions mentioned above is still under construction ^_^