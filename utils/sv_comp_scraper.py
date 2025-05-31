from pydantic import BaseModel, PrivateAttr, computed_field
import os
from bs4 import BeautifulSoup
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from .reader import VerificationResults, VerifierResult, Verifier, VerificationTask, get_file


def get_table(soup: BeautifulSoup) -> VerificationResults:
    table = soup.find('div', class_='main-table')
    columns = get_table_headers(table)
    results = get_table_rows(table)
    verification_results = []
    
    for row in results:
        for col_i in range(len(columns)):
            i = col_i * 6 + 1

            cpu = row[i+3].replace("s", "").replace(",", ".")
            memory = row[i+4].replace("MB", "").replace(",", ".")
            verification_results.append(
                VerifierResult(
                    # i is empty
                    status=row[i+1],
                    raw_core=row[i+2],
                    cpu=float(cpu) if len(cpu)>0 else None,
                    memory=float(memory) if len(memory)>0 else None,
                    # energy i+5 is empty
                    verifier=Verifier(name=columns[col_i]),
                    verification_task=VerificationTask(name=row[0])
                )
            )

    return VerificationResults(
        verification_results=verification_results,
    )



def get_table_headers(soup: BeautifulSoup) -> list:
    table_header = soup.find('div', class_='table-header')
    headers = [header.text.strip() for header in table_header.find_all('div', class_="th header outer undefined")]
    return headers

def get_table_rows(soup: BeautifulSoup) -> list:
    table = soup.find("div", class_="table-body")
    results = []
    for row in table.find_all("div", class_="tr"):
        cells = row.find_all("div", class_="td")
        row_results = []
        for c in cells:
            row_results.append(c.text.strip())
        results.append(row_results)
    return results

def save_all_pages(url: str, output_dir: str = "tables", overwrite:bool=False):
    os.makedirs(output_dir, exist_ok=True)
    
    file_name = get_file(url, output_dir)
    if os.path.exists(file_name) and not overwrite:
        print(f"URL already scraped: {url}")
        return None

    driver = webdriver.Chrome()
    driver.get(url)
    wait = WebDriverWait(driver, 20)

    page_num = 1
    prev_page = None

    all_verification_results = VerificationResults()
    while True:
        # Wait for the table to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "main-table")))

        # Save current page
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        if prev_page == soup.prettify():
            print("No new page loaded, stopping.")
            break
        
        verification_results = get_table(soup)

        all_verification_results.extend(verification_results)

        # Try to find and click the "Next" button
        next_button = driver.find_element(By.ID, "pagination-next")
        next_class = next_button.get_attribute("class")

        # Check if "Next" is disabled
        if "disabled" in next_class.lower():
            print("Reached last page.")
            break

        # Scroll to and click the next button
        driver.execute_script("arguments[0].scrollIntoView();", next_button)
        next_button.click()

        # Optional: Wait for a status change or a brief pause to allow content to load
        time.sleep(2)
        page_num += 1
        prev_page = soup.prettify()


    driver.quit()
    
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(all_verification_results.model_dump_json(indent=2))
