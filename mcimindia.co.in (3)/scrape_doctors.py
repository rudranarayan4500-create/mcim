from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
json_file = os.path.join(script_dir, "doctors_data.json")
html_file = os.path.join(script_dir, "mcimindia.co.in", "FindDoctor.html")

target_start = 1
target_end = 10000
start_reg = target_start
scraped_ids = set()
existing_data = []

if os.path.exists(json_file):
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)

        # Keep only valid doctor records and ignore broken header artifacts
        cleaned_data = []
        for item in existing_data:
            if (isinstance(item, dict)
                    and item.get("Doctor's Name")
                    and item.get("Registration No")
                    and isinstance(item.get("Requested Registration No"), int)):
                cleaned_data.append(item)
        if len(cleaned_data) != len(existing_data):
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, indent=4, ensure_ascii=False)
        existing_data = cleaned_data

        scraped_ids = {
            item["Requested Registration No"]
            for item in existing_data
            if target_start <= item["Requested Registration No"] <= target_end
        }

        if scraped_ids:
            for candidate in range(target_start, target_end + 1):
                if candidate not in scraped_ids:
                    start_reg = candidate
                    break
            else:
                start_reg = target_end + 1
                print(f"Data up to Reg No {target_end} appears already completed in your JSON file.")

            if start_reg <= target_end:
                print(f"Detected existing data. Resuming automatically from Reg No: {start_reg}")
    except Exception:
        print(f"Could not read progress file. Starting from default boundary ({target_start}).")
else:
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump([], f)

# Step 2: Run Scraping Loop from start_reg up to target_end
if start_reg <= target_end:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, 15)
    url = "https://mcimindia.co.in/FindDoctor"

    for reg_no in range(start_reg, target_end + 1):
        if reg_no in scraped_ids:
            continue

        # 3-Attempt Retry wrapper to fight temporary web lag/timeouts
        for attempt in range(1, 4):
            try:
                print(f"\nProcessing Registration No: {reg_no} (Attempt {attempt}/3)")
                driver.get(url)

                # 1. First, pick the correct registration type choice inside dropdown
                dropdown_element = wait.until(EC.presence_of_element_located((By.ID, "ddType")))
                dropdown = Select(dropdown_element)
                dropdown.select_by_visible_text("Find by Registration No (Only Number)")
                time.sleep(1.5)

                # 2. Complete clean typing of current registration item
                reg_box = wait.until(EC.presence_of_element_located((By.ID, "txtSearchValue")))
                reg_box.clear()
                reg_box.send_keys(str(reg_no))

                # 3. Read and automatically compute the live math captcha calculation
                captcha_element = wait.until(EC.presence_of_element_located((By.ID, "lblCaptcha")))
                match = re.search(r'(\d+)\s*\+\s*(\d+)', captcha_element.text)
                if not match:
                    match = re.search(r'(\d+)\s*\+\s*(\d+)', driver.page_source)

                if match:
                    answer = int(match.group(1)) + int(match.group(2))
                    captcha_box = wait.until(EC.presence_of_element_located((By.ID, "txtCaptchaAnswer")))
                    captcha_box.clear()
                    captcha_box.send_keys(str(answer))
                else:
                    print(" -> CAPTCHA could not be read. Retrying step...")
                    time.sleep(2)
                    continue

                # 4. Fire search submit click
                search_btn = wait.until(EC.element_to_be_clickable((By.ID, "btnSearch")))
                driver.execute_script("arguments[0].click();", search_btn)
                time.sleep(3)

                # 5. Track search container result rendering
                try:
                    results_table = wait.until(EC.presence_of_element_located((By.ID, "searchResults")))
                    if not results_table.is_displayed():
                        print(f" -> No records displayed for Reg No {reg_no}")
                        break
                except:
                    print(f" -> Results table not found for Reg No {reg_no}. Retrying...")
                    time.sleep(2)
                    continue

                # 6. Parse row segments explicitly out of table body
                rows = results_table.find_elements(By.XPATH, ".//tbody/tr")
                
                if rows:
                    has_data = False
                    
                    for row in rows:
                        cells = row.find_elements(By.XPATH, "./td")
                        
                        # 7. Map exactly to your 8 column requirements layout structure
                        if len(cells) >= 8:
                            doctor_profile = {
                                "Requested Registration No": reg_no,
                                "Sr.": cells[0].text.strip(),
                                "Registration No": cells[1].text.strip(),
                                "Registration Date": cells[2].text.strip(),
                                "Doctor's Name": cells[3].text.strip(),
                                "Gender": cells[4].text.strip(),
                                "Qualification": cells[5].text.strip(),
                                "MCIM Status": cells[6].text.strip(),
                                "Location": cells[7].text.strip()
                            }
                            
                            # Filter out dummy duplicate table headers or blank cells
                            if doctor_profile["Sr."] != "" and "Registration" not in doctor_profile["Sr."]:
                                has_data = True
                                current_name = doctor_profile["Doctor's Name"]
                                print(f" -> Found and extracted: {current_name}")
                                
                                # Stream item payload straight to active storage file
                                with open(json_file, "r", encoding="utf-8") as f:
                                    current_data = json.load(f)
                                
                                current_data.append(doctor_profile)
                                
                                with open(json_file, "w", encoding="utf-8") as f:
                                    json.dump(current_data, f, indent=4, ensure_ascii=False)
                    
                    if not has_data:
                        print(f" -> No valid doctor profiles parsed for Reg No {reg_no}")
                    break 
                else:
                    print(f" -> Empty rows for Reg No {reg_no}")
                    break

            except KeyboardInterrupt:
                print("\nScript manually paused. Progress remains securely saved.")
                driver.quit()
                exit(0)
            except Exception as e:
                print(f" -> Error on attempt {attempt} for Reg No {reg_no}: {e}")
                time.sleep(2)
                if attempt == 3:
                    print(f" -> Skipped Reg No {reg_no} after 3 failed attempts.")

    driver.quit()

print(f"\nScraping Target Range [{target_start}-{target_end}] Run Completed.")

# --- STEP 3: DATA INJECTION BLOCK FOR LOCAL TEMPLATE HTML ---
try:
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            doctors_data = json.load(f)

        # Clean any malformed records before injection
        doctors_data = [
            item for item in doctors_data
            if isinstance(item, dict)
            and item.get("Doctor's Name")
            and item.get("Registration No")
            and isinstance(item.get("Requested Registration No"), int)
        ]

        if os.path.exists(html_file):
            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()

            new_array = json.dumps(doctors_data, indent=4, ensure_ascii=False)
            new_array_js = f"var doctorsData = {new_array};"

            import re
            pattern = re.compile(r"var\s+doctorsData\s*=\s*\[.*?\];", re.DOTALL)
            new_html, count = pattern.subn(new_array_js, html_content, count=1)

            if count == 1:
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(new_html)
                print(f"Successfully updated {html_file} with {len(doctors_data)} doctor records.")
            else:
                print("Could not replace the doctorsData array in HTML.")
        else:
            print(f"Local file injection skipped: '{html_file}' template path does not exist.")
except Exception as e:
    print(f"Error updating local HTML asset block: {e}")