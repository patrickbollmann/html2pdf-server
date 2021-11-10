import flask
from flask import request
from flask import send_file
from flask import after_this_request
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import base64
import os

chromedriver_path = "/usr/local/bin/chromedriver"

app = flask.Flask(__name__)
app.config["DEBUG"] = True


def send_devtools(driver, cmd, params={}):
    resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
    url = driver.command_executor._url + resource
    body = json.dumps({'cmd': cmd, 'params': params})
    response = driver.command_executor._request('POST', url, body)
    if response.get('status'):
        raise Exception(response.get('value'))
    return response.get('value')


def get_pdf_from_html(html_content, chromedriver=chromedriver_path, print_options={}):
    webdriver_options = Options()
    webdriver_options.add_argument('--headless')
    webdriver_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(chromedriver, options=webdriver_options)

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
    result = get_pdf_from_html(
        html, chromedriver=chromedriver_path)
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
    pdf = html2pdf(str(html), filename)
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


app.run()
