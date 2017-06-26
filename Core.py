

from Agent import Agent
from Environment import Environment
import time as time
import numpy as np
import time as time

class Core:
    def __init__(self,agent,environment, deadline,plotter =None):
        self.agent=agent
        self.environment=environment
        self.deadline = deadline
        self.plotter = plotter
        self.t=0



    def step(self,fixedBid=True):
        [budget,bid] = self.agent.chooseAction(sampling=True,fixedBid=fixedBid,fixedBidValue=1.0)
        observations = self.environment.step(bid,budget)
        if(fixedBid == True):
            print("Fixed bid in the step function")
        lastClicks = observations[0]
        lastConversions = observations[1]
        lastCosts = observations[2]
        lastRevenues = observations[3]
        lastHours = observations[4]
        self.agent.updateState(bid,budget,lastClicks,lastConversions,lastCosts,lastRevenues,lastHours)

        self.t+=1




    def runEpisode(self):
        for t in range(0,self.deadline):
            print "Day : ",t
            #start = time.time()
            self.step()
            #print time.time() - start

