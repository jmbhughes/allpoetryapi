import requests
import lxml.html
from dateutil.parser import parse as parse_date
from bs4 import BeautifulSoup  # parsing html
from collections import namedtuple
from PIL import Image


class Poem:
    """ Container for a poem with associated metadata from allpoetry.com """

    def __init__(self, title=None, author=None, body=None, meta=None, url=None, date=None,
                 count_likes=None, count_views=None, categories=None, comments=None):
        """
        initialize a poem object
        :param title: the title of the poem
        :type title: str
        :param author: who wrote this poem, their allpoetry.com username
        :type author: str
        :param body: the poem's lines
        :type body: list of str
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
        :param categories: genres assigned to poem
        :type categories: list of str
        """
        self.title = title
        self.author = author
        self.body = body
        self.meta = meta
        self.url = url
        self.count_like = count_likes
        self.count_view = count_views
        self.date = date
        self.categories = categories
        self.comments = comments

    def __len__(self):
        """
        :return: number of words in poem
        :rtype: int
        """
        return len((" ".join(self.body)).split(" "))

    def num_comments(self):
        """
        :return: number of comments on the poem
        :rtype: int
        """
        return sum([comment.num_replies()+1 for comment in self.comments]) if self.comments is not None else 0

    def num_comment_threads(self):
        """
        :return: number of comment threads
        :rtype: int
        """
        return len(self.comments) if self.comments is not None else 0

    def _texed(self):
        """
        creates a tex version of the poem
        :return: the poem formatted in LaTeX
        :rtype: str
        """
        raise NotImplementedError()
        # tex = "\poemtitle{" + self.title + "}"
        #
        # tex += "\\begin{verse}"
        # stanzas = self.body.split("\n\n")
        # for stanza in stanzas:
        #     for line in stanza.split("\n"):
        #         if line:
        #             tex += line + " \\\\ "
        #     tex += " \\vspace{0.4cm} "
        # tex += "\end{verse} "
        # tex += "\attrib{" + str(self.date) + "} "
        # tex += " \\newpage"
        #
        # # the quotation marks are wonky... find them and fix them
        # p = re.compile('"([\w\s.!?\\-,]+)"')
        # for quote in p.findall(tex):
        #     new = "\enquote{" + quote + "}"
        #     tex = tex.replace('"' + quote + '"', new)
        # return tex


# Comment = namedtuple("Comment", ['user', 'date', 'text', 'replies'])


class Comment:
    """ container comments, structured so that a comment includes a link to its replies"""

    def __init__(self, user=None, date=None, text=None, replies=None):
        """
        initialize comment
        :param user: the user making the comment
        :type user: str
        :param date: the time when the comment was made
        :type date: datetime.datetime
        :param text: the text content of the comment
        :type text: str
        :param replies: all comment replies made to this comment
        :type replies: list of Comment
        """
        self.user = user
        self.date = date
        self.text = text
        self.replies = replies

    def num_replies(self):
        """
        :return: the number of replies to a comment
        :rtype: int
        """
        if self.replies: # is not None or empty
            replies = [r for r in self.replies]
            count = len(replies)
            while replies:
                reply = replies.pop()
                count += len(reply.replies)
                replies += reply.replies
            return count
        else:
            return 0


class AllPoetry:
    """ API to access poems on allpoetry.com"""
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

    def get_user_poem_links(self, username, at_least=None):
        """
        retrieve names of all poems written by user
        :param username: name of user (from URL) to search
        :type username: str
        :param at_least: approximate number of most recent poems titles to return, may slightly exceed this number
            if None, will return all poems
        :type at_least: int
        :return: mapping of poem titles to their urls
        :rtype: dict
        """

        def get_nth_links(n):
            """ load the links for the n-th page of the user's poems"""
            links_url = "https://allpoetry.com/{}?links=1&page={}".format(username, n)
            links = self.session.get(links_url)
            links_soup = BeautifulSoup(links.text, 'html.parser')
            links = dict()
            for entry in links_soup.select(".t_links")[0].select(".clearfix")[0].find_all('div', {'class': "itm"}):
                entry = entry.select("a")[0]
                title = entry.text
                url = "https://allpoetry.com" + entry['href']
                links[title] = url
            return links

        links = dict()
        get_more_poems, i = True, 1
        # run until either all poems have been fetched because the page is blank or a desired number have been fetched
        while get_more_poems:
            new_links = get_nth_links(i)
            if new_links:
                for title, url in new_links.items():
                    links[title] = url
            else:
                get_more_poems = False

            if at_least and len(links) >= at_least:
                get_more_poems = False
            i += 1

        return links

    def get_comments_by_url(self, poem_url, page_number):
        """
        get the comments associated with a page
        :param poem_url: the page for the poem
        :type poem_url: str
        :param page_number: which page of comments to fetch
        :type page_number: int
        :return: list of Comments
        :rtype: list of Comment
        """

        poem_html = self.session.get(poem_url + "?page={}".format(page_number))
        poem_soup = BeautifulSoup(poem_html.text, 'html.parser')

        try:
            comment_list = poem_soup.select(".comments")[0].select(".media")
        except IndexError:  # no comments section found,
            comment_list = []

        comments = []
        ref_comment = dict()  # the most recent comment at that depth already

        for comment_raw in comment_list:
            depth = int(comment_raw.get("data-depth"))
            user = comment_raw.select(".u")[0].text
            date = parse_date(comment_raw.select(".timeago ")[0].get("title"))

            # since the text is embedded between tags, it's a bit of a mess to extract so we just delete the portions
            # that we want to ignore
            text = comment_raw.select(".media-body")[0].text
            text = text.replace(user, "")[3:]
            date_str = comment_raw.select(".media-body")[0].select(".timeago")[0].text
            text = text[:text.index(date_str)].strip()

            comment = Comment(user, date, text, [])

            # add the comment in the appropriate depth
            if depth == 0:
                ref_comment = {depth: comment}
                comments.append(comment)
            else:
                ref_comment[depth] = comment
                ref_comment[depth - 1].replies.append(comment)

        if comment_list:
            comments += self.get_comments_by_url(poem_url, page_number=page_number+1)

        return comments

    def get_poem_by_url(self, poem_url, fetch_comments=False):
        """
        given an allpoetry.com url retrieve the poem and parse metadata
        :param poem_url: string for location of poem
        :rtype poem_url: str
        :param fetch_comments: if True will also get comments for poems, ignores otherwise
        :type fetch_comments: bool
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
        contents['author'] = poem_soup.select(".bio")[0].select(".u")[0].get("href")[1:]

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

        if fetch_comments:
            comments = self.get_comments_by_url(poem_url,1)
            contents['comments'] = comments

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

    def get_user_picture(self, username):
        """
        retrieve a user profile picture
        :param username: which  user to fetch
        :rtype username: str
        :return: the user's profile picture
        :rtype: PIL.JpegImagePlugin.JpegImageFile
        """
        url_user = "https://allpoetry.com/{}".format(username)
        soup = BeautifulSoup(self.session.get(url_user).text, 'html.parser')
        url_img =  "https:" + soup.select(".media-figure")[0].get("src")
        return Image.open(Image.io.BytesIO(self.session.get(url_img).content))

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
