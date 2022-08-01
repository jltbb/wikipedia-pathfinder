import requests
import re
import time
s = requests.Session()

# Put your starting and ending Wikipedia URL's here
# eg. start_term = 'https://en.wikipedia.org/wiki/Dovrefjell–Sunndalsfjella_National_Park'.split("/")[-1]
start_term = ''.split("/")[-1]
end_term = ''.split("/")[-1]

counter = 0

prelook_visited = []
all_visited = []
all_visited_clean = []
close_terms = []
links_back_end = []

def parse(article):
    response = s.get(f'https://en.wikipedia.org/w/api.php?action=parse&page={article}&prop=text&format=json').json()

    text = str(response['parse']['text'])

    # We don't want to use the references section
    text = text.split('<span class=\"mw-headline\" id=\"References\">References</span>')[0]

    #Prevent all countries from having "Geographic Coordinate System" come up
    text = text.split('title="Geographic coordinate system">Coordinates</a>')[-1]
    reg = re.findall('a href="\/wiki\/(.+?(?="))', text)
    return reg, response

def light_search(search):
    possible_links = []

    reg, response = parse(search)

    for x in reg:
        if ':' not in x:
            if '#' in x:
                x = x.split('#')[0]
            possible_links.append(x)

    for x in possible_links[:min(len(possible_links), 3)]:
        close_terms.append(x)

def search(start, end, end_thread=False):
    global close_terms
    global counter
    counter += 1

    reg, response = parse(start)
    article_title = response['parse']['title']
    print("Checking", article_title)

    possible_links = []

    for x in reg:
        if ':' not in x:
            if '#' in x:
                x = x.split('#')[0]
            possible_links.append(x)

    # Remove duplicates
    orig_links = possible_links
    possible_links = [link for link in list(set(possible_links)) if link not in all_visited]

    if end_thread:
        prelook_visited.append(start)
        possible_links = [link for link in list(set(possible_links)) if link not in prelook_visited]

        for x in possible_links:
            for y in end.split('_'):
                if y in x and len(y) > 4:
                    close_terms.append(x)

        if counter == 1:
            for x in range(min(len(orig_links), 10)):
                close_terms.append(orig_links[x])
                light_search(orig_links[x])
        else:
            for x in range(min(len(orig_links), 5)):
                close_terms.append(orig_links[x])

    # Kill the keyword searching end-thread after 3 rounds
    if end_thread and counter == 3:
        counter -= 3
        return

    # Does one of our keyword searches link back to the end?
    for link in possible_links:
        if start_term == link and end_thread:
            links_back_end.append(start)

    # Let's decide what to check next
    check_next = []
    if not end_thread:
        # Add this site as a visited site
        all_visited.append(start)
        all_visited_clean.append(article_title)

        for item in possible_links:
            if item in close_terms:
                check_next.append(item)
            for item_link in links_back_end:
                if item_link == item:
                    check_next.append(item)

        check_next = list(set(check_next))

        # Don't loop to self
        if start in possible_links:
            possible_links.remove(start)

        if end in possible_links:
            end_clean = s.get(f'https://en.wikipedia.org/w/api.php?action=parse&page={end}&prop=text&format=json').json()['parse']['title']
            all_visited_clean.append(end_clean)
            print('-----------------------')
            print(all_visited_clean[0], '->', all_visited_clean[-1])
            print("It took", str(counter), "links but..")
            print("WE FOUND THE END")
            print(all_visited_clean)
            exit()

    time.sleep(0.1)

    if len(check_next) == 0 or end_thread:
        if len(possible_links) == 0:
            # No more links avaliable, go back a step
            search(all_visited[-2], end, end_thread)
        else:
            search(possible_links[0], end, end_thread)
    else:
        for item in check_next:
            if item not in all_visited:
                print("close term being checked:", item)
                search(item, end)
        search(possible_links[0], end, end_thread)

search(end_term, start_term, True)
search(start_term, end_term)
