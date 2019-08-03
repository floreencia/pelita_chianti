# This bot tries to catch an enemy bot. It will stop at the border of its
# homezone if the enemy still did not cross the border.
# As long as the enemies are far away (their position is noisy), the bot
# tries to get near to the bot in the enemy team which has the same turn.
# As soon as an enemy bot is not noisy anymore, i.e. it has come near, the
# bot goes after it and leaves the other enemy alone

TEAM_NAME = 'Better Defender Bots'

#from pelita.utils import Graph
from utils import walls_to_nxgraph
#from utils import shortest_path
from better_attacker import largest_food_clusters
import networkx as nx
import random
import numpy as np

def move(bot, state):

    if state is None:
        # initialize the state dictionary
        state = {}
        # each bot needs its own state dictionary to keep track of the food targets
        state['bot_status'] = (None, None)
        # initialize a graph representation of the maze this can be shared among our bots
        state['graph'] = walls_to_nxgraph(bot.walls)

    target, cluster = state['bot_status']


    turn = bot.turn
    #if bot.enemy[0].is_noisy and bot.enemy[1].is_noisy:
    #print("both enemies are noisy")
    # if both enemies are noisy, just aim for our turn companion

    if (target is None) or (cluster is None) or (len(cluster) == 0):
        print("reset cluster")
        cluster_list = largest_food_clusters(state['graph'], bot.enemy[0])
        cluster = cluster_list.pop(0)
        target = cluster[0]
    if bot.position in cluster:
        print("we are in the cluster")
        if (not bot.enemy[0].is_noisy):
            en_dist_list = []
            for cl_food in cluster:
                en_path = nx.shortest_path(state['graph'], bot.enemy[0].position, cl_food)
                en_dist = len(en_path)
                en_dist_list.append(en_dist)
            food_ix = np.argmin(en_dist_list)
            target = cluster[food_ix]
        elif (not bot.enemy[1].is_noisy):
            en_dist_list = []
            for cl_food in cluster:
                en_path = nx.shortest_path(state['graph'], bot.enemy[1].position, cl_food)
                en_dist = len(en_path)
                en_dist_list.append(en_dist)
            food_ix = np.argmin(en_dist_list)
            target = cluster[food_ix]
        else:
            bot.say("You Shall Not Pass!")
            target = bot.position
            #target = cluster[random.randint(0, len(cluster) - 1)]
        

    state['bot_status'] = (target, cluster)
    print("going to cluster", cluster)

    ate_a_guy = False
    if not bot.enemy[0].is_noisy:
        # if our turn companion is not noisy, go for it
        if bot.enemy[0].position in bot.legal_positions:
            target = bot.enemy[0].position
            ate_a_guy = True

    if not bot.enemy[1].is_noisy:
        # if the other enemy is not noisy, go for it
        if bot.enemy[1].position in bot.legal_positions:
            target = bot.enemy[1].position
            ate_a_guy = True

    # get the next position along the shortest path to our target enemy bot
    
    print("target", target)
    print("bot.food", bot.food)
    if target not in bot.food:
        print("enemy ate our clusters food")
        state['bot_status'] = (None, None)

    shortest_path = nx.shortest_path(state['graph'], bot.position, target)
    if len(shortest_path)>=2:
        next_pos = shortest_path[1]
    else:
        next_pos = shortest_path[0]

    # let's check that we don't go into the enemy homezone, i.e. stop at the
    # border
    if next_pos in bot.enemy[turn].homezone:
        next_pos = bot.position

    if ate_a_guy:
        state['bot_status'] = (None, None)

    
    return next_pos, state

