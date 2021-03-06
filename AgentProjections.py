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


class Agent:

    def __init__(self,budgetTot,deadline,ncampaigns,nIntervals,nBids,maxBudget=100.0,maxBid=1.0):
        self.budgetTot = budgetTot
        self.deadline = deadline
        self.ncampaigns = ncampaigns
        self.costs = np.array([])
        self.revenues = np.array([])
        self.t = 0
        self.gps = []
        self.prevBudgets = np.array([])
        self.prevBids = np.array([])
        self.prevClicks = np.array([])
        self.prevCosts = np.array([])
        self.prevConversions = np.array([])
        self.prevRevenues = np.array([])
        self.prevHours = np.array([])
        self.valuesPerClick = np.zeros(ncampaigns)
        self.maxTotDailyBudget = maxBudget
        self.maxBid = maxBid
        self.nBudgetIntervals = nIntervals
        self.nBids = nBids

        self.budgets = np.linspace(0, maxBudget,nIntervals)
        self.bids = np.linspace(0,maxBid,nBids)
        self.optimalBidPerBudget = np.zeros((ncampaigns,nIntervals))

        self.campaignsValues = []
        self.ymax=np.ones((ncampaigns))


    def updateValuesPerClick(self):
        for c in range(0,self.ncampaigns):
            value = np.sum(self.prevConversions[:,c])/np.sum(self.prevClicks[:,c])
            if(np.isnan(value) or np.isinf(value)):
                self.valuesPerClick[c] = 0
            else:
                self.valuesPerClick[c] = value




    def initGPs(self):
        for c in range(0,self.ncampaigns):
            #C(1.0, (1e-3, 1e3))
            #l= np.array([200,200])
            #kernel = C(1, (1e-3, 1e1))*RBF(l, ((100, 300),(100,300)))
            l = np.array([1.0, 1.0])
            kernel = C(1.0, (1e-3, 1e3))*RBF(l, ((1e-3, 1e3),(1e-3, 1e3)))
            #l=1.0
            #kernel = C(1.0, (1e-3, 1e3)) * RBF(l, (1e-3, 1e3))
            alpha=200
            self.gps.append(GaussianProcessRegressor(kernel=kernel, alpha=alpha, n_restarts_optimizer=10,normalize_y=True))

    def dividePotentialClicks(self,numerator,denominator):
        div = numerator/denominator
        div[np.isnan(div)]=0
        div[np.isinf(div)]=0
        return div

    def updateGP(self,c):
        """
        self.prevBids=np.atleast_2d(self.prevBids)
        self.prevBudgets=np.atleast_2d(self.prevBudgets)
        self.prevClicks=np.atleast_2d(self.prevClicks)
        X=np.array([self.prevBids.T[c,:],self.prevBudgets.T[c,:]])
        X=np.atleast_2d(X).T
        X=self.normalize(X)
        #potentialClicks = self.dividePotentialClicks(self.prevClicks * 24.0, self.prevHours)
        #y=potentialClicks.T[c,:].ravel()
        y=self.prevClicks.T[c,:].ravel()
        y=self.normalizeOutput(y,c)
        self.gps[c].fit(X, y)
        """
        self.prevBids = np.atleast_2d(self.prevBids)
        potentialCosts = self.dividePotentialClicks(self.prevCosts*24.0,self.prevHours)
        potentialCosts= np.atleast_2d(potentialCosts)
        self.prevClicks = np.atleast_2d(self.prevClicks)
        X = np.array([self.prevBids.T[c, :], potentialCosts.T[c, :]])
        X = np.atleast_2d(X).T
        X = self.normalize(X)
        potentialClicks = self.dividePotentialClicks(self.prevClicks * 24.0, self.prevHours)
        y=potentialClicks.T[c,:].ravel()
        #y = self.prevClicks.T[c, :].ravel()
        #y = self.normalizeOutput(y, c)
        self.gps[c].fit(X, y)



    def updateMultiGP(self):
        for c in range(0,self.ncampaigns):
            self.updateGP(c)

    def updateState(self,bids,budgets,clicks,conversions,costs,revenues,hours):
        bids=np.atleast_2d(bids)
        budgets=np.atleast_2d(budgets)
        clicks=np.atleast_2d(clicks)
        conversions=np.atleast_2d(conversions)
        hours=np.atleast_2d(hours)
        costs=np.atleast_2d(costs)
        revenues=np.atleast_2d(revenues)
        """
        self.prevBids=np.atleast_2d(self.prevBids)
        self.prevBudgets=np.atleast_2d(self.prevBudgets)
        self.prevClicks=np.atleast_2d(self.prevClicks)
        self.prevConversions=np.atleast_2d(self.prevConversions)
        self.prevHours=np.atleast_2d(self.prevHours)
        """
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



    def optimize2(self,values):
        valIdx = 0
        itIdx = 1
        bIdx = 2


    def optimize(self,values):
        #start = time.time()
        valIdx = 0
        itIdx = 1
        bIdx = 2
        h = np.zeros(shape=(self.ncampaigns,len(self.budgets)))
        h=h.tolist()
        h[0] = self.firstRow(values)
        for i in range(1,self.ncampaigns):
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
        # se non mi lista alcune campagne le listo comunque con budget 0!
        if len(newBudgets) < self.ncampaigns:
            temp = np.zeros(self.ncampaigns)
            temp[newCampaigns] = newBudgets
            newBudgets = temp
            newCampaigns = np.array(range(0,self.ncampaigns))
        return [newBudgets,newCampaigns]

    def valuesForCampaigns(self,sampling=False ,bidSampling = True):
        estimatedClicks = np.zeros(shape=(self.ncampaigns, len(self.budgets)))
        if( sampling==False):
            for c in range(0,self.ncampaigns):
                for j,b in enumerate(self.budgets):
                    x= np.array([self.bids.T,np.matlib.repmat(b,1,self.nBids).reshape(-1)])
                    x=np.atleast_2d(x).T
                    x = self.normalize(x)
                    if(bidSampling==False):
                        estimatedClicksforBids=self.denormalizeOutput(self.gps[c].predict(x),c)
                        idxs = np.argwhere(estimatedClicksforBids == estimatedClicksforBids.max()).reshape(-1)
                        idx = np.random.choice(idxs)
                        self.optimalBidPerBudget[c,j] = self.bids[idx]
                        estimatedClicks[c,j] = estimatedClicksforBids.max()
                    else:
                        [meanEstimatedClicksForBids,sigmaEstimatedClicksForBids] = self.denormalizeOutput(self.gps[c].predict(x,return_std = True),c)
                        estimatedClicksforBids = np.random.normal(meanEstimatedClicksForBids,sigmaEstimatedClicksForBids)
                        idxs = np.argwhere(estimatedClicksforBids == estimatedClicksforBids.max()).reshape(-1)
                        idx = np.random.choice(idxs)
                        self.optimalBidPerBudget[c,j] = self.bids[idx]
                        estimatedClicks[c,j] = estimatedClicksforBids.max()
        else:
            for c in range(0, self.ncampaigns):
                for j, b in enumerate(self.budgets):
                    x= np.array([self.bids.T,np.matlib.repmat(b,1,self.nBids).reshape(-1)])
                    x = np.atleast_2d(x).T
                    x = self.normalize(x)
                    [means,sigmas] = self.gps[c].predict(x,return_std=True)

                    means = self.denormalizeOutput(means,c)
                    sigmas = self.denormalizeOutput(sigmas,c)
                    estimatedClicksforBids = np.random.normal(means,sigmas)
                    idxs = np.argwhere(estimatedClicksforBids == estimatedClicksforBids.max()).reshape(-1)
                    idx = np.random.choice(idxs)
                    self.optimalBidPerBudget[c, j] = self.bids[idx]
                    estimatedClicks[c, j] = estimatedClicksforBids.max()

        self.campaignsValues=estimatedClicks*self.valuesPerClick.reshape((self.ncampaigns,1))
        return estimatedClicks*self.valuesPerClick.reshape((self.ncampaigns,1))


    def chooseAction(self,sampling=False, fixedBid=False, fixedBudget=False, fixedBidValue=1.0, fixedBudgetValue=1000.0):

        """
        finalBudgets = np.zeros(self.ncampaigns)
        finalBids = np.zeros(self.ncampaigns)

        for i in range(0,self.ncampaigns):
            finalBudgets[i] = np.random.choice(self.budgets)
            finalBids[i] = np.random.choice(self.bids)

        if (fixedBid == True):
            finalBids = np.ones(self.ncampaigns) * fixedBidValue

        if (fixedBudget == True):
            finalBudgets = np.ones(self.ncampaigns)* fixedBudgetValue
        """
        values = self.valuesForCampaigns(sampling=sampling)

        #values = self.valuesCorrection(values)

        [newBudgets,newCampaigns] = self.optimize(values)
        finalBudgets = np.zeros(self.ncampaigns)
        finalBids = np.zeros(self.ncampaigns)
        for i,c in enumerate(newCampaigns):
            finalBudgets[c] = newBudgets[i]
            idx = np.argwhere(np.isclose(self.budgets,newBudgets[i])).reshape(-1)
            finalBids[c] = self.optimalBidPerBudget[c,idx]
        return [finalBudgets,finalBids]


    def valuesCorrection(self,values):
        for c in range(0,self.ncampaigns):
            for b in range(1,self.nBudgetIntervals):
                if(values[c,b]<values[c,b-1]):
                    values[c,b] = values[c,b-1]
            return values

    def normalizeBudgetArray(self,budgetArray):
        return budgetArray/self.maxTotDailyBudget

    def normalizeBidsArray(self,bidsArray):
        return bidsArray/self.maxBid


    def normalize(self,X):
        X[:,0] = X[:,0]/(self.maxBid)
        X[:,1] = X[:,1]/(self.maxTotDailyBudget)
        return X

    def normalizeOutput(self,y,campaign):
        return y
        if(y.max()!=0):
            self.ymax[campaign] = y.max()
            y=y/y.max()
        return y


    def denormalizeOutput(self,y,campaign):
        return y
        return y*self.ymax[campaign]


    def findBestBidPerBudget(self,budget,bidsArray,gpIndex):
        x = np.array([bidsArray.T, np.matlib.repmat(budget, 1, len(bidsArray)).reshape(-1)])
        x = np.atleast_2d(x).T
        x = self.normalize(x)
        valuesforBids = self.denormalizeOutput(self.gps[gpIndex].predict(x), gpIndex)
        idxs = np.argwhere(valuesforBids == valuesforBids.max()).reshape(-1)
        idx = np.random.choice(idxs)
        return bidsArray[idx]


    def bestBidsPerBudgetsArray(self,budgetArray,bidsArray,gpIndex):
        bestBidsArray= np.zeros(len(budgetArray))
        for i,b in enumerate(budgetArray):
            bestBidsArray[i]=self.findBestBidPerBudget(b,bidsArray,gpIndex)
        return bestBidsArray
