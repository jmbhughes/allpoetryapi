# AllPoetryAPI

[![CodeFactor](https://www.codefactor.io/repository/github/jmbhughes/allpoetryapi/badge)](https://www.codefactor.io/repository/github/jmbhughes/allpoetryapi)

An API to access poetry from the popular site [allpoetry.com](https://allpoetry.com/poems). 

## Functionality
Because of the policies of [allpoetry.com](https://allpoetry.com/poems), you must have an account to see poems beyond 
the 15th page, roughly more than 45 poems, for any user. You can make an account for free. When using it, you can fetch 
all the poems you desire for a given user or fetch specific poems for which you already know the URL.

## Example usage
You can retrieve all the poems written by a user with:
    
```python
import allpoetryapi
query_username = "whose_poems_you_want_to_fetch"
login_username, login_password = "your_user", "your_password"
api = allpoetryapi.AllPoetry(login_username, login_password)
links = api.get_user_poem_links(query_username)
poems = [api.get_poem_by_url(link) for title,link in links.items()]

# now get the average number of words in them
avg_word_count = sum([len(p) for p in poems]) / len(poems)
```