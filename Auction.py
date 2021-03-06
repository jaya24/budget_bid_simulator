import numpy as np
import time


class Auction:

    def __init__(self, nBidders, nSlots, mu, sigma, lambdas, myClickProb):
        self.nBidders = nBidders
        self.nSlots = nSlots
        self.mu = mu
        self.sigma = sigma
        self.lambdas = lambdas
        self.pClick = myClickProb
        if(nBidders < nSlots):
            print "nBidders should be >= than nSlots"

    def simulateAuction(self, myBid):
        return self.simulateMultipleAuctions(1, myBid)

    def simulateMultipleAuctions(self, nAuctions, myBid):
        # Generate other bids and qualities
        bids = np.maximum( np.random.randn(self.nBidders, nAuctions) * self.sigma + self.mu, 0.0)
        pClicks = np.random.beta(1, 1, (self.nBidders, nAuctions))
        expValue = bids * pClicks

        indexMatr = (expValue > (myBid * self.pClick)).astype(int)

        myPos = np.sum(indexMatr, axis=0)
        cpc = np.max(bids * (1-indexMatr), axis=0)
        pObsSlot = np.zeros(nAuctions)
        idxVisible = np.argwhere(myPos < self.nSlots).reshape(-1)
        pObsSlot[idxVisible] = self.lambdas[myPos[idxVisible]]
        return [cpc, myPos, pObsSlot]
