import numpy as np
import csv
from matplotlib import pyplot as plt
from AgentOracle import *
from matplotlib2tikz import save as tikz_save

path0 = '../resultsPAPER/results_9200NCampaignsSettings_SameOracle/'
#path0 ='../results_1016NCampaignsSettings/'
nCampaignsSettings = np.array([3,4,5,6])

nAgents=4
regr = np.zeros((len(nCampaignsSettings), nAgents))
optRegr = np.zeros(len(nCampaignsSettings))
for d in range(0,len(nCampaignsSettings)):

    path = path0+str(nCampaignsSettings[d])+'_campaigns/'
    agentPath = np.load(path + "Agents.npy")
    nExperiments = 63
    nCampaigns = nCampaignsSettings[d]

    optimum = np.load(path + "opt.npy")
    print "Oracle Optimum ", optimum
    print "sum Optimum", np.sum(optimum)
    optPol = np.load(path + "optPolicy.npy")

    optBidBudMatrix = np.load(path + "OracleBidBudMatrix.npy")
    bids = np.linspace(0.0, 1.0, 5)
    #legend = ['AdComB-BUCB']


    budgets = np.linspace(0.0, 100.0, 10)

    convparams = np.load(path + "ConversionValues.npy")

    T = np.load(path + "Deadline.npy")
    T=100

    def budIndex(bud):
        return np.argwhere(np.isclose(budgets, bud)).reshape(-1)

    def bidIndex(bid):
        return np.argwhere(np.isclose(bids,bid)).reshape(-1)

    def calcClicks(bidArray,budArray,convParams):
        clicks = []
        for i in range(0,len(bidArray)):
            budInd = budIndex(budArray[i])
            bidInd = bidIndex(bidArray[i])
            c = optBidBudMatrix[i, bidInd, budInd]
            clicks.append(c)
        clicks = np.array(clicks)
        return np.sum(clicks.reshape(-1)*convParams[:nCampaigns,0])

    def calcClicksForExperiment(policy, deadline, convParams):
        clicks = np.array([])
        for t in range(0,deadline):
            bidArray = policy[0,t,:]
            budArray = policy[1,t,:]
            clicks = np.append(clicks, calcClicks(bidArray, budArray, convParams))
        return clicks

    # Plotting single agents results
    res = []
    observedRes = []
    for a in range(0, len(agentPath)):
        conv = []
        pol = []
        expClicks = []
        for e in range(0,nExperiments):
            temp = np.load(path + agentPath[a] + "experiment_" + str(e) + ".npy")
            tempPol = np.load(path+ agentPath[a] + "policy_" + str(e) + ".npy")
            if len(temp) > 0:
                conv.append(temp)
                pol.append(tempPol)
                expClicks.append(calcClicksForExperiment(tempPol,T,convparams))
        conv = np.array(conv)
        pol = np.array(pol)
        expClicks = np.array(expClicks)
        res.append(np.mean(expClicks, axis=0))

    legend = ['AdComB-TS', 'AdComB-Mean', 'AdComB-BUCB', 'AdComB-3D', 'Oracle']


    # All mean results in a single plot
    res = np.array(res)



    # REGRET plot
    opt = np.ones((len(agentPath), T)) * np.sum(optimum)
    opt = np.ones((len(agentPath), T)) * 19.45

    regret = np.cumsum((opt - res[0:len(agentPath), 0:T]), axis=1)

    regr[d,:] = regret[:,-1]




#plt.title("Cumulated Expected Pseudo-Regret")

plt.xlabel(r'$|C|$',fontsize=20)
plt.ylabel(r'$R_T(\mathfrak{U})$',fontsize=20)
plt.plot(nCampaignsSettings,regr)
plt.legend(legend)
plt.xticks(nCampaignsSettings)

tikz_save('nCampaigns.tex');
