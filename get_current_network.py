import argparse
import pickle
import pandas as pd
import louvain as lv
from os import path
from time import localtime, strftime


parser = argparse.ArgumentParser()
parser.add_argument("-datetag", help="Date to tag the run with.", type=str,
                    default=strftime("%Y-%m-%d", localtime()))
parser.add_argument("-loaddir", help="Directory to grab the network from.",
                    type=str, default="run_saves")
parser.add_argument("-savedir", help="Directory to save the results in.",
                    type=str, default="net_saves")
args = parser.parse_args()

# Set NA values manually
na_values = ['#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN', '-NaN', '-nan', '1.#IND', '1.#QNAN', 'N/A', 'NA', 'NULL', 'NaN', 'n/a', 'nan', 'null']

edge_list = pd.read_csv(path.join(args.loaddir, 'edge_list.csv'),
                        encoding='utf-8', 
                        na_values=na_values, 
                        keep_default_na=False,
                        index_col=0)
with open(path.join(args.loaddir, 'jms.txt'), 'r') as f:
    jms = eval(f.read())
with open(path.join(args.loaddir, 'jas.txt'), 'r') as f:
    jas = eval(f.read())
with open(path.join(args.loaddir, 'to_scrape.txt'), 'r') as f:
    to_scrape = eval(f.read())
with open(path.join(args.loaddir, 'scraped.txt'), 'r') as f:
    scraped = eval(f.read())
with open(path.join(args.loaddir, 'count.txt'), 'r') as f:
    count = int(eval(f.read()))
with open(path.join(args.loaddir, 'checkpoint_num.txt'), 'r') as f:
    checkpoint_num = int(eval(f.read()))
with open(path.join(args.loaddir, 'current_jm.txt'), 'r') as f:
    current_jm = str(f.read())

result_dict = {'edge_list': edge_list, 'jms': jms, 'jas': jas}
savefn = path.join(args.savedir, 'results_' + args.datetag + '.pckl')
with open(savefn, "wb") as f:
    pickle.dump(result_dict, f)

#jnet = ig.Graph()
#edges = zip(edge_list['Musician1'].values, edge_list['Musician2'].values)
#node_set = set(edge_list['Musician1'].values)
#node_set.update(edge_list['Musician2'].values)
#node_list = list(node_set)
#jnet.add_vertices(node_list)
#jnet.add_edges(edges)
#part = lv.find_partition(jnet, method="Modularity")

#membership = part.membership
