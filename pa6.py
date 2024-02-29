#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 15:44:31 2024

@author: rachellecho
"""
import time
import csv
from urllib.parse import urljoin
import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "http://collegecatalog.uchicago.edu/"

def programs_of_study(base):
    '''go to programs of study page'''
    programs = requests.get(base, timeout = 3)
    soup = BeautifulSoup(programs.text, "html.parser")
    programs_of_study_link = soup.find("a", href = "/thecollege/programsofstudy/")
    if programs_of_study_link is None:
        print("Could not find link to Programs of Study page.")
        return None
    programs_of_study_url = urljoin(base, programs_of_study_link["href"])
    return programs_of_study_url

def to_department(programs_of_study_url):
    '''retrieving departments'''
    department_urls = []
    response = requests.get(programs_of_study_url, timeout = 3)
    if response.status_code != 200:
        print(f"Failed to fetch Programs of Study page (status code: {response.status_code})")
        return department_urls
    soup = BeautifulSoup(response.text, "html.parser")
    department_links = soup.find_all("a", href=True)
    for link in department_links:
        href = link["href"]
        if href.startswith("/thecollege/") and href.endswith("/"):
            excluded = ["thecurriculum", "minors", "academicregulationsprocedures", "examinationcreditandtransfercredit",
                        "transfercredit", "interdisciplinaryopportunities", "jointdegreeprograms",
                        "offcampusstudyprograms", "preparationforprofessionalstudy", "researchopportunities",
                        "archives", "academiccalendar"]
            if not any(keyword in href for keyword in excluded):
                department_url = urljoin(programs_of_study_url, href)
                department_urls.append(department_url)
    return department_urls

def course_information(department_url):
    '''Extracting course information'''
    course_info_list = []
    response = requests.get(department_url, timeout = 3)
    if response.status_code != 200:
        print(f"Failed to fetch data from department URL: {department_url} (status code: {response.status_code})")
        return course_info_list
    soup = BeautifulSoup(response.text, "html.parser")
    course_elements = soup.find_all("div", class_="courseblock main")
    subsequence_blocks = soup.find_all("div", class_="courseblock subsequence")
    for course_element in course_elements + subsequence_blocks:
        if course_element.find("p", class_="courseblockdetail"):
            course_title_elem = course_element.find("p", class_="courseblocktitle")
            description_elem = course_element.find("p", class_="courseblockdesc")
            if description_elem:
                course_title = course_title_elem.text.strip() if course_title_elem else "N/A"
                description = description_elem.text.strip()
                detail_elem = course_element.find("p", class_="courseblockdetail")
                instructor = terms_offered = equivalent_courses = pre_req = "N/A"
                if detail_elem:
                    lines = detail_elem.get_text(separator="\n").split("\n")
                    for line in lines:
                        if "Instructor(s):" in line:
                            parts = line.split("Instructor(s):")
                            if len(parts) > 1:
                                instructor = parts[1].strip()
                                if "Terms Offered:" in instructor:
                                    instructor_terms_parts = instructor.split("Terms Offered:")
                                    instructor = instructor_terms_parts[0].strip()
                                    terms_offered = instructor_terms_parts[1].strip()
                        elif "Equivalent Course(s):" in line:
                            equivalent_courses = line.split("Equivalent Course(s):")[1].strip()
                        elif "Prerequisite(s):" in line:
                            pre_req = line.split("Prerequisite(s):")[1].strip()
                course_info = {
                    'Course Number': course_title,
                    'Description': description,
                    'Instructor': instructor,
                    'Terms Offered': terms_offered,
                    'Equivalent Courses': equivalent_courses,
                    'Prerequisite': pre_req}
                course_info_list.append(course_info)
                if course_title_elem:
                    course_title_text = course_title_elem.text.strip()
                    course_title_text = course_title_text.encode('ascii', 'ignore').decode()
                    course_code_title_parts = course_title_text.split(".")
                    course_code = course_code_title_parts[0].strip()
                    course_info['Course Number'] = course_code
                else:
                    course_info['Course Number'] = "N/A"
    return course_info_list

def make_csv(course_info_list):
    '''saving relevant information as csv'''
    with open('college_courses.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Course Number', 'Description', 'Instructor', 'Terms Offered', 'Equivalent Courses', 'Prerequisite']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for course_info in course_info_list:
            writer.writerow(course_info)

def final():
    '''retrieving all course information'''
    programs_of_study_url = programs_of_study(BASE_URL)
    if programs_of_study_url:
        department_urls = to_department(programs_of_study_url)
        all_course_info = []
        for department_url in department_urls:
            print(f"Extracting course information from department: {department_url}")
            course_info = course_information(department_url)
            if course_info:
                all_course_info.extend(course_info)
                time.sleep(3)
            else:
                print(f"Failed to extract course information from department: {department_url}")
        if all_course_info:
            make_csv(all_course_info)
            print("Course information written to college_courses.csv")

college_courses = pd.read_csv("college_courses.csv")
len(college_courses)

df = pd.DataFrame(college_courses)
df["Department"]=df["Course Number"].str[:4]
df.groupby("Department")["Course Number"].count().idxmax()

quarter_counts = df['Terms Offered'].str.split().str[0].value_counts()
print("Number of classes offered in each quarter:", quarter_counts)