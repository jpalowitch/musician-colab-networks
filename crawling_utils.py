import pandas as pd
import numpy as np
import urllib2
from bs4 import BeautifulSoup
from time import sleep
import re

# Do you want to read from the current position? If so, set restart = False
restart = False
# Do you want to load from last checkpoint?
checkpoint = 0
# Want chatter?
verbose = False
# Set NA values manually
na_values = ['#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN', '-NaN', '-nan', '1.#IND', '1.#QNAN', 'N/A', 'NA', 'NULL', 'NaN', 'n/a', 'nan', 'null']

def get_page_contents (url, verbose=False):
    
    try_again = True
    count = 0
    page_contents = None
    
    while try_again:
        
        try_again = False

        try:
            page_contents = urllib2.urlopen(url)
        except urllib2.URLError, err:
            if hasattr(err, 'code'):
                if err.code == 404 and verbose:
                    print "URLError, 404: Likely no wiki page"
            else: 
                if verbose:
                    print "unknown URLError: Trying again"
                sleep(1)
                try_again = True
                count = count + 1
        except urllib2.HTTPError:
            if verbose:
                print "HTTPError: likely no wiki page"
            
        if count > 50 and verbose:
            print "Encountered over 50 URLErrors: exiting"
            exit()
    
    return page_contents
    
    
def get_links_text (child):
    links = child.findAll('a')
    nlinks = len(links)

    # Getting text from links
    linksText = [''] * nlinks
    for i in range(0, nlinks):
        link = links[i]
        if 'href' in link.attrs:
            linkText = link['href']
            if '/wiki/' in linkText:
                linkText = linkText.replace('/wiki/', '')
                linksText[i] = linkText

    # Filtering links
    linksText = filter(None, linksText)
    linksText = list(set(linksText))
    
    return linksText
    
    
def is_jazz_musician (name_string, report_string, jms, verbose=False):
    
    if verbose:
        print '--from ' + report_string + \
              ': checking jm status of ' + name_string
        
    if name_string in jms:
        return True
    
    # Getting page content
    wiki_page = "https://en.wikipedia.org/wiki/" + name_string
    wp_html = get_page_contents(wiki_page, verbose)
    if wp_html is None:
        return False
    wp_soup = BeautifulSoup(wp_html, 'html.parser')
    
    # Getting tags
    th_tags = wp_soup.findAll('th', attrs={'scope':'row'})
    
    # Checking for human-ness
    human_texts = ['Occupation', 'Born']
    human_index = -1
    count = 0
    for tag in th_tags:
        if tag.text in human_texts:
            human_index = count
            break
        count = count + 1
    if human_index == -1:
        return False
            
    # Checking for genre
    genre_index = 0
    count = 0
    for tag in th_tags:
        if tag.text == 'Genres':
            genre_index = count
            break
        count = count + 1
    if genre_index == -1:
        return False
    
    # Getting genre content and checking for jazz
    genre_content = th_tags[genre_index].find_next_sibling()
    genre_links = genre_content.findAll('a')
    is_jazz = False
    jazz_genres = ['jazz', 'Jazz', 'bop']
    for link in genre_links:
        if any(x in link.text for x in jazz_genres):
            is_jazz = True
            break
    
    return is_jazz
   

def mine_double_caps (child, report_string, jms, ignore_italics=False, verbose=False):
    jazz_peeps = []
    if ignore_italics:
        child_print = re.sub('<i.*?/i>', '', str(child), flags=re.DOTALL)
    else:
        child_print = str(child)
    child_words = re.sub("[^\w]", " ", child_print).split()
    count = 1
    while count < len(child_words):
        wordi = child_words[count - 1]
        wordj = child_words[count]
        add_str = ''
        is_potential = wordi[0].isupper() and wordj[0].isupper()
        if is_potential and len(wordj) == 1 and count < len(child_words) - 1:
            additional_word = child_words[count]
            add_str = "_" + additional_word
        if is_potential:
            potential_name = wordi + "_" + wordj + add_str
            if verbose:
                print '--potential_name is ' + potential_name
            if is_jazz_musician(potential_name, report_string, jms, verbose):
                jazz_peeps.append(potential_name)
                if len(add_str) == 0:
                    count = count + 2
                else:
                    count = count + 3
            else:
                count = count + 1
        else:
            count = count + 1
    return jazz_peeps
    
    
def get_personnel_if_jazz (name_string, report_string, jms, verbose=False):

    if verbose:
        print '--from ' + report_string + \
              ': checking album status of ' + name_string    
    # Getting page content
    wiki_page = "https://en.wikipedia.org/wiki/" + name_string
    wp_html = get_page_contents(wiki_page, verbose)
    if wp_html is None:
        return [False, None, jms]
    wp_soup = BeautifulSoup(wp_html, 'html.parser')
    
    # Getting first description tag checking for "Album" link
    th_tags = wp_soup.find('th', attrs={'class':'description'})
    if th_tags is None:
        return [False, None, jms]
    if th_tags.findChildren('a', attrs={'title':'Album'}) is None:
        return [False, None, jms]
        
    # Checking genre [genre -> parent -> sibling -> genre text]
    genre_tag = wp_soup.find('a', attrs={'title':'Music genre'})
    if genre_tag is None:
        return [False, None, jms]
    genre_text = genre_tag.parent.find_next_sibling().text
    jazz_genres = ['jazz', 'Jazz', 'bop']
    if all(x not in genre_text for x in jazz_genres):
        return [False, None, jms]
        
    # Find personnel header
    if wp_soup.findAll('h2') is None:
        return [False, None, jms]
    personnel_tag = None
    for tag in wp_soup.findAll('h2'):
        if tag.find('span', attrs={'id':'Personnel'}):
            personnel_tag = tag
    if personnel_tag is None:
        return [False, None, jms]
            
    # Mining double caps and links from personnel list
    person_list = []
    next_sibling = personnel_tag
    move_on = True
    while move_on:
        next_sibling = next_sibling.find_next_sibling()
        if next_sibling is None or next_sibling.name in ['h2']:
            break
        else:
            # Mining double caps
            jazz_peeps = mine_double_caps(next_sibling, report_string, jms, verbose)
            jazz_peeps = list(set(jazz_peeps))
            person_list = person_list + jazz_peeps
            jms.update(jazz_peeps)

            # Mining links
            linksText = get_links_text(next_sibling)
            for link in linksText:
                if is_jazz_musician(link, name_string, jms, verbose):
                    jms.add(link)
                    person_list = person_list + [link]
    person_list = list(set(person_list))
                
    # Getting album release text
    released_text = ''
    th_rows = wp_soup.findAll('th', attrs={'scope':'row'})
    if (len(th_rows) > 0):
        #if len(th_rows) == 1:
        #    th_rows = [th_rows]
        # *** If you feel the need to put these in, try mining Habana_(album) ***
        for tag in th_rows:
            if tag.text == "Recorded" or tag.text== "Released":
                released_tag = tag
                released_text = tag.find_next_sibling().text
                released_text = released_text.replace(u'\xa0', u' ')
                released_text = re.sub('\[.*?\]', '', released_text, flags=re.DOTALL)
    
    # Getting data frame to return
    dfData = {'Musician2': person_list,
              'Album': [name_string] * len(person_list),
              'Released': [released_text] * len(person_list)}
    returnDf = pd.DataFrame(data=dfData)
    
    return [True, returnDf, jms]
    
    
def get_jazz_musicians_table (table, report_string, jms, jas, verbose=False):
    
    # Get all row tags
    trows = table.find_all('tr')

    # Names that signify the album name column
    album_col_names = ['Album', 'Album Title', 'Title', 'Album title']

    # Initializing edge list
    dfcols = ['Musician2', 'Album', 'Released']
    album_jazz_musicians = pd.DataFrame(columns=dfcols)

    # Parse rows
    for i in range(0, len(trows)):

        # Find row tags
        row_i = trows[i]
        row_i_tags = row_i.find_all()

        # Populate the cells of the row
        row_cells = [row_i_tags[0]]
        while not row_cells[-1].find_next_sibling() is None:
            row_cells.append(row_cells[-1].find_next_sibling())
        ncol = len(row_cells)

        if i == 0:
            # Finding album column
            album_col = None
            table_ncol = ncol
            for j in range(0, table_ncol):
                if any(x == row_cells[j].text for x in album_col_names):
                    album_col = j
            if album_col is None:
                return [album_jazz_musicians, jms, jas]
        else:
            if ncol < table_ncol:
                continue
            jm_add = pd.DataFrame(columns=dfcols)
            # Check out album title with album col
            mine_other_cells = False
            album_name_children = row_cells[album_col].findChildren()
            link_tag = None
            for child in album_name_children:
                if child.has_attr('href'):
                    if 'wiki' in child['href']:
                        link_tag = child
            if link_tag is None:
                try:
                    album_name = str(row_cells[album_col].text)
                except UnicodeEncodeError:
                    continue
                album_name = re.sub('\[.*?\]', '', album_name, flags=re.DOTALL)
                mine_other_cells = True
            else:
                href = link_tag['href']
                album_name = str(href.encode('ascii', 'replace'))
                album_name = re.sub('/wiki/', '', album_name)
                if album_name not in jas:
                    album_res = get_personnel_if_jazz(album_name, report_string, jms, verbose)
                    if album_res[0]:
                        jm_add = album_res[1]
                        jas.add(album_name)
                        jms = album_res[2]
                    else:
                        mine_other_cells = True
                else: 
                    mine_other_cells = False
            # Check out other cells if album name was not a link
            if mine_other_cells and len(row_cells) > 1:
                jm_add = pd.DataFrame(columns=dfcols)
                check_cols = range(0, ncol)
                check_cols.remove(album_col)
                for j in check_cols:
                    jazz_peeps = mine_double_caps(row_cells[j], report_string, jms, verbose)
                    jms.update(jazz_peeps)
                    njps = len(jazz_peeps)
                    if njps > 0:
                        addDf = pd.DataFrame({'Musician2':jazz_peeps,
                                              'Album':[album_name] * njps,
                                              'Released':['0000'] * njps})
                        jm_add = jm_add.append(addDf)
            album_jazz_musicians = album_jazz_musicians.append(jm_add)
    
    return(album_jazz_musicians, jms, jas)
    
    
def get_jazz_musicians_discography (name_string, report_string, jms, jas, verbose=False):

    if verbose:
        print '--from ' + report_string + \
              ': scraping separate discography page wiki/' + name_string
        
    # Initializing edge list
    dfcols = ['Musician2', 'Album', 'Released']
    album_jazz_musicians = pd.DataFrame(columns=dfcols)

    # Getting page content
    wiki_page = "https://en.wikipedia.org/wiki/" + name_string
    wp_html = get_page_contents(wiki_page, verbose)
    wp_soup = BeautifulSoup(wp_html, 'html.parser')


    # Finding the first legitimate h2 that could have real content
    current_tag = None
    h2s = wp_soup.findAll('h2')
    for tag in h2s:
        all_children = tag.findAll()
        if len(all_children) > 0:
            first_child = all_children[0]
            if first_child.has_attr('class'):
                if str(first_child['class'][0]) == 'mw-headline':
                    current_tag = tag
                    break
    if current_tag is None:
        return(album_jazz_musicians, jms, jas, None)
        
    # Cycling through h2 siblings
    comp_names = ["Compilation", "compilation", "Box", "box"]
    do_next_section = True
    already_logged_albums = set()
    while not 'References' in current_tag.find_next_sibling().text:
        current_tag = current_tag.find_next_sibling()
        if do_next_section:
            if current_tag.name == 'table':
                ajm_res, jms, jas = get_jazz_musicians_table(current_tag, report_string, jms, jas, verbose)
                album_jazz_musicians = album_jazz_musicians.append(ajm_res)
            elif current_tag.name == 'ul':
                link_tags = current_tag.findAll('a')
                for link_tag in link_tags:
                    href = link_tag['href']
                    album_name = str(href.encode('ascii', 'replace'))
                    album_name = re.sub('/wiki/', '', album_name)
                    if album_name not in jas:
                        album_res = get_personnel_if_jazz(album_name, report_string, jms, verbose)
                        if album_res[0]:
                            album_jazz_musicians = album_jazz_musicians.append(album_res[1])
                            jas.add(album_name)
                            jms = album_res[2]
                    else:
                        already_logged_albums.add(album_name)
            else:
                if any(x in current_tag.text for x in comp_names):
                    do_next_table = False
        else:
            do_next_section = True
        if current_tag.find_next_sibling() is None:
            break

    return(album_jazz_musicians, jms, jas, already_logged_albums)
    
    
def get_jazz_musicians (name_string, jms, jas, verbose=False):
    
    if verbose:
        print 'getting jazz musicians from ' + name_string
        
    # Initializing data frame
    dfcols = ['Musician2', 'Album', 'Released']
    album_jazz_musicians = pd.DataFrame(columns=dfcols)

    # Getting page content
    wiki_page = "https://en.wikipedia.org/wiki/" + name_string
    wp_html = get_page_contents(wiki_page, verbose)
    try:
        wp_soup = BeautifulSoup(wp_html, 'html.parser')
    except TypeError:
        print "encountered TypeError at BeautifulSoup; likely no wiki page"
        return(album_jazz_musicians, jms, jas, None)
    
    # Getting links
    links = wp_soup.findAll('a')
    nlinks = len(links)
    
    # Getting text from links
    linksText = [''] * nlinks
    for i in range(0, nlinks):
        link = links[i]
        if 'href' in link.attrs:
            linkText = link['href']
            if '/wiki/' in linkText:
                linkText = linkText.replace('/wiki/', '')
                linksText[i] = linkText
                
    # Filtering text from links
    linksText = filter(None, linksText)
    linksText = list(set(linksText))
    bad_strings = ['/', ':', '!', 'album', 'film', 'at', 'the', 'and']
    for z in bad_strings:
        linksText = [x for x in linksText if z not in x]
        
    # Finding jazz musicians
    mentioned_jazz_musicians = []
    for link in linksText:
        if is_jazz_musician(link, name_string, jms, verbose):
            mentioned_jazz_musicians.append(link)
            jms.add(link)
        else:
            ar_report_string = name_string + '/' + link
            if link not in jas:
                album_res = get_personnel_if_jazz(link, ar_report_string, jms)                
                if album_res[0]:
                    album_jazz_musicians = album_jazz_musicians.append(album_res[1])
                    jas.add(link)
                    jms = album_res[2]
                
    # Find discography/recordings header
    if wp_soup.findAll('h2') is None:
        print "--no h2 tags, returning"
        album_jazz_musicians['Musician1'] = pd.Series([name_string] * album_jazz_musicians.shape[0])
        return(album_jazz_musicians, jms, jas, None)
    discography_tag = None
    for tag in wp_soup.findAll('h2'):
        span_tags = tag.findAll('span')
        for span in span_tags:
            if ('discography' in span.text) or ('Discography' in span.text) or ('Recordings' in span.text):
                discography_tag = tag
    if discography_tag is None:
        print "--discography_tag is None, returning"
        album_jazz_musicians['Musician1'] = pd.Series([name_string] * album_jazz_musicians.shape[0])
        return(album_jazz_musicians, jms, jas, None)

    # Finding if there is a separate discography page
    disc_link = None
    current_tag = discography_tag
    while current_tag.find_next_sibling() is not None and not current_tag.find_next_sibling().name == 'h2':
        current_tag = current_tag.find_next_sibling()
        # Mine the links
        tag_links = current_tag.findAll('a')
        for link in tag_links:
            if link.has_attr('href'):
                href = link['href']
            else:
                continue
            link_href = str(href.encode('ascii', 'replace'))
            if ('discography' in link_href or 'Discography' in link_href or 'Works' in link_href) and \
                ('wiki' in link_href) and \
                (name_string in link_href):
                disc_link = link_href
    
    if disc_link is None:    
        # Finding all unlinked jazz musicians in discography
        #disc_mentions = []
        #for child in discography_sib.findChildren():
        #    jazz_peeps = mine_double_caps(child, name_string, jms, ignore_italics=True)
        #    jms.update(jazz_peeps)
        #    njps = len(jazz_peeps)
        #    if njps > 0:
        #        add_data = {'Musician2': jazz_peeps, 
        #                    'Album': ['Disc_mention'] * njps,
        #                    'Released': ['0000'] * njps}
        #        album_jazz_musicians.append(pd.DataFrame(add_data))
        # Cycling through h2 siblings
        current_tag = discography_tag
        already_logged_albums = set()
        while current_tag.find_next_sibling() is not None and not current_tag.find_next_sibling().name == 'h2':
            current_tag = current_tag.find_next_sibling()
            # Mine the links
            tag_links = current_tag.findAll('a')
            for link in tag_links:
                if 'href' in link.attrs:
                    href = link['href']
                    album_name = str(href.encode('ascii', 'replace'))
                    album_name = re.sub('/wiki/', '', album_name)
                    if album_name not in jas:
                        album_res = get_personnel_if_jazz(album_name, name_string, jms, verbose)
                        if album_res[0]:
                            album_jazz_musicians = album_jazz_musicians.append(album_res[1])
                            jas.add(album_name)
                            jms = album_res[2]
                    else:
                        already_logged_albums.add(album_name)
    else:
        disc_link = re.sub('/wiki/', '', disc_link)
        disc_jazz_musicians = get_jazz_musicians_discography(disc_link, name_string, jms, jas, verbose)
        ajm_res, jms, jas, already_logged_albums = disc_jazz_musicians
        album_jazz_musicians = album_jazz_musicians.append(ajm_res)
        
    # Formatting album_jazz_musicians
    print "--formatting album_jazz_musicians"
    not_artist = album_jazz_musicians['Musician2'] != name_string
    album_jazz_musicians = album_jazz_musicians[not_artist]
    dup_erase = ~album_jazz_musicians.duplicated(subset=['Album', 'Musician2'], keep='first')
    album_jazz_musicians = album_jazz_musicians[dup_erase]
    album_jazz_musicians = album_jazz_musicians.reset_index().drop('index', 1)
    album_jazz_musicians['Musician1'] = pd.Series([name_string] * album_jazz_musicians.shape[0], 
                                                  index=album_jazz_musicians.index)
    album_jazz_musicians = album_jazz_musicians[['Musician1', 'Musician2', 'Album', 'Released']]
            
    return(album_jazz_musicians, jms, jas, already_logged_albums)
    
    

