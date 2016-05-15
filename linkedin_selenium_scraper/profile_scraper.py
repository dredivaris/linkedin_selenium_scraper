import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LinkedinProfile:
  def _login(self, email, password):
    try:
      sign_in = self.profile.find_element_by_class_name('sign-in-link')
    except NoSuchElementException:
      sign_in = self.profile.find_element_by_partial_link_text('Sign In')
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
      go_to_profile = self.profile.find_element_by_partial_link_text('Improve your profile')
      go_to_profile.click()
      preview_button = self.profile.find_element_by_class_name('preview-profile')
      preview_button.click()
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

    # may not be necessary
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
      date_section = position.find_element_by_class_name('experience-date-locale')

      range = date_section.find_elements_by_tag_name('time')
      experience.from_date = range[0].text
      if len(range) == 2:
        experience.to_date = range[1].text
      else:
        experience.to_date = 'present'

      experience.time_at_position = date_section.text.split('(')[1].split(')')[0]
      experience.position_location = date_section.text.split('(')[1].split(')')[1]

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
    # skills = profile.find_elements_by_id('profile-skills').find_elements_by_tag_name('ul')
    skills = [s for s in profile.find_element_by_id('profile-skills').
      find_elements_by_tag_name('ul') if 'skills-section' in s.get_attribute('class')]
    top_skills, other_skills = skills[0], skills[1]

    def get_skills_list(skills_selenium):
      skills_selenium_list = skills_selenium.find_elements_by_class_name('endorse-item')
      parsed_skills = []
      for current in skills_selenium_list:
        skill = Skill()
        try:
          skill.name = current.find_element_by_class_name('endorse-item-name').text
          skill.url = current.find_element_by_class_name('endorse-item-name-text').get_attribute('href')
        except NoSuchElementException:
          continue
        parsed_skills.append(skill)
      return parsed_skills

    self.top_skills = get_skills_list(top_skills)
    self.other_skills = get_skills_list(other_skills)

    # get education
    schools = profile.find_elements_by_class_name('education')
    self.schools = []
    for institution in schools:
      logo = institution.find_element_by_class_name('education-logo')
      school = School()

      try:
        school.url = institution.find_element_by_tag_name('a').get_attribute('href')
        school.image = logo.find_element_by_tag_name('img').get_attribute('src')
      except NoSuchElementException:
        school.url = None
        school.image = None

      title_and_degree = institution.find_element_by_tag_name('header')
      title = title_and_degree.find_element_by_tag_name('a')
      school.name = title.text
      if not school.url:
        school.url = title.find_element_by_tag_name('a').get_attribute('href')

      school.degree = '{} {}'.format(title_and_degree.find_element_by_class_name('degree').text,
                                     title_and_degree.find_element_by_class_name('major').text)
      date_range = institution.find_element_by_class_name('education-date').find_elements_by_tag_name('time')
      if date_range:
        school.from_date = date_range[0].text
        school.to_date = None
        if len(date_range) > 1:
          school.to_date = date_range[1].text.replace('- ', '')

      self.schools.append(school)

    # get volunteer opportunities, causes, and organizations
    opportunities = profile.find_element_by_class_name('opportunities').find_elements_by_tag_name('li')
    causes = profile.find_element_by_id('volunteering-causes-view').find_element_by_class_name('volunteering-listing').find_elements_by_tag_name('li')
    organizations = profile.find_element_by_id('volunteering-organizations-view').find_elements_by_tag_name('li')

    self.opportunities = [i.text for i in opportunities]
    self.causes = [i.text for i in causes]
    self.organizations = [i.text for i in organizations]

    # get languages
    languages = profile.find_element_by_id('languages-view').find_elements_by_tag_name('li')
    self.languages = []
    for language in languages:
      lang = Language()
      lang.name = language.find_element_by_tag_name('h4').text
      lang.proficiency_level = language.find_element_by_class_name('languages-proficiency').text
      self.languages.append(lang)

    profile.close()


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

class Group:
  pass