from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, \
    StaleElementReferenceException
import time
import json
import os, sys
from loggerClass import logger

# WEB_DRIVER_LINK = os.path.join(os.path.realpath(os.path.dirname(__file__)),'chromedriver-win64', 'chromedrive.exe')
WEB_DRIVER_LINK = 'chromedrive.exe'
SITE_TO_SCRAPE = r'https://erquran.org/'


def load_json(filename='chapter-verse-number-data.json', data: dict | bool = False):
    if isinstance(data, bool):
        with open(filename, 'r') as file:
            return json.load(file)
    else:
        with open(filename, 'w') as file:
            json.dump(data, file)


def get_driver():
    _driver = None
    _driver_action = None
    try:
        _driver = webdriver.Chrome()
        _driver_action = ActionChains(_driver)
        # Other selenium operations
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
    _driver.get(SITE_TO_SCRAPE)
    logger.debug(f'Driver and action successfully acquired: {_driver.title}')
    return _driver, _driver_action


def next_chapter():
    chapters_list = list(CHAPTER_VERSE_NUMBER.keys())
    for chapter_number_in_list in chapters_list:
        yield chapter_number_in_list


def next_verse(current_chapter_number):
    verse_list = CHAPTER_VERSE_NUMBER[current_chapter_number]
    for chunck in verse_list:
        for i in range(chunck[0], chunck[1]):
            yield i


def get_element_by_class(name, transform=True, driver=None):
    element = None
    try:
        if transform:
            selector = '.'.join(name.split())
        else:
            selector = name
        logger.debug(f'Finding element with selector: {selector}')

        element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, selector)))
        logger.debug(f'Found ({selector}): {element}')
    except Exception as e:
        if isinstance(e, str):
            logger.error(e)
        else:
            logger.error(str(e))
    return element


def go_to_chapter(chapter, driver, check_if_transition=False):
    actual_chapter_index = chapter - 1
    if chapter <= 0:
        logger.error('Chapter number must be greater than 0')
        return
    elif chapter > 114:
        logger.error('Chapter number is too large, maximum is 114')
        return

    logger.info(f"Navigating to chapter number {chapter}")
    # finding and showing dropdown action button
    chapter_dropdown_button_selector = 'dropdown icon'
    chapter_dropdown_button_element = get_element_by_class(chapter_dropdown_button_selector, driver=driver)

    chapter_dropdown_button_element.click()

    # finding and selecting chapter from dropdown list
    chapter_dropdown_list_selector = '.'.join('visible menu transition'.split())
    chapter_dropdown_list_element = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.CLASS_NAME, chapter_dropdown_list_selector)))

    clickable_chapters_in_list = chapter_dropdown_list_element.find_elements(By.CLASS_NAME, 'item')
    current_chapter = clickable_chapters_in_list[actual_chapter_index]
    # assertion
    current_chapter_text_element = WebDriverWait(current_chapter, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'span.text'))
    )
    current_chapter_text_element_text = current_chapter_text_element.text
    current_chapter.click()

    if check_if_transition:
        chapter_dropdown_button_element.click()
        active_chapter = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div[role='option'][aria-checked='true']")))
        active_chapter_text_element = active_chapter.find_element(By.CSS_SELECTOR, 'span.text')
        active_chapter_text_element_text = active_chapter_text_element.text
        chapter_dropdown_button_element.click()
        logger.debug(f'{current_chapter_text_element_text} - has been successfully navigated to with verified')
        return current_chapter_text_element_text in active_chapter_text_element_text and active_chapter_text_element_text in current_chapter_text_element_text
    else:
        logger.debug(f'{current_chapter_text_element_text} - has been successfully navigated to without verification.')
        return True


def looping_through_verses(current_chapter_number):
    # getting the table
    CURRENT_CHAPTER_GENERATOR = next_verse(current_chapter_number=current_chapter_number)
    verse_table_selector = "#root > div.ui.divided.grid.text-sidebar > div > div.eleven.wide.column.text-column > div.verses-list-container > div > table"
    verse_table_element = WebDriverWait(global_driver, 1).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, verse_table_selector)))
    # getting all the visible rows
    rows = WebDriverWait(verse_table_element, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr')))
    number_of_visible_verses = len(rows)
    logger.info(f'Chapter {current_chapter_number} has {number_of_visible_verses} verses')
    try:
        verse_index = next(CURRENT_CHAPTER_GENERATOR)
    except StopIteration:
        # TODO: save all current progress
        return
    while True:
        logger.info(f'Getting [{current_chapter_number}:{verse_index}]')
        row = rows[verse_index-1]
        # getting the text from each cell
        verse_num_element = WebDriverWait(row, 0.5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'td[class="middle aligned verse-reference"]')))
        verse_words_that_are_also_buttons_weird_ikr_element = WebDriverWait(row, 0.5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button[type="button"]')))
        global_driver.execute_script("arguments[0].scrollIntoView(true);", verse_num_element)
        for button in verse_words_that_are_also_buttons_weird_ikr_element:
            try:
                button.click()
            except ElementClickInterceptedException:
                logger.warning(f"{button.text} was non clickable")
                global_driver.execute_script("arguments[0].scrollIntoView();", button)
                button.click()
            logger.debug(f"{button.text} was clickable")
            logger.debug('asserting button was clicked')
            select_jeton = safe_element_lookup(row, By.CSS_SELECTOR, "div[class='selected-text-underlay']", EC.presence_of_element_located)
            selected_bottom = WebDriverWait(select_jeton, 0.5).until(EC.presence_of_element_located((By.XPATH, "..")))
            logger.debug(f'The selected button is: {selected_bottom.text}')
            assert selected_bottom.text == button.text, "The selected button is not the appropriate one."

            # opening variants
            logger.debug(f'Opening variants')
            time.sleep(1)
            variant_parent = safe_element_lookup(global_driver, By.CSS_SELECTOR, "div[class='sticky-content']", EC.presence_of_element_located)
            variant_selector = "/html/body/div/div[3]/div/div[2]/div/div[2]/button[1]"
            variant_selector_2 = "//*[@id=\"root\"]/div[3]/div/div[2]/div/div[2]/button[1]"
            variant_selector_3 = "button.ui.basic.compact.icon.button"
            variant_selector_4 = "//*[@id=\"root\"]/div[3]/div/div[2]/div/div[2]/button[1]/i[1]"

            #variant_button_element_2 = safe_element_lookup(variant_parent, By.CSS_SELECTOR,
            #                                               variant_selector,
            #                                               EC.element_to_be_clickable, delay=1, return_type='safe')


            variant_button_element_2 = global_driver.find_element(By.CSS_SELECTOR, variant_selector_3)
            variant_button_element_2.click()

            entire_popup_variant_element = safe_element_lookup(global_driver, By.CSS_SELECTOR,
                                                               "div[class='ui page modals dimmer transition visible "
                                                               "active']",
                                                               EC.presence_of_element_located, return_type='safe')
            if entire_popup_variant_element is False:
                entire_popup_variant_element = safe_element_lookup(global_driver, By.CSS_SELECTOR,
                                                                   "div[class='ui page modals dimmer transition "
                                                                   "visible active']",
                                                                   EC.presence_of_element_located, return_type='safe')
            logger.debug(global_driver.page_source)
            # choosing the annotation option
            annotation_option = safe_element_lookup(driver=global_driver, by=By.XPATH,
                                                    search_string="/html/body/div[2]/div/div[1]/a[2]",
                                                    expected_condition=EC.visibility_of_element_located, return_type='safe')
            if not annotation_option:
                a = safe_element_lookup(global_driver, By.CLASS_NAME, search_string="div[role='button'][class='ui basic compact icon button']", expected_condition=EC.presence_of_element_located)

                menu_annotation = safe_element_lookup(global_driver, By.CLASS_NAME, search_string="div[role='button'][class='ui left attached button mobile-sidebar-toggle']", expected_condition=EC.visibility_of_element_located)
                menu_annotation.click()
                annotation_option = safe_element_lookup(driver=global_driver, by=By.XPATH,
                                                    search_string="/html/body/div[2]/div/div[1]/a[2]",
                                                    expected_condition=EC.visibility_of_element_located, return_type='safe')
                annotation_option.click()
            # WebDriverWait(entire_popup_variant_element, 2).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[2]/div/div[1]/a[2]"))))
            annotation_option.click()
            time.sleep(5)
            # getting the table itself
            table_with_variations_element = safe_element_lookup(entire_popup_variant_element, By.CSS_SELECTOR,
                                                                "table[class='ui celled sortable table data-table']",
                                                                EC.presence_of_element_located, )
            # WebDriverWait(entire_popup_variant_element, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table[class='ui celled sortable table data-table']")))
            # wait_until_search_icon_loads = WebDriverWait(table_with_variations_element, 10).until(
            #    EC.visibility_of_element_located(
            #        (By.XPATH, "/html/body/div[2]/div/div[2]/div/div/div[2]/div/div[4]/div/i")))
            logger.debug('Loading table')
            table_text = None
            table_lines = None
            table_status = 'default'
            looking_table = True
            while looking_table:
                logger.debug(f'scraping table again')
                table_text, table_lines = safe_element_lookup(driver=table_with_variations_element, by=By.CSS_SELECTOR,
                                                              search_string="tr",
                                                              expected_condition=EC.visibility_of_all_elements_located,
                                                              return_type='list-string')
                if len(table_text) > 2:
                    logger.debug(f"Table has {len(table_text)} lines")
                    table_status = True
                    break
                for t in table_text[1:]:
                    logger.debug(f'checking: {t}, {"No matching records found." == t}')
                    if "No matching records found." == t:
                        table_status = False
                        looking_table = False
                        break
                    elif 'Loading' in t:
                        looking_table = True
                        break
                time.sleep(1)

            if not table_status:
                logger.info(f"No variations for word: {button.text}")
                pass
            else:
                table_length = len(table_text)
                logger.info(f"We working with {table_length} lines")
                first_line_index, last_line_index = 1, table_length
                currrent_line_index = first_line_index
                logger.info(f"Scraping line from ({(first_line_index, currrent_line_index, last_line_index)})")
                while currrent_line_index < table_length:
                    table_line = table_lines[currrent_line_index]
                    logger.info(f'current line text: {table_line.text}')
                    chapter_verse = safe_element_lookup(table_line, By.CSS_SELECTOR, "td[class='chapter-verse']",
                                                        EC.visibility_of_element_located, return_type='string')
                    arabic = safe_element_lookup(table_line, By.CSS_SELECTOR, "td[class='arabic']",
                                                 EC.visibility_of_element_located, return_type='string')
                    transmission_name = safe_element_lookup(table_line, By.CSS_SELECTOR,
                                                            "td[class='transmission-name']",
                                                            EC.visibility_of_element_located, return_type='string')
                    manual = safe_element_lookup(table_line, By.CSS_SELECTOR, "td[class='manual-name']",
                                                 EC.visibility_of_element_located, return_type='string')
                    page_number = safe_element_lookup(table_line, By.CSS_SELECTOR, "td[class='page-number']",
                                                      EC.visibility_of_element_located, return_type='string')
                    footnotes = safe_element_lookup(table_line, By.CSS_SELECTOR, "td[class='footnotes']",
                                                    EC.visibility_of_element_located, return_type='string')
                    logger.debug(
                        f"Chapter: {chapter_verse}, Arabic: {arabic}, Transmission Name: {transmission_name}, Manual Name: {manual}, Page Number: {page_number}, Footnotes: {footnotes}")
                    currrent_line_index += 1

            # Check if there's a load more button

            # press the return button and look at another word.
            back_to_text_button_element = WebDriverWait(entire_popup_variant_element, 0.5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "button[class='ui primary button']")))
            back_to_text_button_element.click()

            time.sleep(1)


def safe_element_lookup(driver, by, search_string, expected_condition, retries=5, delay=2, return_type='normal'):
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, delay).until(expected_condition((by, search_string)))
            if return_type == 'normal':
                return element
            elif return_type == 'string':
                return element.text
            elif return_type == 'list-string':
                return [i.text for i in element], element
        except TimeoutException:
            time.sleep(0.5)
            logger.warning(f'Element not found, retrying attempt {attempt + 1}/{retries}')
            continue
        except StaleElementReferenceException:
            time.sleep(0.5)
            logger.warning(f'Stale element reference, retrying attempt {attempt + 1}/{retries}')
            continue
    if return_type == 'safe':
        return False
    raise Exception(f'We did not find the element after {retries} attempts.')


if __name__ == '__main__':
    CHAPTER_VERSE_NUMBER = {1: [(6, 7)], 2: [(1, 286)], 3: [(1, 200)], 4: [(1, 176)], 5: [(1, 120)], 6: [(1, 165)],
                            7: [(1, 206)], 8: [(1, 75)], 9: [(1, 127)], 10: [(1, 109)], 11: [(1, 123)], 12: [(1, 111)],
                            13: [(1, 43)], 14: [(1, 52)], 15: [(1, 99)], 16: [(1, 128)], 17: [(1, 111)], 18: [(1, 110)],
                            19: [(1, 98)], 20: [(1, 135)], 21: [(1, 112)], 22: [(1, 78)], 23: [(1, 118)], 24: [(1, 64)],
                            25: [(1, 77)], 26: [(1, 227)], 27: [(1, 93)], 28: [(1, 88)], 29: [(1, 69)], 30: [(1, 60)],
                            31: [(1, 34)], 32: [(1, 30)], 33: [(1, 73)], 34: [(1, 54)], 35: [(1, 45)], 36: [(1, 83)],
                            37: [(1, 182)], 38: [(1, 88)], 39: [(1, 75)], 40: [(1, 85)], 41: [(1, 54)], 42: [(1, 53)],
                            43: [(1, 89)], 44: [(1, 59)], 45: [(1, 37)], 46: [(1, 35)], 47: [(1, 38)], 48: [(1, 29)],
                            49: [(1, 18)], 50: [(1, 45)], 51: [(1, 60)], 52: [(1, 49)], 53: [(1, 62)], 54: [(1, 55)],
                            55: [(1, 78)], 56: [(1, 96)], 57: [(1, 29)], 58: [(1, 22)], 59: [(1, 24)], 60: [(1, 13)],
                            61: [(1, 14)], 62: [(1, 11)], 63: [(1, 11)], 64: [(1, 18)], 65: [(1, 12)], 66: [(1, 12)],
                            67: [(1, 30)], 68: [(1, 52)], 69: [(1, 52)], 70: [(1, 44)], 71: [(1, 28)], 72: [(1, 28)],
                            73: [(1, 20)], 74: [(1, 56)], 75: [(1, 40)], 76: [(1, 31)], 77: [(1, 50)], 78: [(1, 40)],
                            79: [(1, 46)], 80: [(1, 42)], 81: [(1, 29)], 82: [(1, 19)], 83: [(1, 36)], 84: [(1, 25)],
                            85: [(1, 22)], 86: [(1, 17)], 87: [(1, 19)], 88: [(1, 26)], 89: [(1, 30)], 90: [(1, 20)],
                            91: [(1, 15)], 92: [(1, 21)], 93: [(1, 11)], 94: [(1, 8)], 95: [(1, 8)], 96: [(1, 19)],
                            97: [(1, 5)], 98: [(1, 8)], 99: [(1, 8)], 100: [(1, 11)], 101: [(1, 11)], 102: [(1, 8)],
                            103: [(1, 3)], 104: [(1, 9)], 105: [(1, 5)], 106: [(1, 4)], 107: [(1, 7)], 108: [(1, 3)],
                            109: [(1, 6)], 110: [(1, 3)], 111: [(1, 5)], 112: [(1, 4)], 113: [(1, 5)], 114: [(1, 6)]}
    load_json(data={"chapters": CHAPTER_VERSE_NUMBER})
    # loop global variables
    CHAPTER_NUMBER_GENERATOR = next_chapter()
    NUMBER_OF_ERRORS_IN_CURRENT_CHAPTER = 0
    ROBUST_MODE = False
    SCROLL_TO_THE_BOTTOM_INSTANTLY = False
    CHAPTER_LOOP_FLAG = True
    CHAPTER_VERSE_RESUME_DATA = load_json()

    # initializing driver and action chains
    global_driver, global_action = get_driver()
    global_driver.set_window_position(54, 40)
    EREQURAN_HANDLE = global_driver.current_window_handle

    chapter_number = next(CHAPTER_NUMBER_GENERATOR)
    logger.debug('starting loop')
    while CHAPTER_LOOP_FLAG:
        # navigation to the proper chapter
        page_status = go_to_chapter(chapter_number, driver=global_driver, check_if_transition=ROBUST_MODE)
        if not page_status:
            logger.error(
                f'Failed to navigate to chapter {chapter_number}. RETRYING {NUMBER_OF_ERRORS_IN_CURRENT_CHAPTER}/5')
            if NUMBER_OF_ERRORS_IN_CURRENT_CHAPTER <= 5:
                NUMBER_OF_ERRORS_IN_CURRENT_CHAPTER += 1
                continue
            else:
                logger.error(
                    f'Maximum number of errors in current chapter reached, stopping scraping for chapter {chapter_number}.')
                break
        else:
            NUMBER_OF_ERRORS_IN_CURRENT_CHAPTER = 0
            try:
                chapter_number = next(CHAPTER_NUMBER_GENERATOR)
            except StopIteration:
                CHAPTER_LOOP_FLAG = False
                break
        time.sleep(1)  # wait for page to load

        logger.debug('Loading all verses')
        # looping through each word, then verse.
        verse_table_more_button_selector = "button[class='ui primary button']"
        #   click the load more button until entire chapter is loaded
        #   TODO: Good luck figuring out how to deal with really long verses. Maybe do gradual scroll down?

        while SCROLL_TO_THE_BOTTOM_INSTANTLY:
            try:
                verse_table_button_element = WebDriverWait(global_driver, 1).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, verse_table_more_button_selector)))
            except TimeoutException:
                break
            global_driver.execute_script("arguments[0].scrollIntoView();", verse_table_button_element)
            verse_table_button_element.click()
        # getting variant buttons as well as setting the filters
        variant_button_element = safe_element_lookup(global_driver, By.CSS_SELECTOR,
                                                     "button[class='ui basic compact icon button']",
                                                     EC.presence_of_element_located)
        variant_button_element.click()
        #   load variant popup
        entire_popup_variant_element = safe_element_lookup(global_driver, By.CSS_SELECTOR,
                                                           "div[class='ui page modals dimmer transition visible active']",
                                                           EC.presence_of_element_located)
        variant_setting_button = WebDriverWait(entire_popup_variant_element, 0.5).until(EC.visibility_of_element_located
                                                                                        ((By.CSS_SELECTOR,
                                                                                          "button[aria-label='Filter'][class='ui basic icon button']")))
        variant_setting_button.click()
        #   load setting popup
        setting_variant_popup = safe_element_lookup(global_driver, By.CSS_SELECTOR, "div[class='ui top aligned page modals dimmer transition visible active']", EC.presence_of_element_located)
        text_input_variant_settings = WebDriverWait(setting_variant_popup, 1).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[class='search']")))
        variant_settings_button_element = WebDriverWait(setting_variant_popup, 1).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "button[type='submit']")))
        logger.info(f"We're at element: {text_input_variant_settings.text}")
        text_input_variant_settings.send_keys(Keys.ENTER)
        text_input_variant_settings.send_keys("The Ten Readings")  # sughar
        text_input_variant_settings.send_keys(Keys.ENTER)
        text_input_variant_settings.send_keys("The Ten Readings")  # kubra
        text_input_variant_settings.send_keys(Keys.ENTER)
        text_input_variant_settings.send_keys("Manuscript reading")  # manuscript
        text_input_variant_settings.send_keys(Keys.ENTER)
        text_input_variant_settings.send_keys("Grammatical readings")  # Grammatical readings
        text_input_variant_settings.send_keys(Keys.ENTER)
        text_input_variant_settings.send_keys(Keys.ESCAPE)
        variant_settings_button_element.click()
        back_to_text_button_element = WebDriverWait(entire_popup_variant_element, 0.5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "button[class='ui primary button']")))
        back_to_text_button_element.click()
        time.sleep(5)

        looping_through_verses(chapter_number)
        input('Go to next chapter')
