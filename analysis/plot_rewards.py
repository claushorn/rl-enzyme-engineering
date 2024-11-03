import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.helpers import this_package_path
import numpy as np
import matplotlib.pyplot as plt

sdate = '2024-10-18/13-49-07'
sdate = '2024-10-21/23-34-14'
sdate = '2024-10-23/15-13-45'
sdate = '2024-10-25/07-55-15'
sdate = '2024-10-29/09-04-06'
sdate = '2024-10-29/09-37-37'

mdates = {
    '2024-10-26/13-28-35' : '1bcu',
    '2024-10-26/10-25-07' : '2YMD',
    '2024-10-26/08-19-11' : '3PRS',
    '2024-10-26/11-31-49' : '1p1q',
    '2024-10-26/09-49-24' : '3dxg',
    '2024-10-25/15-46-20' : '3dxg',
    '2024-10-25/16-25-52' : '1o0H',
    '2024-10-25/20-37-44' : '2BRB'
}


def plot_reward_evolution_fromLog(sdate, runtype='frontier', logformat=1, sTitle=''):
    sPath = this_package_path()+f'/rl-enzyme-engineering/experiments/{sdate}/'

    if runtype == 'main':
        file = open(sPath+ 'main.log', 'r')
    if runtype == 'frontier':
        file = open(sPath+ 'main_frontier.log', 'r')

    lines = file.readlines()
    file.close()

    # discard all lines without 'Reward:'
    if logformat == 1:
        rewards = [float(line.split('Reward:')[1].strip()) for line in lines if 'Reward:' in line]
    if logformat == 2:
        rewards = [float(line.split('reward:')[1].split(',')[0].strip()) for line in lines if 'reward:' in line]
    #print(rewards)

    # calculate cumulative sum of rewards
    #if logformat == 2:
    #    rewards = np.cumsum(rewards)

    # plot rewards
    plt.plot(rewards)
    plt.ylabel('Reward')
    plt.xlabel('Steps')
    plt.title(sTitle)

    # save plot
    #plt.savefig(sPath + 'rewards.png')
    plt.savefig("./results/" + f"rewardEvolution_{sTitle}_{sdate.replace('/','_')}.png")
    plt.show()

plot_reward_evolution_fromLog(sdate, runtype='main', logformat=2)
exit()

for sdate in mdates.keys():
    print(mdates[sdate])
    plot_reward_evolution_fromLog(sdate, mdates[sdate])
