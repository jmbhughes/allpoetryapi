# AllPoetryAPI

[![CodeFactor](https://www.codefactor.io/repository/github/jmbhughes/allpoetryapi/badge)](https://www.codefactor.io/repository/github/jmbhughes/allpoetryapi)

An API to access poetry from the popular site [allpoetry.com](https://allpoetry.com/poems). 

## Example usage
You can retrieve all the poems written by a user with:
```
import allpoetryapi
query_username = "whose_poems_you_want_to_fetch"
login_username, login_passowrd = "your_user", "your_password"
api = allpoetryapi.AllPoetry(login_username, login_password)
links = api.get_user_poem_links(query_username)
poems = [api.get_poem_by_url(link) for title,link in links.items()]

# now get the average number of words in them
avg_word_count = sum([len(p) for p in poems]) / len(poems)
```