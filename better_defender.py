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

def move(bot, state):

    if state is None:
        # initialize the state dictionary
        state = {}
        # each bot needs its own state dictionary to keep track of the food targets
        state[0] = (None, None)
        state[1] = (None, None)
        # initialize a graph representation of the maze this can be shared among our bots
        state['graph'] = walls_to_nxgraph(bot.walls)

    target, cluster = state[bot.turn]


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
        target = cluster[random.randint(0,len(cluster)-1)]
    state[bot.turn] = (target, cluster)
    print("going to cluster", cluster)
    
    if not bot.enemy[0].is_noisy:
        # if our turn companion is not noisy, go for it
        if bot.enemy[0].position in bot.legal_positions:
            target = bot.enemy[0].position
            
    if not bot.enemy[1].is_noisy:
        # if the other enemy is not noisy, go for it
        if bot.enemy[1].position in bot.legal_positions:
            target = bot.enemy[1].position

    # get the next position along the shortest path to our target enemy bot
    shortest_path = nx.shortest_path(state['graph'], bot.position, target)
    if len(shortest_path)>=2:
        next_pos = shortest_path[1]
    else:
        next_pos = shortest_path[0]

    # let's check that we don't go into the enemy homezone, i.e. stop at the
    # border
    if next_pos in bot.enemy[turn].homezone:
        next_pos = bot.position

    return next_pos, state

