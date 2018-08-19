import requests
import lxml.html
import re
from dateutil.parser import parse as parse_date
from datetime import datetime
from bs4 import BeautifulSoup #parsing html


class Poem:
    """ Container for a poem with associated metadata from allpoetry.com """

    def __init__(self, title=None, body=None, meta=None, url=None, date=None,
                 count_likes=None, count_views=None):
        """
        initialize a poem object
        :param title: the title of the poem
        :type title: str
        :param body: the poem's lines
        :type body: list
        :param meta: the copyright information and extra author's comments
        :type meta: str
        :param url: the url of the poem
        :type url: str
        :param date: the date the poem was written
        :type date: datetime.datetime
        :param count_likes: how many people liked the poem
        :type count_likes: int
        :param count_views: how many people viewed the poem
        :type count_views: int
        """
        self.title = title
        self.body = body
        self.meta = meta
        self.url = url
        self.count_like = count_likes
        self.count_view = count_views
        self.copyright = copyright
        self.date = date

    def _texed(self):
        """
        creates a tex version of the poem
        :return: the poem formatted in LaTeX
        :rtype: str
        """
        tex = "\poemtitle{" + self.title + "}"

        tex += "\\begin{verse}"
        stanzas = self.body.split("\n\n")
        for stanza in stanzas:
            for line in stanza.split("\n"):
                if len(line) > 0:
                    tex += line + " \\\\ "
            tex += " \\vspace{0.4cm} "
        tex += "\end{verse} "
        tex += "\attrib{" + str(self.date) + "} "
        tex += " \\newpage"

        # the quotation marks are wonky... find them and fix them
        p = re.compile('"([\w\s.!?\\-,]+)"')
        for quote in p.findall(tex):
            new = "\enquote{" + quote + "}"
            tex = tex.replace('"' + quote + '"', new)
        return tex


class AllPoetry:
    LOGIN_URL = "https://allpoetry.com/login"

    def __init__(self, login_username=None, login_password=None):
        """
        setup an allpoetry api request
        must login if wanting more than the 15th page of poems
        :param login_username: credentials to login
        :type login_username: str
        :param login_password: credentials to login
        :type login_password: str
        """
        self.session = requests.session()  # a continuous session is used for security authentication
        if login_username and login_password:
            self._login(login_username, login_password)

    @staticmethod
    def _nth_page_url(username, n):
        """
        url for the n-th poetry page of a user, not an actual poem but just the index
        :param username: user to fetch  n-th page for
        :type username: str
        :param n: which page number to fetch
        :type n: int
        :return: the url of the nth page
        :rtype: str
        """
        return "https://allpoetryapi.com/poems/read_by/{}?page={}".format(username, n)

    def get_poem_by_url(self, poem_url):
        """
        given an allpoetry.com url retrieve the poem and parse metadata
        :param poem_url: string for location of poem
        :rtype poem_url: str
        :return: a poem object with all metadata
        :rtype: Poem
        """

        # get page contents
        poem_html = self.session.get(poem_url)
        poem_soup = BeautifulSoup(poem_html.text, 'html.parser')

        # store the details of the poem in contents, this will be passed to a poem object
        contents = dict()
        contents['url'] = poem_url
        contents['title']= poem_soup.select(".title")[0].text  # title of poem
        contents['meta'] = poem_soup.find_all("div", {"class": "copyright"})[0].text  # extra information at end of poem
        contents['body'] = poem_soup.select(".poem_body")[0].text.split(contents['meta'])[0].split("\n")  # poem text

        view_string = poem_soup.find("span", {"id": "views"}).text.split("views")[0].strip()
        contents['count_views']= self._parse_view_string(view_string)

        try:
            date = parse_date(poem_soup.select(".author_copyright")[0].select(".timeago")[0].get("title"))
        except IndexError:
            date = None
        finally:
            contents['date'] = date

        try:
            categories = [a.text.strip() for a in poem_soup.select(".cats_dot")[0].select("a")]
        except IndexError:
            categories = None
        finally:
            contents['categories'] = categories

        try:
            count_likes = int(poem_soup.select(".cmt_wrap")[0].select('.num')[0].text)
        except IndexError:
            count_likes = None
        finally:
            contents['count_likes'] = count_likes

        return Poem(**contents)

    def _login(self, username, password):
        """
        login to allpoetry.com so that poems beyond page 15 can be fetched
        :param username: the username associated with allpoetry.com
        :type username: str
        :param password: the password associated with allpoetry.com
        :type password: str
        :return: None
        :rtype: NoneType
        """
        login_page = self.session.get(self.LOGIN_URL)
        login_html = lxml.html.fromstring(login_page.text)
        hidden_inputs = login_html.xpath(
            r'//form//input[@type="hidden"]')  # find authentication token and other form data
        indices = [0, 1]  # these are the two attributes we need: authenticity token and utf8
        form = {hidden_inputs[i].attrib['name']: hidden_inputs[i].attrib['value'] for i in indices}
        form['user[name]'] = username
        form['user[password]'] = password
        form['referer'] = self.LOGIN_URL
        response = self.session.post(self.LOGIN_URL, data=form)
        errors = BeautifulSoup(response.text, 'html.parser').select('.error')
        if errors:
            raise RuntimeError("Error logging in: {}".format("&&".join([e.text for e in errors])))

    @staticmethod
    def _parse_view_string(view_string):
        """
        given a string indicating number of views for a poem, e.g. "321 views " or "541.7k views "
        parse and return an integer type
        :param view_string: string indicating number of views, output of span with id=views
        :type view_string: str
        :return: integer representation of views
        :rtype: int
        """
        try:
            count = int(view_string)
        except ValueError:
            if "k" in view_string:
                try:
                    count = int(float(view_string.replace("k", "")) * 1000)
                except ValueError:
                    count = None
        return count
