import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json, base64
import os

def send_devtools(driver, cmd, params={}):
  resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
  url = driver.command_executor._url + resource
  body = json.dumps({'cmd': cmd, 'params': params})
  response = driver.command_executor._request('POST', url, body)
  if response.get('status'):
    raise Exception(response.get('value'))
  return response.get('value')

def get_pdf_from_html(html_content, chromedriver='/usr/local/bin/chromedriver', print_options = {}):
  webdriver_options = Options()
  webdriver_options.add_argument('--headless')
  webdriver_options.add_argument('--disable-gpu')
  driver = webdriver.Chrome(chromedriver, options=webdriver_options)

  driver.get("data:text/html;charset=utf-8," + html_content);

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


filename = "invoice.pdf"
html = "<html>test</html>"

result = get_pdf_from_html(inv, chromedriver='/usr/local/bin/chromedriver')
with open(filename, 'wb') as file:
  file.write(result)