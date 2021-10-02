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


while True:
    browser = webdriver.Chrome()

    # lets start
    print("Connecting!")
    browser.get("http://calledearth.herokuapp.com")
    #browser.get("http://127.0.0.1:8000")

    # pick emoji
    ptxt = browser.find_element_by_tag_name("body").text
    assert "Pick your emoji" in ptxt
    elems = browser.find_elements_by_tag_name("span")
    emoji = elems[randint(0, len(elems)-1)]
    print("Our emoji is ", str(emoji.text))
    emoji.click()

    # browser tag
    tag = randint(100, 999)
    n = 0
    bye = False

    # maybe only continue for X seconds, then exit...
    while True:
        try:
            ptxt = browser.find_element_by_tag_name("body").text
        except Exception as ex:
            print(ex)
            break
        if "feeling" in ptxt or 'DANCE!' in ptxt or 'more' in ptxt:
            # cheer prompt, send random energy
            elems = browser.find_elements_by_tag_name("img")
            if not elems:
                bye = True
                print("THE END!")
                break  # we must have reached the end!
            powerup = elems[randint(0, len(elems)-1)]
            try:
                print("Power Up!")
                powerup.click()
            except Exception as ex:
                print(ex)
                break
        else:
            # writing prompt. send a random hello
            try:
                txtarea = browser.find_element_by_tag_name("textarea")
            except Exception as ex:
                print(ex)  # ended or unexpected, quit
                break
            n += 1
            print("Texting!")
            txtarea.send_keys("hello bot friends #" + str(tag) + "." + str(n) )
            f = browser.find_element_by_tag_name("form")
            f.submit()
        # sleep depending on intensity!
        sleep(2)

    browser.close()

    if bye:
        break

    sleep(10)
