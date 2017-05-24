#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import numpy as np
import math
from Campaign import *
from Environment import *
from Auction import *
from Agent import *
from Core import *


convparams=np.array([0.4,100,200])
# ho messo prob di conversione a 0.4 a caso,mentre 100 e 200 sono i due estremi della uniforme per generare le revenues
lambdas = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
deadline=5
a1= Auction(4,5,0.5,0.1, lambdas)
a2= Auction(5,5, 0.8, 0.2, lambdas)
c1 = Campaign(a1,1000.0,0.5,convparams)
c2 = Campaign(a2,1500.0, 0.5,convparams)
ag1 = Agent(1000, deadline, 2)
ag1.initGPs()
env = Environment([c1,c2])
core = Core(ag1, env, deadline)


core.step()
core.runEpisode()

