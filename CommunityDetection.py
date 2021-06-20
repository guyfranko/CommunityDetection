import community as community_louvain
import networkx as nx
from networkx.algorithms import community
from operator import itemgetter
from networkx.algorithms.community import k_clique_communities
import json
import os
from datetime import datetime
import csv

def community_detector(algorithm_name,network,most_valualble_edge=None):
        dict = {'num_partitions': 0, 'modularity': 0, 'partition': []}
        if algorithm_name == 'girvin_newman':
            return girvin_newman(network,dict,most_valualble_edge)
        elif algorithm_name == 'louvain':
            return louvain(network,dict)
        else:
            return clique_percolation(network,dict)

def girvin_newman(network,dict,most_valuable_edge=None):
    communities = nx.algorithms.community.centrality.girvan_newman(network, most_valuable_edge)
    communities_lst = []
    for i in communities:
        communities_lst.append((nx.algorithms.community.modularity(network, i),i))
    community = (sorted(communities_lst, key=itemgetter(0),reverse=True))[0]
    for k in community[1]:
         lst=[]
         for j in k:
             lst.append(j)
         dict['partition'].append(lst)
    dict['modularity'] = community[0]
    dict['num_partitions'] = len(community[1])
    return dict




def louvain(network,dict):
    partition = community_louvain.best_partition(network)
    dict['num_partitions'] = partition[max(partition, key=partition.get)]+1
    dict['modularity'] = community_louvain.modularity(partition,network)
    lst = []
    for i in range(dict['num_partitions']):
        lst.append([])
    for i in partition.items():
        lst[i[1]].append(i[0])
    dict['partition'] = lst
    return dict


def clique_percolation(network,dict):
    node_list = list(network.nodes)
    communities_lst = []
    for i in range(len(node_list)-3):
        tmp_lst = []
        last = nx.algorithms.community.k_clique_communities(network,i+2)
        communities = [list(x) for x in last]
        for community in communities:
            for nodes in community:
                if nodes not in tmp_lst:
                    tmp_lst.append(nodes)
        for node in node_list:
            if node not in tmp_lst:
                communities.append([node])
        modularities = modularity(network,communities)
        communities_lst.append((modularities,communities))
    community = (sorted(communities_lst, key=itemgetter(0), reverse=True))[0]
    com = []
    for stam in community[1]:
        if len(stam) != 1:
            com.append(stam)
    dict['modularity'] = community[0]
    dict['num_partitions'] = len(com)
    dict['partition'] = com
    return dict

def modularity(G, communities, weight="weight"):
    directed = G.is_directed()
    if directed:
        out_degree = dict(G.out_degree(weight=weight))
        in_degree = dict(G.in_degree(weight=weight))
        m = sum(out_degree.values())
        norm = 1 / m ** 2
    else:
        out_degree = in_degree = dict(G.degree(weight=weight))
        deg_sum = sum(out_degree.values())
        m = deg_sum / 2
        norm = 1 / deg_sum ** 2
    def community_contribution(community):
        comm = set(community)
        L_c = sum(wt for u, v, wt in G.edges(comm, data=weight, default=1) if v in comm)

        out_degree_sum = sum(out_degree[u] for u in comm)
        in_degree_sum = sum(in_degree[u] for u in comm) if directed else out_degree_sum

        return L_c / m - out_degree_sum * in_degree_sum * norm

    return sum(map(community_contribution, communities))


def edge_selector_optimizer(network):
    betweenness = nx.edge_betweenness_centrality(network,weight='weight')
    return max(betweenness, key=betweenness.get)




def construct_heb_edges(files_path,start_date='2019-03-15',end_date='2019-04-15',non_parliamentarians_nodes=0):
    edges_dict = {}
    names_lst = []
    lst_tweetes = os.listdir(files_path)
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    parliamentarians_id = []
    with open(files_path+'\\'+'central_political_players.csv', newline='') as f:
        reader = csv.reader(f)
        data = list(reader)
    data = data[1:]
    for tuple in data:
        parliamentarians_id.append(tuple[0])
    for tweets in lst_tweetes:
        try:
            now_date = datetime.strptime(tweets[19:29], '%Y-%m-%d')
        except:
            continue;
        if now_date>=start_date and now_date<=end_date:
            file_path = files_path + "\\" + tweets
            with open(file_path, "r") as tweet:
                for dict in tweet:
                    json_data = json.loads(dict)
                    U = json_data["user"]["id"]
                    names_lst.append((json_data["user"]["id"],json_data["user"]["screen_name"]))
                    try:
                        V = json_data["retweeted_status"]["user"]["id"]
                    except:
                        continue;
                    if (U, V) in edges_dict:
                        edges_dict[(U, V)] += 1
                    else:
                        edges_dict[(int(U), int(V))] = 1
    candedit_dict = {}
    for cand in edges_dict:
        if str(cand[1]) in parliamentarians_id:
            continue
        elif cand[1] in candedit_dict:
            candedit_dict[cand[1]]+= edges_dict[cand]
        else:
            candedit_dict[cand[1]] = edges_dict[cand]
    for cand1 in edges_dict:
        if cand1[0] not in candedit_dict:
            candedit_dict[cand1[0]] = 0
    candidate_list = [k for k in sorted(candedit_dict, key=candedit_dict.get, reverse=True)]
    for i in range(min(non_parliamentarians_nodes,(len(candidate_list)))):
    for key in [key for key in edges_dict if (str(key[0]) not in parliamentarians_id) or (str(key[1]) not in parliamentarians_id)]: del edges_dict[key]
    return edges_dict


def construct_heb_network(network_dict):
    G = nx.DiGraph()
    for i in network_dict:
        G.add_weighted_edges_from([(i[0],i[1],network_dict[i])])
    return G

# 
def tester(fath):
    G = nx.les_miserables_graph()
    tmp = community_detector('louvain',G.copy())
    print('louvain algorithem:')
    print(tmp)
    # print('modularity = ' + str(tmp['modularity']))
    # print('num_partitions = ' + str(tmp['num_partitions']))
    tmp = community_detector('clique_percolation', G.copy())
    print('clique percolation algorithem:')
    print(tmp)
    # print('modularity = ' + str(tmp['modularity']))
    # print('num_partitions = ' + str(tmp['num_partitions']))
    tmp = community_detector('girvin_newman',G.copy())
    print('girvin newman algorithem:')
    print(tmp)
    # print('modularity = ' + str(tmp['modularity']))
    # print('num_partitions = ' + str(tmp['num_partitions']))
    tmp = community_detector('girvin_newman',G.copy(),most_valualble_edge=edge_selector_optimizer)
    print('girvin newman algorithem with edge selector optimizer:')
    print(tmp)
    # print('modularity = ' + str(tmp['modularity']))
    # print('num_partitions = ' + str(tmp['num_partitions']))
    # print("----------helek bet--------------")
    for i in range(1):
        print("non_parliamentarians_nodes = " + str(i*10))
        dct = construct_heb_edges(fath,start_date='2019-03-15',end_date='2019-03-15', non_parliamentarians_nodes=999999999999999999)
        print("len of dict = " + str(len(dct)))
        G = (construct_heb_network(dct))
        print('num of nodes = ' + str(G.number_of_nodes()))
        print('num of edges = ' + str(G.number_of_edges()))
        #tmp = (community_detector('girvin_newman',G.copy(),most_valualble_edge=edge_selector_optimizer))
        print('modularity = ' + str(tmp['modularity']))
        print('num_partitions = ' + str(tmp['num_partitions']))
        #tmp = (community_detector('girvin_newman', G.copy()))
        print('modularity = ' + str(tmp['modularity']))
        print('num_partitions = ' + str(tmp['num_partitions']))

