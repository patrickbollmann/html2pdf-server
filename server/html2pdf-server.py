import flask
from flask import request
from flask import send_file
from flask import after_this_request
import sys
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import json
import base64
import os

chromedriver_path = "/usr/local/bin/chromedriver"

app = flask.Flask(__name__)
app.config["DEBUG"] = False

def set_chrome_options() -> None:
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    return chrome_options

def send_devtools(driver, cmd, params={}):
    resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
    url = driver.command_executor._url + resource
    body = json.dumps({'cmd': cmd, 'params': params})
    response = driver.command_executor._request('POST', url, body)
    if response.get('status'):
        raise Exception(response.get('value'))
    return response.get('value')


def get_pdf_from_html(html_content, print_options={}):
    driver = webdriver.Chrome(options=set_chrome_options())

    driver.get("data:text/html;charset=utf-8," + html_content)

    calculated_print_options = {
        'landscape': False,
        'displayHeaderFooter': False,
        'printBackground': True,
        'preferCSSPageSize': True,
    }
    calculated_print_options.update(print_options)
    result = send_devtools(driver, "Page.printToPDF", calculated_print_options)
    driver.quit()

    return base64.b64decode(result['data'])


def html2pdf(html):
    result = get_pdf_from_html(html)
    return result


@app.route('/', methods=['GET'])
def home():
    return "<h1>HTML 2 PDF Server</h1><p>use post request at /render to render your HTML into a pdf file. As Parameters you need to specify 'html' with the htnl string and 'filename' like invoice.pdf</p>"


@app.route('/render', methods=['POST'])
def render():

    # get parameters from request
    html = request.form["html"]
    filename = request.form["filename"]

    # print html for debug
    print(html)

    # render html
    print("rendering "+filename+"...")
    pdf = html2pdf(str(html))
    # store pdf file
    print("storing "+filename+"...")
    with open(filename, 'wb') as file:
        file.write(pdf)

    # return stored file
    print("returning "+filename+"...")

    @after_this_request
    def remove_file(response):
        print("removing sent file...")
        try:
            os.remove(filename)
        except Exception as error:
            app.logger.error("Error removing or closing downloaded file handle", error)
        return response
    return send_file(filename)


app.run(host='0.0.0.0')
