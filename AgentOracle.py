# -*- coding: utf-8 -*-
"""
Created on Wed May 24 10:44:49 2017

@author: alessandro
"""

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from matplotlib import pyplot as plt
import time as time
from Agent import *
from Environment import *
from Utils import *


# [NOTA] rivedere in quanto non agente
class Oracle(Agent):

    def __init__(self, budgetTot, deadline, nCampaigns, nBudget, nBids, maxBudget=100.0, maxBid=2.0,environment = None):
        self.budgetTot = budgetTot
        self.deadline = deadline
        self.nCampaigns = nCampaigns
        self.costs = np.array([])
        self.revenues = np.array([])
        self.t = 0

        # Historical data: GP prediction
        self.gpsClicks = []
        self.gpsCosts = []
        self.gps3D = []
        self.alphasClicksGP =np.ones(self.nCampaigns)  # for 3D gp

        self.alphasPotClicksGP =np.ones(self.nCampaigns) # for 2D GP
        self.alphasPotCostsGP =np.ones(self.nCampaigns)  # for 2D GP


        # Historical data: realizations
        self.prevBudgets = np.array([])
        self.prevBids = np.array([])
        self.prevClicks = np.array([])
        self.prevConversions = np.array([])
        self.prevCosts = np.array([])
        self.prevHours = np.array([])

        # Estimated value per click (initially small)
        self.valuesPerClick = np.zeros(nCampaigns)

        self.maxTotDailyBudget = maxBudget
        self.maxBid = maxBid
        self.nBudget = nBudget
        self.nBids = nBids
        self.bidBudgetMatrix = np.zeros(shape=(self.nCampaigns, self.nBids, self.nBudget))

        self.budgets = np.linspace(0, maxBudget, nBudget)
        self.bids = np.linspace(0, maxBid, nBids)
        self.optimalBidPerBudget = np.zeros((nCampaigns, nBudget))

        self.campaignsValues = np.zeros(shape=(self.nCampaigns, nBudget))
        self.clicksPerBid = np.zeros(shape=(self.nCampaigns, nBids))
        self.costsPerBid = np.zeros(shape=(self.nCampaigns, nBids))
        self.budgetPerBid =  np.zeros(shape=(self.nCampaigns, nBids))
        self.ymax = np.ones((nCampaigns))

        self.environment = environment




    def updateValuesPerClick(self,values):
        self.valuesPerClick=values




    def initGPs(self):
        for c in range(0, self.nCampaigns):
            #C(1.0, (1e-3, 1e3))
            #l= np.array([200,200])
            #kernel = C(1, (1e-3, 1e1))*RBF(l, ((100, 300),(100,300)))
            l1 = np.array([1.0])
            l2 = np.array([1.0])
            kernel1 = C(1.0, (1e-3, 1e3))*RBF(l1,(1e-3, 1e3))
            kernel2 = C(1.0, (1e-3, 1e3))*RBF(l2,(1e-3, 1e3))
            #l=1.0
            #kernel = C(1.0, (1e-3, 1e3)) * RBF(l, (1e-3, 1e3))
            alpha1 = self.alphasPotClicksGP[c]
            alpha2 = self.alphasPotCostsGP[c]
            #alpha1 = 1000.0
            #alpha2 = 1000.0
            self.gpsClicks.append(GaussianProcessRegressor(kernel=kernel2, alpha=alpha1, n_restarts_optimizer=10,normalize_y=True))
            self.gpsCosts.append(GaussianProcessRegressor(kernel=kernel1, alpha=alpha2, n_restarts_optimizer=10,normalize_y=True))

    def initGPs3D(self):
        for c in range(0,self.nCampaigns):
            C(1.0, (1e-3, 1e3))
            l = np.array([1.0, 1.0])
            kernel = C(1.0, (1e-3, 1e3))*RBF(l, ((1e-3, 1e3),(1e-3, 1e3)))
            alpha = self.alphasClicksGP[c]
            self.gps3D.append(GaussianProcessRegressor(kernel=kernel,alpha=alpha,n_restarts_optimizer=10,normalize_y=True))



    def updateClickGP(self,c, nSamples):
        clicks = self.environment.campaigns[c].clicks
        hours = self.environment.campaigns[c].hours
        bids = self.environment.campaigns[c].bid
        budgets = self.environment.campaigns[c].budget

        # Sample random observations
        nObservations = len(bids)
        idxs = np.arange(0,nObservations)
        idxs = np.random.choice(idxs,nSamples,replace=False)
        clicks = clicks[idxs]
        hours = hours[idxs]
        bids = bids[idxs]
        budgets = budgets[idxs]

        x = np.array([bids.T])
        xnorm=self.normalize(x).reshape(-1)
        idxsNoZero = np.argwhere(budgets!=0).reshape(-1)
        xnorm = xnorm[idxsNoZero]
        xnorm = np.atleast_2d(xnorm)
        potentialClicks = dividePotentialClicks(clicks* 24.0, hours)
        y = potentialClicks.T.ravel()
        # remove 0 in training
        y = y[idxsNoZero]
        if(len(y)>0):
            self.gpsClicks[c].fit(xnorm.T, y)





    def updateCostGP(self,c, nSamples):

        costs = self.environment.campaigns[c].costs
        hours = self.environment.campaigns[c].hours
        bids = self.environment.campaigns[c].bid
        budgets = self.environment.campaigns[c].budget

        # Sample random observations
        nObservations = len(bids)
        idxs = np.arange(0,nObservations)
        idxs = np.random.choice(idxs,nSamples,replace=False)
        costs = costs[idxs]
        hours = hours[idxs]
        bids = bids[idxs]
        budgets = budgets[idxs]

        x = np.array([bids.T])
        xnorm = self.normalize(x).reshape(-1)
        idxsNoZero = np.argwhere(budgets != 0).reshape(-1)

        xnorm = xnorm[idxsNoZero]
        xnorm = np.atleast_2d(xnorm)
        potentialCosts = dividePotentialClicks(costs * 24.0, hours)
        y = potentialCosts.T.ravel()
        y = y[idxsNoZero]
        if(len(y)>0):
            self.gpsCosts[c].fit(xnorm.T, y)


    def updateGP3D(self,c,nSamples):
        # Sample random observations
        nObservations = len(self.environment.campaigns[c].bid)
        idxs = np.arange(0,nObservations)
        idxs = np.random.choice(idxs,nSamples,replace=False)

        clicks = self.environment.campaigns[c].clicks[idxs]
        hours = self.environment.campaigns[c].hours[idxs]
        bids = self.environment.campaigns[c].bid[idxs]
        budgets = self.environment.campaigns[c].budget[idxs]


        #bids=np.atleast_2d(bids)
        #budgets=np.atleast_2d(budgets)
        #clicks=np.atleast_2d(clicks)
        x=np.array([bids,budgets])
        x=np.atleast_2d(x).T
        x=self.normalize3D(x)
        #potentialClicks = self.dividePotentialClicks(self.prevClicks * 24.0, self.prevHours)
        #y=potentialClicks.T[c,:].ravel()
        y=clicks.T.ravel()
        y=self.normalizeOutput(y,c)
        self.fitPrior(c,x,y)

    def updateMultiGP3D(self,nSamples):
        for c in range(0,self.nCampaigns):
            self.updateGP3D(c,nSamples)

    def updateGP(self,c,nSamples):
        self.updateCostGP(c, nSamples)
        self.updateClickGP(c, nSamples)



    def updateMultiGP(self,nSamples):
        for c in range(0, self.nCampaigns):
            self.updateGP(c,nSamples)




    def updateState(self,bids,budgets,clicks,conversions,costs,revenues,hours):
        bids=np.atleast_2d(bids)
        budgets=np.atleast_2d(budgets)
        clicks=np.atleast_2d(clicks)
        conversions=np.atleast_2d(conversions)
        hours=np.atleast_2d(hours)
        costs=np.atleast_2d(costs)
        revenues=np.atleast_2d(revenues)


        if(self.t==0):
            self.prevBudgets = budgets
            self.prevBids = bids
            self.prevClicks = clicks
            self.prevConversions = conversions
            self.prevHours = hours
            self.prevCosts = costs
            self.prevRevenues = revenues
        else:
            self.prevBudgets = np.append(self.prevBudgets,budgets, axis=0)
            self.prevBids = np.append(self.prevBids,bids, axis=0)
            self.prevClicks = np.append(self.prevClicks,clicks, axis=0)
            self.prevConversions = np.append(self.prevConversions,conversions, axis=0)
            self.prevHours = np.append(self.prevHours,hours, axis=0)
            self.prevCosts = np.append(self.prevCosts, costs, axis=0)
            self.prevRevenues = np.append(self.prevRevenues, revenues, axis=0)
        self.updateMultiGP()
        self.updateValuesPerClick()
        self.t +=1

    def valueForBudget(self,itemIdx,budget,values):
        idx = np.isclose(budget,self.budgets)
        if (len(idx)>0):
            return values[itemIdx,idx]
        idx = np.argwhere(budget>=self.budgets)
        return values[itemIdx,idx.max()]

    def firstRow(self,values):
        firstRow = np.zeros(len(self.budgets)).tolist()
        for i,b in enumerate(self.budgets):
            firstRow[i]=[[values[0,i]],[0],[b]]
        return firstRow



    def optimize(self,values):
        valIdx = 0
        itIdx = 1
        bIdx = 2
        h = np.zeros(shape=(self.nCampaigns, len(self.budgets)))
        h=h.tolist()
        h[0] = self.firstRow(values)
        for i in range(1, self.nCampaigns):
            for j,b in enumerate(self.budgets):
                h[i][j] = h[i-1][j][:]
                maxVal = 0
                for bi in range(0,j+1):
                    if ((np.sum(h[i-1][bi][valIdx]) + self.valueForBudget(i,b - self.budgets[bi],values)) >maxVal):
                        val = h[i-1][bi][valIdx][:]
                        val.append(self.valueForBudget(i,b - self.budgets[bi],values))
                        newValues = val[:]
                        items = h[i-1][bi][itIdx][:]
                        items.append(i)
                        newItems = items[:]
                        selBudgets = h[i-1][bi][bIdx][:]
                        selBudgets.append(b - self.budgets[bi])
                        newSelBudgets = selBudgets[:]
                        h[i][j]=[newValues,newItems,newSelBudgets]
                        maxVal = np.sum(newValues)
        newBudgets=h[-1][-1][2]
        newCampaigns=h[-1][-1][1]
        estimLeads = h[-1][-1][0]
        return [newBudgets,newCampaigns,estimLeads]


    def updateCostsPerBids(self):
        for c in range(0, self.nCampaigns):
            bidPoints = self.bids[:]
            x = np.array([bidPoints.T])
            x = np.atleast_2d(x).T
            x = self.normalize(x)
            [mean,sigma]=self.gpsCosts[c].predict(x,return_std=True)
            self.costsPerBid[c,:] = np.random.normal(mean,sigma)
            idxs = np.argwhere(self.bids==0).reshape(-1)
            for i in idxs:
                self.costsPerBid[c,i]=0.0



        return self.costsPerBid


    def updateClicksPerBids(self):
        for c in range(0, self.nCampaigns):
            bidPoints = self.bids[:]
            x = np.array([bidPoints.T])
            x = np.atleast_2d(x).T
            x = self.normalize(x)

            [mean,sigma]=self.gpsClicks[c].predict(x,return_std=True)
            self.clicksPerBid[c,:] = np.random.normal(mean,sigma)

            idxs = np.argwhere(self.bids==0).reshape(-1)
            for i in idxs:
                self.clicksPerBid[c,i]=0.0

        return self.clicksPerBid


    def generateBidBudgetMatrix(self,nSimul):
        alphasPotClicks = np.zeros((self.nCampaigns,self.nBids,self.nBudget))
        alphasPotCosts = np.zeros((self.nCampaigns,self.nBids,self.nBudget))
        alphasClicks = np.zeros((self.nCampaigns,self.nBids,self.nBudget))

        for i,bid in enumerate(self.bids):
            for j,bud in enumerate(self.budgets):
                nClicks = np.zeros((nSimul,self.nCampaigns,))
                costs = np.zeros((nSimul,self.nCampaigns))
                hours = np.zeros((nSimul,self.nCampaigns))

                for n in range(0,nSimul):
                    [nClicks[n,:],_, costs[n,:],_,hours[n,:]] = self.environment.generateObservationsforCampaigns(np.ones(self.nCampaigns)*bid,np.ones(self.nCampaigns)*bud)
                self.bidBudgetMatrix[:,i, j] =np.mean(nClicks,axis=0)
                alphasPotClicks[:,i,j] = np.std(dividePotentialClicks(nClicks*24.0,hours),axis=0)
                alphasPotCosts[:,i,j] = np.std(dividePotentialClicks(costs*24.0,hours),axis=0)
                alphasClicks[:,i,j] = np.std(nClicks,axis=0)

        self.alphasPotClicksGP = np.mean(np.mean(alphasPotClicks,axis=1),axis=1)
        self.alphasPotClicksGP = np.maximum(self.alphasPotClicksGP,0.1)**2
        self.alphasPotCostsGP = np.mean(np.mean(alphasPotCosts,axis=1),axis=1)
        self.alphasPotCostsGP = np.maximum(self.alphasPotCostsGP,0.1)**2

        self.alphasClicksGP = np.mean(np.mean(alphasClicks,axis=1),axis=1)
        self.alphasClicksGP = np.maximum(self.alphasClicksGP,0.1)**2

        #self.alphasClicksGP =np.ones(self.nCampaigns)*1000.0
        #self.alphasCostsGP =np.ones(self.nCampaigns)*1000.0



    def updateOptimalBidPerBudget(self):
        for c in range(0, self.nCampaigns):
            for b in range(0, self.nBudget):
                idx = np.argwhere(self.bidBudgetMatrix[c,:,b]==self.bidBudgetMatrix[c,:,b].max()).reshape(-1)
                idx = np.random.choice(idx)
                self.optimalBidPerBudget[c,b] = self.bids[idx]


    def valuesForCampaigns(self,sampling=False):
        for c in range(0, self.nCampaigns):
            for b in range(0, self.nBudget):
                self.campaignsValues[c,b] = self.bidBudgetMatrix[c,:,b].max() * self.valuesPerClick[c]

        return self.campaignsValues

        #self.campaignsValues[c,b] = self.campaignsValues *



    """
    def valuesForCampaigns(self,sampling=False ,bidSampling = True):

        for c in range(0,self.ncampaigns):
            x = np.array([self.bids.T])
            x = np.atleast_2d(x).T
            x = self.normalize(x)
            [meanClicksPerBid,sigmaClicksPerBid] = self.gpsClicks[c].predict(x,return_std=True)

            #self.clicksPerBid[c,:] = meanClicksPerBid
            self.clicksPerBid[c,:] = np.random.normal(meanClicksPerBid,sigmaClicksPerBid)
            # RICORDA FARE SAMPLING TODO AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            [meanCostsPerBid, sigmaCostsPerBid] = self.gpsCosts[c].predict(x, return_std=True)

            self.costsPerBid[c,:] =  np.random.normal(meanCostsPerBid, sigmaCostsPerBid)

            for i,b in enumerate(self.budgets):
                self.campaignsValues[c,i] = self.valuesPerClick[c]*self.clicksForBudget(c,b)
                self.defineOptimalBidPerBudget(c,i)
        return self.campaignsValues
    """




    def chooseAction(self):
        #self.generateBidBudgetMatrix()
        self.updateOptimalBidPerBudget()
        values = self.valuesForCampaigns()
        [newBudgets,newCampaigns,estimLeads] = self.optimize(values)
        finalBudgets = np.zeros(self.nCampaigns)
        finalBids = np.zeros(self.nCampaigns)
        for i,c in enumerate(newCampaigns):
            finalBudgets[c] = newBudgets[i]
            idx = np.argwhere(np.isclose(self.budgets,newBudgets[i])).reshape(-1)
            finalBids[c] = self.optimalBidPerBudget[c,idx]
        print "EstimLeads",np.sum(estimLeads)
        return [finalBudgets,finalBids,estimLeads]



    def normalize(self,X):
       return X/(self.maxBid)

    def normalize3D(self,X):
        X[:,0] = X[:,0]/(self.maxBid)
        X[:,1] = X[:,1]/(self.maxTotDailyBudget)
        return X


    def prior(self,x,y):
        return 0.0
        max_y= np.max(y)
        return max_y * x[:,1]

    def fitPrior(self,gpIndex,x,y):

        y_new = y - self.prior(x,y)
        self.gps3D[gpIndex].fit(x,y_new)

    def predictPrior(self,gpIndex,x,returnStd = False):
        if(returnStd ==False):
            y = self.gps3D[gpIndex].predict(x,return_std=returnStd)
            y_new = y + self.prior(x,self.environment.campaigns[gpIndex].clicks)
            return y_new
        else:

            [mean_y,sigma_y] = self.gps3D[gpIndex].predict(x,return_std=returnStd)
            if (len(self.prevClicks)==0):
                return mean_y,sigma_y
            y_new = mean_y + self.prior(x,self.environment.campaigns[gpIndex].clicks)
            """
            print "\n"
            #print "prediction without prior:",mean_y
            y_new = mean_y + self.prior(x,self.prevClicks[:,gpIndex])
            #print "prediction with prior",y_new
            #print "x ",x
            #print "prior ",self.prior(x,self.prevClicks[:,gpIndex])
            print "prediction without prior:",mean_y
            print "prediction with prior",y_new
            print "x ",x
            print "prior ",self.prior(x,self.prevClicks[:,gpIndex])
            """
            return y_new,sigma_y
