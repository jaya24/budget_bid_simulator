import numpy as np
import csv
from matplotlib import pyplot as plt

path = '../resultsSuc/'
results = np.load(path + "allExperiments.npy" )
opt = np.load(path + "opt.npy")
results= results[:,0]
conv = np.mean(results)
std = np.std(results)
plt.plot(conv)
plt.plot(np.ones(len(conv))*np.sum(opt))
plt.plot(conv +std)
