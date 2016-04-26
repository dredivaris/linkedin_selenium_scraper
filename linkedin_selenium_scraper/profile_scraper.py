import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LinkedinProfile:
  def _login(self, email, password):
    sign_in = self.profile.find_element_by_class_name('sign-in-link')
    sign_in.click()
    self.profile.implicitly_wait(2)

    # get input elements
    email_input = self.profile.find_element_by_id('session_key-login')
    password_input = self.profile.find_element_by_id('session_password-login')
    submit = self.profile.find_element_by_id('btn-primary')

    # enter credentials
    email_input.send_keys(email)
    password_input.send_keys(password)
    submit.click()

    self.profile.implicitly_wait(3)

    # if parsing profile of currently logged in user, we need to enter preview mode
    try:
      preview_button = self.profile.find_element_by_class_name('preview-profile')
    except NoSuchElementException:
      pass
    else:
      preview_button.click()

  def __init__(self, url, email, password):
    # verify proper linkedin profile url:
    is_linkedin_profile_url = re.compile(r'http(s)?://(www\.)?linkedin\.com/in/[a-zA-Z]+')
    matched = is_linkedin_profile_url.match(url)

    # setup selenium & get page
    self.profile = webdriver.Firefox()
    profile = self.profile
    profile.implicitly_wait(2)
    profile.get(url)
    WebDriverWait(profile, 5)

    self._login(email, password)

    profile.implicitly_wait(15)
    profile.execute_script("window.scrollBy(0,1000000)")

    # handle name, headline and summary
    self.name = profile.find_element_by_id('name').text
    self.connections = profile.find_element_by_class_name('member-connections').\
      text.replace('\n', ' ')
    self.headline = profile.find_element_by_class_name('profile-overview-content').\
      find_element_by_id('headline').text
    self.locality = profile.find_element_by_id('location').\
      find_element_by_class_name('locality').text
    self.industry = profile.find_element_by_id('location').\
      find_element_by_class_name('industry').text


    current_position = profile.find_element_by_id('overview-summary-current').\
      find_element_by_tag_name('td').find_element_by_tag_name('a').text

    previous_positions = profile.find_element_by_id('overview-summary-past').\
      find_element_by_tag_name('td').\
      find_elements_by_tag_name('li')
    previous_positions = [p.text for p in previous_positions]

    education = profile.find_element_by_id('overview-summary-education').\
      find_element_by_tag_name('td').\
      find_elements_by_tag_name('li')
    education = ','.join([p.text for p in education])

    try:
      summary_text = profile.find_element_by_class_name('summary').find_element_by_class_name('description').text
    except NoSuchElementException:
      summary_text = None

    self.summary_info = SummaryInfo(current_position, previous_positions, education, summary_text)


    # parse experience
    positions = profile.find_element_by_id('background-experience').find_elements_by_class_name('section-item')
    self.experiences = []
    for position in positions:
      experience = Experience()

      try:
        logo = position.find_element_by_class_name('experience-logo')
      except NoSuchElementException:
        experience.company_url = None
        experience.company_image_url = None
      else:
        experience.company_url = logo.find_element_by_tag_name('a').get_attribute('href')
        experience.company_image_url = logo.find_element_by_tag_name('img').get_attribute('src')

      try:
        position_section = position.find_element_by_tag_name('h4').find_element_by_tag_name('a')
      except NoSuchElementException:
        experience.position_title = None
        experience.position_title_url = None
      else:
        experience.position_title = position_section.text
        experience.position_title_url = position_section.get_attribute('href')

      experience.company_title = position.find_element_by_tag_name('header').find_elements_by_tag_name('h5')[1].\
        find_element_by_tag_name('a').text

      # experience.date_range = position.find_element_by_class_name('meta').\
      #   find_element_by_class_name('date-range').text

      date_section = position.find_element_by_class_name('date-header-field').\
        find_element_by_class_name('experience-date-locale')

      date_section = position.find_element_by_class_name('experience-date-locale')

      range = date_section.find_elements_by_tag_name('time')
      experience.from_date = range[0].text
      if len(range) == 2:
        experience.to_date = range[1].text
      else:
        experience.to_date = 'present'

      experience.time_at_position = date_section.text.split('(')[1].split(')')[0]
      experience.position_location = date_section.text.split('(')[1].split(')')[1]

      # from_to_times = position.find_element_by_class_name('meta').\
      #   find_element_by_class_name('date-range').find_elements_by_tag_name('time')
      # experience.from_date = from_to_times[0].text
      # experience.to_date = None
      # if len(from_to_times) > 1:
      #   experience.to_date = from_to_times[1].text
      # experience.time_at_position = re.search(r"\((.*)\)", experience.date_range).group(1)

      experience.description = position.find_element_by_class_name('description').text
      self.experiences.append(experience)  # TODO: append at start/end to have it be chronological?

    # get certifications
    certifications = [p for p in profile.find_element_by_class_name('background-certifications').\
      find_elements_by_xpath("//*[contains(@id, 'certification-')]") if '-view' in p.get_attribute('id')]

    self.certifications = []
    for cert in certifications:
      certification = Certification()

      try:
        certification.issuer_url_or_certificate_url = cert.find_element_by_tag_name('h4').\
          find_element_by_tag_name('a').get_attribute('href')
      except NoSuchElementException:
        certification.issuer_url_or_certificate_url = None

      try:
        certification.issuer_url = cert.find_element_by_tag_name('a').get_attribute('href')
      except NoSuchElementException:
        certification.issuer_url = None

      try:
        certification.cert_url = cert.find_element_by_class_name('certification-logo').\
          find_element_by_tag_name('a').get_attribute('href')
      except NoSuchElementException:
        certification.cert_url = None

      try:
        certification.issuer_image_url = cert.find_element_by_class_name('certification-logo').\
          find_element_by_tag_name('img').get_attribute('src')
      except NoSuchElementException:
        certification.issuer_image_url = None

      try:
        certification.title = cert.find_element_by_tag_name('h4').\
          find_element_by_tag_name('a').text.replace('(Link)', '')
      except NoSuchElementException:
        certification.title = None

      try:
        inst = cert.find_element_by_tag_name('hgroup').find_elements_by_tag_name('h5')
      except NoSuchElementException:
        certification.institution = None
        certification.license = None
      else:
        inst = inst[0].text if len(inst) == 1 else inst[1].text
        if 'License' in inst:
          inst = inst.split(', License ')
          certification.institution, certification.license = inst
        else:
          certification.institution = inst
          certification.license = None

      try:
        certification.date = cert.find_element_by_class_name('certification-date').\
          find_element_by_tag_name('time').text
      except NoSuchElementException:
        certification.date = None

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

    # get volunteer opportunities, causes, and organizations
    extra_sections = profile.find_element_by_id('volunteering').\
      find_elements_by_class_name('extra-section')

    self.opportunities, self.causes, self.organizations = [], [], []
    for section in extra_sections:
      sect = section.find_element_by_class_name('title')
      for item in section.find_elements_by_tag_name('li'):
        ex = VolunteeringExperiences()
        ex.text = item.text
        if 'Opportunities' in sect.text:
          self.opportunities.append(ex)
        elif 'Causes' in sect.text:
          self.causes.append(ex)
        elif 'Organizations' in sect.text:
          self.organizations.append(ex)

    # get languages
    languages = profile.find_elements_by_class_name('language')
    self.languages = []
    for language in languages:
      lang = Language()
      lang.name = language.find_element_by_class_name('name').text
      lang.proficiency_level = language.find_element_by_class_name('proficiency').text
      self.languages.append(lang)

    # get interests
    interests = profile.find_element_by_id('interests').find_elements_by_class_name('interest')
    self.interests = []
    for interest in interests:
      current_interest = Interest()
      classes = interest.get_attribute('class')
      if 'see-more' in classes or 'see-less' in classes:
        continue
      try:
        interest = interest.find_element_by_tag_name('a')
      except NoSuchElementException:
        interest = interest.find_element_by_tag_name('span')
        current_interest.name = interest.text
        current_interest.url = None
      else:
        current_interest.name = interest.get_attribute('title')
        current_interest.url = interest.get_attribute('href')
      self.interests.append(current_interest)

class SummaryInfo:
  def __init__(self, current, previous, education, summary):
    self.current_position = current
    self.previous_position = previous
    self.education = education
    self.summary = summary


class Experience:
    pass

class Certification:
  pass

class Skill:
  pass

class School:
  pass

class VolunteeringExperiences:
  pass

class Causes:
  pass

class Language:
  pass

class Interest:
  pass