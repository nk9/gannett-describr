# Gannett Describr

A tool to very quickly associate [ED description images](https://gannett.cc/docs#ed-descriptions) with the names of the EDs described on that page.

https://github.com/user-attachments/assets/ddffc9c5-eabe-4877-9721-755d7440befa

## The Scraper

To download images from FamilySearch for categorization, populate the `../gannett-data/scrape_fs/ed_descr_nums.csv` file with all of the film numbers, UTP codes, and index start/end points. If you have added any new film numbers, you'll need to fetch the JSON description of those using the `just scrape_fs_ed_desc_film_info` recipe in `gannett-pipeline`.


Then simply run `just scrape-img` in this repo. Sign into FamilySearch in the spawned browser, and then return to the terminal and press Return.

That will populate the `../gannett-data/` directory with images broken up by years and UTP code.

## The Annotator

Having downloaded the images, you can now annotate them. `just` will run the default recipe and start the CLI annotator.

Place your right hand on the <kbd>n</kbd>, <kbd>m</kbd>, <kbd>&lt;</kbd>, and <kbd>&gt;</kbd> keys. This is the "home row" for annotating, and you can do most things with your right hand here and your left on the <kbd>Shift</kbd> key. Keyboard shortcuts which act on the primary ED slot:

| Key  | Effect |
| ---- | ------------- |
| <kbd>e</kbd>  | **Enter new ED** in primary slot and **add that ED** to image |
| <kbd>n</kbd>  | **Increment and add ED** from primary slot (mnemonic: Next) |
| <kbd>m</kbd>  | **Add current ED** from primary slot with no increment  |
| <kbd>,</kbd>, <kbd>&lt;</kbd>  | Switch to **previous image** (mnemonic: left angle bracket)|
| <kbd>.</kbd>, <kbd>&gt;</kbd>  | Switch to **next image** (mnemonic: right angle bracket) |
| <kbd>/</kbd>, <kbd>?</kbd>  | **Undo** last ED addition in the current image |
| <kbd>-</kbd> | **Decrement ED** in primary slot |
| <kbd>=</kbd> | **Increment ED** in primary slot |
| <kbd>f</kbd> | **Fill** all EDs from current primary slot to entered number |

You can add more slots to use, and interact with them by holding down <kbd>Shift</kbd>.

| Key  | Effect |
| ---- | ------------- |
| <kbd>E</kbd>  | **Enter new ED** in a new manual slot and **add that ED** to image |
| <kbd>N</kbd>  | **Increment and add ED** from current manual slot (mnemonic: Next) |
| <kbd>M</kbd>  | **Add current ED** from primary slot with no increment  |
| <kbd>space</kbd> | **Cycle through manual slots** |
| <kbd>_</kbd> | **Decrement ED** in current manual slot |
| <kbd>+</kbd> | **Increment ED** in current manual slot |
| <kbd>Ctrl</kbd>-<kbd>m</kbd> | **Remove current manual slot** |

There are a number of other available shortcuts:

| Key  | Effect |
| ---- | ------------- |
| <kbd>j</kbd> | **Jump to index** |
| <kbd>u</kbd> | **Open URL** for current image on FamilySearch site |
| <kbd>backspace</kbd> | **Remove** last ED from image |
| <kbd>s</kbd> | **Skip 1 beyond last untagged** image within current city |
| <kbd>S</kbd> | **Skip 1 beyond last untagged** image globally (ignoring 1880) |
| <kbd>q</kbd>  | Close browser and **Quit** |
