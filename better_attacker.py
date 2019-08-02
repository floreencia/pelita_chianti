# This bot selects a food pellet at random, then goes and tries to get it by
# following the shortest path to it.
# It tries on the way to avoid being eaten by the enemy: if the next move
# to get to the food would put it on a ghost, then it chooses a random safe
# position
TEAM_NAME = 'Cianti Attackers'

from pelita.utils import Graph

import networkx as nx
from utils import walls_to_nxgraph


def largest_food_cluster(net, bot):
    ## set food attr
    for n in net.nodes:
        if n in bot.enemy[0].food:
            net.node[n]['food'] = True

    ## define food network
    food_dict = nx.get_node_attributes(net, 'food')
    foodnet = net.subgraph(food_dict.keys())

    ## find largest food cluster
    fnets = list(nx.connected_component_subgraphs(foodnet))
    net_sizes = ([(i, len(thisnet.nodes)) for i, thisnet in enumerate(fnets)])
    largest_food_cluster = max(net_sizes, key=lambda x: x[1])[0]
    coordinates_li = list(fnets[largest_food_cluster].nodes)

    return coordinates_li


def shortest_path_to_cluster(coordinates_list, bot, net):
    '''returns path to closest food pellet
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
        # each bot needs its own state dictionary to keep track of the
        # food targets
        state[0] = (None, None, None)
        state[1] = (None, None, None)
        # initialize a graph representation of the maze
        # this can be shared among our bots
        state['graph'] = walls_to_nxgraph(bot.walls)

    target, path, cluster = state[bot.turn]
    print("target", target, "cluster", cluster)
    if bot.position==target:
        print("I ate it")
    # choose a target food pellet if we still don't have one or
    # if the old target has been already eaten
    if (target is None):
        print("resetting cluster")
        # position of the target food pellet
        #target = #bot.random.choice(enemy[0].food)
        # shortest path from here to the target
        cluster = largest_food_cluster(state['graph'], bot)
        path = shortest_path_to_cluster(cluster, bot, state['graph']) #shortest_path(bot.position, target, state['graph'])
        path = path[1:]
        target = path[-1]
        state[bot.turn] = (target, path, cluster)
    elif (target not in enemy[0].food):
        print("new food in cluster")
        cluster.remove(target)
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
        state[bot.turn] = (None, None)
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

    return next_pos, state

