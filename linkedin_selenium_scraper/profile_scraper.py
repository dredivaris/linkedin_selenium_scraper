import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait


class LinkedinProfile:
  def __init__(self, url):
    # verify proper linkedin profile url:
    is_linkedin_profile_url = re.compile(r'http://linkedin\.com/in/[a-zA-Z]+')
    matched = is_linkedin_profile_url.match(url)

    if not matched:
      return

    # setup selenium & get page
    profile = webdriver.Firefox(url)
    profile.implicitly_wait(2)
    profile.get("")
    WebDriverWait(profile, 10)
    profile.execute_script("window.scrollBy(0,100000)")

    # handle name, headline and summary
    self.name = profile.find_element_by_id('name').text
    self.connections = profile.find_element_by_class_name('member-connections').\
      text.replace('\n', ' ')
    self.headline = profile.find_element_by_class_name('profile-overview-content').\
      find_element_by_class_name('headline').text
    self.locality = profile.find_element_by_id('demographics').\
      find_element_by_class_name('locality').text
    self.industry = profile.find_element_by_xpath('//*[@id="demographics"]/dd[2]').text

    current_position = profile.find_element_by_xpath(
        '//*[@id="topcard"]/div[1]/div[2]/div/table/tbody/tr[1]/td/ol/li/span/a').text

    previous_positions = profile.find_element_by_xpath(
      '//*[@id="topcard"]/div[1]/div[2]/div/table/tbody/tr[2]/td/ol').\
      find_elements_by_tag_name('li')
    previous_positions = [p.text for p in previous_positions]

    education = profile.find_element_by_xpath(
        '//*[@id="topcard"]/div[1]/div[2]/div/table/tbody/tr[3]/td/ol/li/a').text

    self.summary_info = SummaryInfo(current_position, previous_positions, education)

    # parse experience
    positions = profile.find_elements_by_class_name('position')
    self.experiences = []
    for position in positions:
      experience = Experience()
      company_url = position.find_element_by_class_name('logo').find_element_by_tag_name('a')
      experience.company_profile_url = company_url.get_attribute('href')
      experience.company_image_url = company_url.find_element_by_tag_name('img').\
        get_attribute('src')

      experience.position_title = position.find_element_by_class_name('item-title').\
        find_element_by_tag_name('a').text
      experience.position_title_url = position.find_element_by_class_name('item-title').\
        find_element_by_tag_name('a').get_attribute('href')

      experience.company_title = position.find_element_by_class_name('item-subtitle').\
        find_element_by_tag_name('a').text

      experience.date_range = position.find_element_by_class_name('meta').\
        find_element_by_class_name('date-range').text
      from_to_times = position.find_element_by_class_name('meta').\
        find_element_by_class_name('date-range').find_elements_by_tag_name('time')
      experience.from_date = from_to_times[0].text
      experience.to_date = None
      if len(from_to_times) > 1:
        experience.to_date = from_to_times[1].text
      experience.time_at_position = re.search(r"\((.*)\)", experience.date_range).group(1)

      experience.description = position.find_element_by_class_name('description').text
      self.experiences.append(experience)  # TODO: append at start/end to have it be chronological?

    # get certifications
    certifications = profile.find_elements_by_class_name('certification')
    self.certifications = []
    for cert in certifications:
      print ('------------------------------ at: ', i)
      certification = Certification()

      try:
        certification.issuer_url = cert.find_element_by_class_name('logo').\
          find_element_by_tag_name('a').get_attribute('href')
      except NoSuchElementException:
        certification.issuer_url = None

      try:
        certification.cert_url = cert.find_element_by_class_name('item-title').\
          find_element_by_tag_name('a').get_attribute('href')
      except NoSuchElementException:
        certification.cert_url = None

      certification.issuer_image_url = '' # TODO
      try:
        certification.title = cert.find_element_by_class_name('item-title').\
          find_element_by_tag_name('a').text
      except NoSuchElementException:
        certification.title = cert.find_element_by_class_name('item-title').text

      try:
        certification.course_url = cert.find_element_by_class_name('item-title').\
          find_element_by_tag_name('a').get_attribute('href')
      except NoSuchElementException:
        certification.course_url = None

      try:
        certification.course_image = cert.find_element_by_tag_name('img').get_attribute('src')
      except NoSuchElementException:
        certification.course_image = None

      try:
        certification.institution = cert.find_element_by_class_name('item-subtitle').\
          find_element_by_tag_name('a').text
      except NoSuchElementException:
        institution = cert.find_element_by_class_name('item-subtitle').text
        if ', License ' in institution:
          certification.institution = institution.split(', License ')[0]
          certification.institution_license = institution.split(', License ')[1]
      else:
        certification.institution_license = None

      try:
        certification.date_range = cert.find_element_by_class_name('meta').\
          find_element_by_class_name('date-range').text
      except NoSuchElementException:
        certification.date_range = None
        certification.from_date = None
        certification.to_date = None
      else:
        from_to_times = cert.find_element_by_class_name('meta').find_element_by_class_name('date-range').find_elements_by_tag_name('time')
        certification.from_date = from_to_times[0].text
        certification.to_date = None
        if len(from_to_times) > 1:  # may way to remove
          certification.to_date = from_to_times[1].text

      self.certifications.append(certification)

    # get skills
    skills = profile.find_elements_by_class_name('skill')
    self.skills = []
    for current_skill in skills:
      classes = current_skill.get_attribute('class')
      if 'see-more' in classes or 'see-less' in classes:
        continue
      skill = Skill()

      a_tag = current_skill.find_element_by_tag_name('a')
      skill.name = a_tag.find_element_by_tag_name('span').text
      skill.url = a_tag.get_attribute('href')

      self.skills.append(skill)

    # get education
    schools = profile.find_elements_by_class_name('school')
    self.schools = []
    for institution in schools:
      logo = institution.find_element_by_class_name('logo')
      school = School()

      try:
        school.url = logo.find_element_by_tag_name('a').get_attribute('href')
        school.image = logo.find_element_by_tag_name('a').find_element_by_tag_name('img').\
          get_attribute('src')
      except NoSuchElementException:
        school.url = None
        school.image = None

      title = institution.find_element_by_class_name('item-title')
      school.name = title.find_element_by_tag_name('a').text
      if not school.url:
        school.url = title.find_element_by_tag_name('a').get_attribute('href')

      school.degree = institution.find_element_by_class_name('item-subtitle').text
      date_range = institution.find_element_by_class_name('meta').find_elements_by_tag_name('time')
      if date_range:
        school.from_date = date_range[0]
        school.to_date = None
        if len(date_range) > 1:
          school.to_date = date_range[1]

      self.schools.append(school)



    # get volunteering

    # get languages

    # get groups

class SummaryInfo:
  def __init__(self, current, previous, education):
    self.current_position = current
    self.previous_position = previous
    self.education = education


class Experience:
    pass


class Certification:
  pass

class Skill:
  pass

class School:
  pass


from datetime import datetime
datetime.now()
from selenium import webdriver
driver = webdriver.Firefox()
driver.get("http://linkedin.com/in/andreasdivaris")
driver.find_element_by_css_selector('.positions')
positions=_
positions
positions.screenshot()
positions.screenshot('neat.png')
positions.id
positions.location
positions.parent
positions.parent()
positions.rect
positions.screenshot
positions.text
positions.find_elements_by_class_name('position')
elements = _
elements[0].text
get_ipython().magic('save work_with_selenium 0-22')