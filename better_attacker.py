# This bot selects a food pellet at random, then goes and tries to get it by
# following the shortest path to it.
# It tries on the way to avoid being eaten by the enemy: if the next move
# to get to the food would put it on a ghost, then it chooses a random safe
# position
TEAM_NAME = 'Cianti Attackers'

from pelita.utils import Graph

import networkx as nx
from utils import walls_to_nxgraph
import numpy as np

def largest_food_clusters(net, bot):
    """
    Returns a list of lists with the coordinates of the food, sorted by size of the cluster
    """
    ## set food attr
    for n in net.nodes:
        if n in bot.enemy[0].food:
            net.node[n]['food'] = True
        else:
            net.node[n]['food'] = False
    
    ## define food network
    food_node_dict = nx.get_node_attributes(net, 'food')
    food_nodes = [k for k in food_node_dict if food_node_dict[k]]
    foodnet = net.subgraph(food_nodes)

    ## find largest food cluster
    fnets = list(nx.connected_component_subgraphs(foodnet))
    net_sizes = ([(i, len(thisnet.nodes)) for i, thisnet in enumerate(fnets)])
    largest_food_cluster_ix = sorted(net_sizes, key=lambda x: x[1], reverse=True)
    coordinates_li = [list(fnets[ix].nodes) for ix,_ in largest_food_cluster_ix]

    return coordinates_li


def shortest_path_to_cluster(coordinates_list, bot, net):
    '''returns path to closest food pellet in a cluster
    Parameters
    -----------
    coordiates_list: list
    list of the coordinates of the food in a cluster
    bot: Bot object
    net: nx Graph
    graph of the walls
    Return
    ------
    shortest path to cluster
    '''
    food_shp = []
    ## path to food in cluster
    for pos in coordinates_list:
        food_shp.append(nx.shortest_path(net, bot.position, pos))

    ## path length (index, path_len)
    path_len = ([(i, len(path)) for i, path in enumerate(food_shp)])
    shortest_path_2food_ix = min(path_len, key=lambda x: x[1])[0]

    return food_shp[shortest_path_2food_ix]




def move(bot, state):
    enemy = bot.enemy
    # we need to create a dictionary to keep information (state) along rounds
    # the state object will be passed untouched at every new round
    if state is None:
        # initialize the state dictionary
        state = {}
        # each bot needs its own state dictionary to keep track of the food targets
        state[0] = (None, None, None)
        state[1] = (None, None, None)
        # initialize a graph representation of the maze this can be shared among our bots
        state['graph'] = walls_to_nxgraph(bot.walls)

    target, path, cluster = state[bot.turn]

    print("pos",bot.position, "target", target, "cluster", cluster)
    if bot.position==target or bot.other.position==target:
        print("We ate it")
        cluster.remove(target)
    # choose a target food pellet if we still don't have one or
    # if the old target has been already eaten
    if (target is None) or (len(cluster) == 0):
        print("resetting cluster")
        # position of the target food pellet
        # shortest path from here to the target
        cluster_list = largest_food_clusters(state['graph'], bot)
        cluster = cluster_list.pop(0)
        # try to have both bots going for different clusters, when possible
        if state[abs(bot.turn - 1)][2] == cluster and len(cluster_list)!=0:
            cluster = cluster_list.pop(0)
        print("new cluster is", cluster)
        path = shortest_path_to_cluster(cluster, bot, state['graph']) #shortest_path(bot.position, target, state['graph'])
        path = path[1:]
        target = path[-1]
        state[bot.turn] = (target, path, cluster)
    elif (target not in enemy[0].food):
        print("new food in cluster")
        path = shortest_path_to_cluster(cluster, bot, state['graph']) #shortest_path(bot.position, target, state['graph'])
        path = path[1:]
        target = path[-1]
        state[bot.turn] = (target, path, cluster)


    # get the next position along the shortest path to reach our target
    next_pos = path.pop(0)
    # get a list of safe positions
    safe_positions = []
    #print("new")
    #print("en", (enemy[0].position, enemy[1].position))
    for pos in bot.legal_positions:
        # a position is safe if the enemy is not sitting on it *and*
        # the enemy does not sit in the neighborhood of that position
        safe = True
        for direction in ((0, 0), (0,1), (0,-1), (1,0), (-1,0)):
            neighbor = (pos[0] + direction[0], pos[1] + direction[1])
            #print("pos", pos, "neighbor:", neighbor, "safe:", neighbor in (enemy[0].position, enemy[1].position))
            
            close_enemies = []
            if not bot.enemy[0].is_noisy:
                close_enemies.append(enemy[0].position)
            if not bot.enemy[1].is_noisy:
                close_enemies.append(enemy[1].position)

            if neighbor in close_enemies:
                safe = False
                break
        if safe:
            safe_positions.append(pos)
        #print("pos", pos," safe ", safe)

    # we now may have duplicates in the list of safe positions -> get rid
    # of them not to bias the random choice
    #print(safe_positions)
    safe_positions = list(set(safe_positions))
    # are we about to move to an unsafe position?
    if next_pos not in safe_positions:
        # 1. Let's forget about this target and this path
        #    We will choose a new target in the next round
        state[bot.turn] = (None, None, None)
        # Choose one safe position at random if we have any
        if safe_positions:
            next_pos = bot.random.choice(safe_positions)
        else:
            # we are doomed anyway
            if next_pos in (enemy[0].position, enemy[1].position):
                next_pos = bot.position
            else:
                # unless the next step is suicide, just pursue our goal
                pass


    # if we are irreparably stuck, only suicide will help
    lastten = np.asarray(bot.track[-10:])
    suicide_possible_b0 = (not bot.enemy[0].is_noisy) & (bot.enemy[0].position in bot.legal_positions)
    suicide_possible_b1 = (not bot.enemy[1].is_noisy) & (bot.enemy[1].position in bot.legal_positions)
    if (len(np.unique(lastten)) < 4):
        bot.say("I am stuck!")
        state[bot.turn] = (None, None, None)
    if (len(np.unique(lastten)) < 4) & (suicide_possible_b0 or suicide_possible_b1):
        bot.say("goodbye, cruel world")
        if suicide_possible_b0:
            next_pos = bot.enemy[0].position
        elif suicide_possible_b1:
            next_pos = bot.enemy[1].position

    return next_pos, state

