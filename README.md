# Gannett Describr

A tool to very quickly associate [ED description images](https://gannett.cc/docs#ed-descriptions) with the names of the EDs described on that page.

https://github.com/user-attachments/assets/ddffc9c5-eabe-4877-9721-755d7440befa

## The Scraper

Describr works with two sets of images, each with its own index CSV, image directory, and database:

| | Index CSV | Images | Database | Annotate | Download | Export |
| --- | --- | --- | --- | --- | --- | --- |
| ED descriptions | `../gannett-data/scrape_fs/ed_descr_nums.csv` | `../ed-desc-img` | `annotated.db` | `just` | `just scrape-img` | `just export` |
| ED maps | `../gannett-data/scrape_fs/ed_map_nums.csv` | `../ed-map-img` | `ed_maps.db` | `just maps` | `just scrape-maps` | `just export-maps` |

To download images from FamilySearch for categorization, populate the index CSV with UTP codes, where the images are, and their image indexes:

- **ED descriptions** are on microfilms: give the `digital_film_no` and `collection`, with `start_index`/`stop_index`.
- **ED maps** are in rolls of collection `2329948`: give that `collection` and the `roll_no` (e.g. `14` for "Roll 14, Illinois, Adams-Cook"), with an `indexes` column holding an inclusive index set such as `150-155,160-200`. Indexes are 1-based, matching the viewer's "Image N of M" (its URLs' `i=` is N − 1).

A metro may span several rows, e.g. when its pages are on more than one film or roll.

Then run the download recipe. It first fetches the image list for any new film or roll into `../gannett-data/scrape_fs/films/`, then downloads any images not already on disk. Roll image lists are public, so fetching them never needs a sign-in. FamilySearch access lives in the shared [`gannett-fs`](../gannett-fs) package, which `gannett-pipeline` uses too.

The scraper only asks you to sign into FamilySearch when it has to. It tries the `FS_AUTH`/`FS_COOKIES` credentials in `../gannett-pipeline/.env`, then the browser profile's saved session, and only then opens the sign-in page. Whenever it finds a newer session in the browser, it writes it back to that `.env`, which keeps `gannett-pipeline`'s FamilySearch scraper working too.

## The Annotator

Having downloaded the images, you can now annotate them. `just` will run the default recipe and start the CLI annotator.

Place your right hand on the <kbd>n</kbd>, <kbd>m</kbd>, <kbd>&lt;</kbd>, and <kbd>&gt;</kbd> keys. This is the "home row" for annotating, and you can do most things with your right hand here and your left on the <kbd>Shift</kbd> key. Keyboard shortcuts which act on the primary ED slot:

| Key  | Effect |
| ---- | ------------- |
| <kbd>e</kbd>  | **Enter new ED** in primary slot and **add that ED** to image |
| <kbd>n</kbd>  | **Increment and add ED** from primary slot (mnemonic: Next) |
| <kbd>m</kbd>  | **Add current ED** from primary slot with no increment |
| <kbd>2</kbd>&ndash;<kbd>9</kbd>  | **Increment and add (count) number of EDs** from primary slot |
| <kbd>,</kbd>,&nbsp;<kbd>&lt;</kbd>  | Switch to **previous image** (mnemonic: left angle bracket)|
| <kbd>.</kbd>,&nbsp;<kbd>&gt;</kbd>  | Switch to **next image** (mnemonic: right angle bracket) |
| <kbd>{</kbd>  | Jump to **previous metro** (mnemonic: left curly brace)|
| <kbd>}</kbd>  | Jump to **next metro** (mnemonic: right curly brace) |
| <kbd>(</kbd>  | Jump to **previous year** (mnemonic: left paren) |
| <kbd>)</kbd>  | Jump to **next year** (mnemonic: right paren) |
| <kbd>/</kbd>,&nbsp;<kbd>?</kbd>  | **Undo** last ED addition in the current image |
| <kbd>-</kbd> | **Decrement ED** in primary slot |
| <kbd>=</kbd> | **Increment ED** in primary slot (mnemonic: <kbd>+</kbd> uses the same key)  |
| <kbd>f</kbd> | **Fill all EDs** from current primary slot to entered number |
| <kbd>t</kbd> | **Fill count number** of EDs from current primary slot (mnemonic: counT) |
| <kbd>r</kbd> | **Remove ED(s)** from image (use <kbd>q</kbd> to dismiss) |

You can add more slots to use, and interact with them by holding down <kbd>Shift</kbd>. Slots are stored and displayed in sorted order.

| Key  | Effect |
| ---- | ------------- |
| <kbd>E</kbd>  | **Enter new ED** in a new manual slot and **add that ED** to image |
| <kbd>N</kbd>  | **Increment and add ED** from current manual slot (mnemonic: Next) |
| <kbd>M</kbd>  | **Add current ED** from primary slot with no increment  |
| <kbd>space</kbd> | **Cycle through manual slots** |
| <kbd>l</kbd>,&nbsp;<kbd>L</kbd>  | **Increase** manual slot |
| <kbd>k</kbd>,&nbsp;<kbd>K</kbd>  | **Decrease** manual slot |
| <kbd>_</kbd> | **Decrement ED** in current manual slot (mnemonic: <kbd>Shift</kbd>-<kbd>-</kbd>) |
| <kbd>+</kbd> | **Increment ED** in current manual slot |
| <kbd>Ctrl</kbd>-<kbd>m</kbd> | **Remove current manual slot** |

There are a number of other available shortcuts:

| Key  | Effect |
| ---- | ------------- |
| <kbd>j</kbd> | **Jump to index** |
| <kbd>J</kbd> | **Jump to metro** by prefix |
| <kbd>u</kbd> | **Open URL** for current image on FamilySearch site |
| <kbd>backspace</kbd> | **Remove** last ED from image |
| <kbd>s</kbd> | **Skip 1 beyond last untagged** image within current city |
| <kbd>S</kbd> | **Skip 1 beyond last untagged** image globally (ignoring 1880) |
| <kbd>q</kbd>  | Close browser and **Quit** |
