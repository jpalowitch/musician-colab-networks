from crawling_utils import *


if restart:
    jms = set()
    jas = set()
    dfcols = ['Musician1', 'Musician2', 'Album', 'Released']
    edge_list = pd.DataFrame(columns=dfcols)
    count = 1
    scraped = set()
    to_scrape = set()
    current_jm = "Miles_Davis"
    checkpoint_num = 1000
else:
    if checkpoint > 0:
        edge_list = pd.read_csv('edge_list_' + str(checkpoint) + '.csv', encoding='utf-8', na_values=na_values, keep_default_na=False)
        if edge_list.shape[1] == 5:
            edge_list = edge_list.drop(edge_list.columns[0], axis=1)
        with open('jms_' + str(checkpoint) + '.txt', 'r') as f:
            jms = eval(f.read())
        with open('jas_' + str(checkpoint) + '.txt', 'r') as f:
            jas = eval(f.read())
        with open('to_scrape_' + str(checkpoint) + '.txt', 'r') as f:
            to_scrape = eval(f.read())
        with open('scraped_' + str(checkpoint) + '.txt', 'r') as f:
            scraped = eval(f.read())
        with open('count_' + str(checkpoint) + '.txt', 'r') as f:
            count = int(eval(f.read()))
        with open('checkpoint_num.txt', 'r') as f:
            checkpoint_num = checkpoint + 1000
        with open('current_jm_' + str(checkpoint) + '.txt', 'r') as f:
            current_jm = str(f.read())
    else:
        edge_list = pd.read_csv('edge_list.csv', encoding='utf-8', na_values=na_values, keep_default_na=False)
        if edge_list.shape[1] == 5:
            edge_list = edge_list.drop(edge_list.columns[0], axis=1)
        with open('jms.txt', 'r') as f:
            jms = eval(f.read())
        with open('jas.txt', 'r') as f:
            jas = eval(f.read())
        with open('to_scrape.txt', 'r') as f:
            to_scrape = eval(f.read())
        with open('scraped.txt', 'r') as f:
            scraped = eval(f.read())
        with open('count.txt', 'r') as f:
            count = int(eval(f.read()))
        with open('checkpoint_num.txt', 'r') as f:
            checkpoint_num = int(eval(f.read()))
        with open('current_jm.txt', 'r') as f:
            current_jm = str(f.read())            
            
while True:
    
    null_counts = [edge_list.isnull()['Musician1'].sum(),
                   edge_list.isnull()['Musician2'].sum(),
                   edge_list.isnull()['Album'].sum(),
                   edge_list.isnull()['Released'].sum()]
    print "------Initial null_counts sum check: " + str(sum(null_counts))
    
    
    # Saving values
    print "saving work"
    edge_list.to_csv('edge_list.csv', encoding='utf-8')
    with open('jms.txt', 'w') as f:
        f.write(str(jms))
    with open('jas.txt', 'w') as f:
        f.write(str(jas))
    with open('scraped.txt', 'w') as f:
        f.write(str(scraped))
    with open('count.txt', 'w') as f:
        f.write(str(count))
    with open('checkpoint_num.txt', 'w') as f:
        f.write(str(checkpoint_num))   
    with open('current_jm.txt', 'w') as f:
        f.write(str(current_jm.encode('ascii', 'replace')))           
    with open('to_scrape.txt', 'w') as f:
        f.write(str(to_scrape))
        
    
    # Saving checkpoint
    if edge_list.shape[0] > checkpoint_num:
        print "--saving checkpoint"
        print "--" + "edge_list.shape[1] is " + str(edge_list.shape[1])
        edge_list.to_csv('edge_list_' + str(checkpoint_num) + '.csv', encoding='utf-8')
        with open('jms_' + str(checkpoint_num) + '.txt', 'w') as f:
            f.write(str(jms))
        with open('jas_' + str(checkpoint_num) + '.txt', 'w') as f:
            f.write(str(jas))
        with open('to_scrape_' + str(checkpoint_num) + '.txt', 'w') as f:
            f.write(str(to_scrape))
        with open('scraped_' + str(checkpoint_num) + '.txt', 'w') as f:
            f.write(str(scraped))
        with open('current_jm_' + str(checkpoint_num) + '.txt', 'w') as f:
            f.write(str(current_jm.encode('ascii', 'replace')))            
        with open('count_' + str(checkpoint_num) + '.txt', 'w') as f:
            f.write(str(count))
        checkpoint_num = checkpoint_num + 1000
        
    
    # Checking saved edgelist
    edge_list_saved = pd.read_csv('edge_list.csv', encoding='utf-8', na_values=na_values, keep_default_na=False)
    null_counts_saved = [edge_list_saved.isnull()['Musician1'].sum(),
                         edge_list_saved.isnull()['Musician2'].sum(),
                         edge_list_saved.isnull()['Album'].sum(),
                         edge_list_saved.isnull()['Released'].sum()]
    if sum(null_counts_saved) > 0:
        print("----saved null counts non-zero")
        break
        
    # Reporting
    null_counts = [edge_list.isnull()['Musician1'].sum(),
                   edge_list.isnull()['Musician2'].sum(),
                   edge_list.isnull()['Album'].sum(),
                   edge_list.isnull()['Released'].sum()]
    print "Loop " + str(count) + ": doing " + current_jm
    print "--" + str(len(jms)) + " jazz musicians"
    print "--" + str(len(jas)) + " jazz albums"
    print "--" + str(edge_list.shape[0]) + " current edges"
    print "--" + "edge_list.shape[1] is " + str(edge_list.shape[1])
    print "--Sum of null_counts is " + str(sum(null_counts))
    print "--Does edge_list have any nulls? " + str(edge_list.isnull().values.any())

    # Scraping
    person_res, jms_res, jas_res, already_logged_albums = get_jazz_musicians(current_jm, jms, jas, verbose)
    
    # Doing trial save
    edge_list_test_in = edge_list.append(person_res)
    edge_list_test_in.to_csv('edge_list_test.csv', encoding='utf-8')
    edge_list_test_out = pd.read_csv('edge_list_test.csv', encoding='utf-8', na_values=na_values, keep_default_na=False)
    null_counts_test = [edge_list_test_out.isnull()['Musician1'].sum(),
                        edge_list_test_out.isnull()['Musician2'].sum(),
                        edge_list_test_out.isnull()['Album'].sum(),
                        edge_list_test_out.isnull()['Released'].sum()]
    if sum(null_counts_test) > 0:
        print("----test null counts non-zero")
    
    # Post-scraping updates
    print "--After scraping:"
    print "----Does person_res have any nulls? " + str(person_res.isnull().values.any())
    if person_res.isnull().values.any():
        print "----null_values detected in person_res"
        break
    else:
        print "----no null_values in person_res"
    scraped.add(current_jm)
    edge_list = edge_list.append(person_res)
    if sum(null_counts) > 0:
        print "----null values in edge_list detected"
        break
    jms = jms_res
    jas = jas_res
    
    # Restarting loop for next run
    to_scrape = jms.difference(scraped)
    try:
        current_jm = to_scrape.pop()
    except KeyError:
        break
    count = count + 1            
