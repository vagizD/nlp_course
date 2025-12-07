from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import requests
from typing import List, Dict, Optional


def parse_tasks() -> list[dict[str, str]]:
    load_dotenv()
    lk_cookie = os.getenv("LK_SESSION_COOKIE")

    url = "https://lk.dataschool.yandex.ru/learning/assignments/"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; parser/1.0)"
    }

    session = requests.Session()
    if lk_cookie:
        session.cookies.set("Session_id", lk_cookie, domain="lk.dataschool.yandex.ru")

    resp = session.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    try:
        open_tasks_table = soup.find("h3", string="Открытые задания").find_next("table")
    except AttributeError:
        raise RuntimeError("Could not find the open tasks table on the page. Check your cookie")

    tasks = []

    for row in open_tasks_table.find_all("tr", class_="noop"):
        date_block = row.find("div", class_="assignment-date")
        if date_block:
            date = date_block.find("span", class_="nowrap").get_text(strip=True)
            time = date_block.get_text(strip=True).replace(date, "")
            deadline = f"{date} {time.strip()}"
        else:
            deadline = None

        assignment_link = row.find_all("a")[0]
        course_link = row.find_all("a")[1]

        assignment_name = assignment_link.get_text(strip=True)
        course_name = course_link.get_text(strip=True)

        tasks.append({
            "course": course_name,
            "assignment": assignment_name,
            "deadline": deadline
        })

    for t in tasks:
        print(f"{t['course']}: {t['assignment']} — {t['deadline']}")

    return tasks


# TODO: Implement function to get a list of upcoming lectures from learning/timetable/
def parse_lectures() -> list[dict[str, str]]:
    load_dotenv()
    lk_cookie = os.getenv("LK_SESSION_COOKIE")

    url = "https://lk.dataschool.yandex.ru/learning/timetable/"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; parser/1.0)"
    }

    session = requests.Session()
    if lk_cookie:
        session.cookies.set("Session_id", lk_cookie, domain="lk.dataschool.yandex.ru")

    resp = session.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    try:
        timetable = soup.select("div.row.timetable-main-row")
    except AttributeError:
        raise RuntimeError("Could not find the lecture timetable.")

    results: List[Dict[str, Optional[str]]] = []

    for block in timetable:
        # Inside the block, dates are in <h4>, each followed by a <table>
        for date_h4 in block.find_all("h4"):
            date_text = date_h4.get_text(strip=True)

            # The table right after this date heading
            table = date_h4.find_next_sibling("table")
            if not table:
                continue

            # Go through all lecture/seminar rows (skip the header row with <th>)
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 4:
                    continue

                # Time is in the first column
                time_text = cells[0].get_text(strip=True)

                # Subject name is in the second column's link text
                subject_link = cells[2].find("a")
                subject = subject_link.get_text(strip=True) if subject_link else cells[2].get_text(strip=True)

                # Place is in the fourth column, usually inside an <a>
                place_link = cells[3].find("a")
                place = place_link.get_text(strip=True) if place_link else cells[3].get_text(strip=True)

                # Type (Seminar/Lecture/etc) is in the last column inside span.badge
                type_cell = cells[4] if len(cells) > 4 else None
                lecture_type: Optional[str] = None
                if type_cell:
                    badge = type_cell.find("span", class_="badge")
                    if badge:
                        lecture_type = badge.get_text(strip=True)

                # Combine date + time into one string
                datetime_str = f"{date_text} {time_text}"

                results.append({
                    "Subject": subject,
                    "Datetime": datetime_str,
                    "Type": lecture_type,
                    "Place": place,
                })

    return results