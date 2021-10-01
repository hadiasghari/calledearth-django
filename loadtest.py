# This is a manually run script that places load on the django/heroku server
# It simulates a webuser (picks an emoji, sends energy & writes prompts in a loop)
# It requires `python3-selenium` package to work


# some ideas for future version of script:
# - can ask how many browsers to run (currently run script once per browser)
# - could also quite after X seconds (and close the browser window!)
# - for simpler testing, we could have slightly different titles in our webpages


from selenium import webdriver
from random import randint
from time import sleep

browser = webdriver.Chrome()  # 1

# lets start
browser.get("http://calledearth.herokuapp.com")

# pick emoji
ptxt = browser.find_element_by_tag_name("body").text
assert "Pick your emoji" in ptxt
elems = browser.find_elements_by_tag_name("span")
emoji = elems[randint(0, len(elems)-1)]
emoji.click()

# browser tag
tag = randint(100, 999)
n = 0

# maybe only continue for X seconds, then exit...
while True:
    ptxt = browser.find_element_by_tag_name("body").text
    if "feeling" in ptxt or 'DANCE!' in ptxt or 'more' in ptxt:
        # cheer prompt, send random energy
        elems = browser.find_elements_by_tag_name("img")
        powerup = elems[randint(0, len(elems)-1)]
        powerup.click()
    else:
        # writing prompt. send a random hello
        txtarea = browser.find_element_by_tag_name("textarea")
        n += 1
        txtarea.send_keys("hello friends #" + str(tag) + "." + str(n) )
        f = browser.find_element_by_tag_name("form")
        f.submit()
    # sleep depending on intensity!
    sleep(1)
