# inference.py
# ------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


import itertools
import random
import busters
import game

from util import manhattanDistance, raiseNotDefined


class DiscreteDistribution(dict):
    """
    A DiscreteDistribution models belief distributions and weight distributions
    over a finite set of discrete keys.
    """
    def __getitem__(self, key):
        self.setdefault(key, 0)
        return dict.__getitem__(self, key)

    def copy(self):
        """
        Return a copy of the distribution.
        """
        return DiscreteDistribution(dict.copy(self))

    def argMax(self):
        """
        Return the key with the highest value.
        """
        if len(self.keys()) == 0:
            return None
        all = list(self.items())
        values = [x[1] for x in all]
        maxIndex = values.index(max(values))
        return all[maxIndex][0]

    def total(self):
        """
        Return the sum of values for all keys.
        """
        return float(sum(self.values()))

    def normalize(self):
        """
        Normalize the distribution such that the total value of all keys sums
        to 1. The ratio of values for all keys will remain the same. In the case
        where the total value of the distribution is 0, do nothing.
        >>> dist = DiscreteDistribution()
        >>> dist['a'] = 1
        >>> dist['b'] = 2
        >>> dist['c'] = 2
        >>> dist['d'] = 0
        >>> dist.normalize()
        >>> list(sorted(dist.items()))
        [('a', 0.2), ('b', 0.4), ('c', 0.4), ('d', 0.0)]
        >>> dist['e'] = 4
        >>> list(sorted(dist.items()))
        [('a', 0.2), ('b', 0.4), ('c', 0.4), ('d', 0.0), ('e', 4)]
        >>> empty = DiscreteDistribution()
        >>> empty.normalize()
        >>> empty
        {}
        """
        "*** YOUR CODE HERE ***"
        sum = self.total()
        if sum != 0:
            for key in self.keys():
                nValue = self[key] / sum
                self[key] = nValue
        return
    def sample(self):
        """
        Draw a random sample from the distribution and return the key, weighted
        by the values associated with each key.
        >>> dist = DiscreteDistribution()
        >>> dist['a'] = 1
        >>> dist['b'] = 2
        >>> dist['c'] = 2
        >>> dist['d'] = 0
        >>> N = 1000000.0
        >>> samples = [dist.sample() for _ in range(int(N))]
        >>> round(samples.count('a') * 1.0/N, 1)  # proportion of 'a'
        0.2
        >>> round(samples.count('b') * 1.0/N, 1)
        0.4
        >>> round(samples.count('c') * 1.0/N, 1)
        0.4
        >>> round(samples.count('d') * 1.0/N, 1)
        0.0
        """
        "*** YOUR CODE HERE ***"
        self.normalize()
        ranges = dict()
        accumulatedV = 0
        
        for key in self.keys():
            start = accumulatedV
            accumulatedV += self[key]
            end = accumulatedV
            ranges[key] = (start, end)
        
        sample = random.random()
        for key in ranges.keys():
            if sample >= ranges[key][0] and sample < ranges[key][1]:
                return key
        
        return sample.keys()[-1]


class InferenceModule:
    """
    An inference module tracks a belief distribution over a ghost's location.
    """
    ############################################
    # Useful methods for all inference modules #
    ############################################

    def __init__(self, ghostAgent):
        """
        Set the ghost agent for later access.
        """
        self.ghostAgent = ghostAgent
        self.index = ghostAgent.index
        self.obs = []  # most recent observation position

    def getJailPosition(self):
        return (2 * self.ghostAgent.index - 1, 1)

    def getPositionDistributionHelper(self, gameState, pos, index, agent):
        try:
            jail = self.getJailPosition()
            gameState = self.setGhostPosition(gameState, pos, index + 1)
        except TypeError:
            jail = self.getJailPosition(index)
            gameState = self.setGhostPositions(gameState, pos)
        pacmanPosition = gameState.getPacmanPosition()
        ghostPosition = gameState.getGhostPosition(index + 1)  # The position you set
        dist = DiscreteDistribution()
        if pacmanPosition == ghostPosition:  # The ghost has been caught!
            dist[jail] = 1.0
            return dist
        pacmanSuccessorStates = game.Actions.getLegalNeighbors(pacmanPosition, \
                gameState.getWalls())  # Positions Pacman can move to
        if ghostPosition in pacmanSuccessorStates:  # Ghost could get caught
            mult = 1.0 / float(len(pacmanSuccessorStates))
            dist[jail] = mult
        else:
            mult = 0.0
        actionDist = agent.getDistribution(gameState)
        for action, prob in actionDist.items():
            successorPosition = game.Actions.getSuccessor(ghostPosition, action)
            if successorPosition in pacmanSuccessorStates:  # Ghost could get caught
                denom = float(len(actionDist))
                dist[jail] += prob * (1.0 / denom) * (1.0 - mult)
                dist[successorPosition] = prob * ((denom - 1.0) / denom) * (1.0 - mult)
            else:
                dist[successorPosition] = prob * (1.0 - mult)
        return dist

    def getPositionDistribution(self, gameState, pos, index=None, agent=None):
        """
        Return a distribution over successor positions of the ghost from the
        given gameState. You must first place the ghost in the gameState, using
        setGhostPosition below.
        """
        if index == None:
            index = self.index - 1
        if agent == None:
            agent = self.ghostAgent
        return self.getPositionDistributionHelper(gameState, pos, index, agent)

    def getObservationProb(self, noisyDistance, pacmanPosition, ghostPosition, jailPosition):
        """
        Return the probability P(noisyDistance | pacmanPosition, ghostPosition).
        """
        "*** YOUR CODE HERE ***"
        if (noisyDistance is None):
            if (ghostPosition == jailPosition):
                return 1
            else:
                return 0
        if (ghostPosition == jailPosition):
            if (noisyDistance is None):
                return 1
            else:
                return 0
        trueDistance = manhattanDistance(pacmanPosition, ghostPosition)
        return busters.getObservationProbability(noisyDistance, trueDistance)

    def setGhostPosition(self, gameState, ghostPosition, index):
        """
        Set the position of the ghost for this inference module to the specified
        position in the supplied gameState.

        Note that calling setGhostPosition does not change the position of the
        ghost in the GameState object used for tracking the true progression of
        the game.  The code in inference.py only ever receives a deep copy of
        the GameState object which is responsible for maintaining game state,
        not a reference to the original object.  Note also that the ghost
        distance observations are stored at the time the GameState object is
        created, so changing the position of the ghost will not affect the
        functioning of observe.
        """
        conf = game.Configuration(ghostPosition, game.Directions.STOP)
        gameState.data.agentStates[index] = game.AgentState(conf, False)
        return gameState

    def setGhostPositions(self, gameState, ghostPositions):
        """
        Sets the position of all ghosts to the values in ghostPositions.
        """
        for index, pos in enumerate(ghostPositions):
            conf = game.Configuration(pos, game.Directions.STOP)
            gameState.data.agentStates[index + 1] = game.AgentState(conf, False)
        return gameState

    def observe(self, gameState):
        """
        Collect the relevant noisy distance observation and pass it along.
        """
        distances = gameState.getNoisyGhostDistances()
        if len(distances) >= self.index:  # Check for missing observations
            obs = distances[self.index - 1]
            self.obs = obs
            self.update(obs, gameState)

    def initialize(self, gameState):
        """
        Initialize beliefs to a uniform distribution over all legal positions.
        """
        self.legalPositions = [p for p in gameState.getWalls().asList(False) if p[1] > 1]
        self.allPositions = self.legalPositions + [self.getJailPosition()]
        self.initializeUniformly(gameState)

    ######################################
    # Methods that need to be overridden #
    ######################################

    def initializeUniformly(self, gameState):
        """
        Set the belief state to a uniform prior belief over all positions.
        """
        raise NotImplementedError

    def update(self, observation, gameState):
        """
        Update beliefs based on the given distance observation and gameState.
        """
        raise NotImplementedError

    def predict(self, gameState):
        """
        Predict beliefs for the next time step from a gameState.
        """
        raise NotImplementedError

    def getBeliefDistribution(self):
        """
        Return the agent's current belief state, a distribution over ghost
        locations conditioned on all evidence so far.
        """
        raise NotImplementedError


class ExactInference(InferenceModule):
    """
    The exact dynamic inference module should use forward algorithm updates to
    compute the exact belief function at each time step.
    """
    def initializeUniformly(self, gameState):
        """
        Begin with a uniform distribution over legal ghost positions (i.e., not
        including the jail position).
        """
        self.beliefs = DiscreteDistribution()
        for p in self.legalPositions:
            self.beliefs[p] = 1.0
        self.beliefs.normalize()

    def update(self, observation, gameState):
        """
        Update beliefs based on the distance observation and Pacman's position.

        The observation is the noisy Manhattan distance to the ghost you are
        tracking.

        self.allPositions is a list of the possible ghost positions, including
        the jail position. You should only consider positions that are in
        self.allPositions.

        The update model is not entirely stationary: it may depend on Pacman's
        current position. However, this is not a problem, as Pacman's current
        position is known.
        """
        "*** YOUR CODE HERE ***"
        pacmanPosition = gameState.getPacmanPosition()
        jailPosition = self.getJailPosition()
        for ghostPosition in self.allPositions:
            self.beliefs[ghostPosition] *= self.getObservationProb(observation, 
            pacmanPosition, ghostPosition, jailPosition)
        self.beliefs.normalize()
        

    def predict(self, gameState):
        """
        Predict beliefs in response to a time step passing from the current
        state.

        The transition model is not entirely stationary: it may depend on
        Pacman's current position. However, this is not a problem, as Pacman's
        current position is known.
        """
        # pacmanPosition = gameState.getPacmanPosition()
        # jailPosition = self.getJailPosition()
        # for oldPos in self.allPositions:
        #     newPosDist = self.getPositionDistribution(gameState, oldPos)
        #     predictP = 0
        #     p_oldPos = self.beliefs[oldPos]
        #     #P(x0)
        #     for pos in self.allPositions:  
        #         predictP += newPosDist[pos]*p_oldPos
        #     self.beliefs[oldPos] *= predictP
        # self.beliefs.normalize()
        newbeliefs = DiscreteDistribution()
        for ghostPosition in self.allPositions:
            newPosDist = self.getPositionDistribution(gameState, ghostPosition)
            for pos in newPosDist.keys():
                prob = newPosDist[pos]
                newbeliefs[pos] += prob * self.beliefs[ghostPosition]
        newbeliefs.normalize()
        self.beliefs = newbeliefs

            
    def getBeliefDistribution(self):
        return self.beliefs


class ParticleFilter(InferenceModule):
    """
    A particle filter for approximately tracking a single ghost.
    """
    def __init__(self, ghostAgent, numParticles=300):
        InferenceModule.__init__(self, ghostAgent)
        self.setNumParticles(numParticles)

    def setNumParticles(self, numParticles):
        self.numParticles = numParticles

    def initializeUniformly(self, gameState):
        """
        Initialize a list of particles. Use self.numParticles for the number of
        particles. Use self.legalPositions for the legal board positions where
        a particle could be located. Particles should be evenly (not randomly)
        distributed across positions in order to ensure a uniform prior. Use
        self.particles for the list of particles.
        """
        self.particles = []
        #step 1 dict -> postion: prob
        num_per_pos = self.numParticles//len(self.legalPositions)
        distribution = DiscreteDistribution()
        for pos in self.legalPositions:
            for i in range(num_per_pos):
                self.particles.append(pos)
        distribution.normalize()
        #step 2 Sample the partciples => build the list
        extra = self.numParticles - num_per_pos * len(self.legalPositions)
        for i in range(extra):
            addition = self.legalPositions[i]
            self.particles.append(addition)
        return self.particles

        "*** YOUR CODE HERE ***"

    def update(self, observation, gameState):
        """
        Update beliefs based on the distance observation and Pacman's position.

        The observation is the estimated Manhattan distance to the ghost you are
        tracking.
        """
        cur_beliefs = DiscreteDistribution()
        pacmanPosition = gameState.getPacmanPosition()
        jailPosition = self.getJailPosition()
        particle_count = {}
        for particle in self.particles:
            if particle in particle_count:
                particle_count[particle] += 1
            else:
                particle_count[particle] = 1
        for particle in self.particles:
            weight = self.getObservationProb(observation, pacmanPosition, particle, jailPosition)
            particle_prob = particle_count[particle]
            cur_beliefs[particle] = weight * particle_prob
        if (DiscreteDistribution(cur_beliefs).total() == 0):
            self.initializeUniformly(gameState)
        else:
            cur_beliefs.normalize()
            for k in range(self.numParticles):
                new_particle = DiscreteDistribution(cur_beliefs).sample()
                self.particles[k] = new_particle

    def predict(self, gameState):
        """
        Sample each particle's next state based on its current state and the
        gameState.
        """
        posDistDic = {}
        new_particles = []
        for particle in self.particles:
            if particle in posDistDic:
                newPosDist = posDistDic[particle]
            else:
                newPosDist = self.getPositionDistribution(gameState, particle)
                posDistDic[particle] = newPosDist
            new_particle = DiscreteDistribution(newPosDist).sample()
            new_particles.append(new_particle)
        self.particles = new_particles

    def getBeliefDistribution(self):
        """
        Return the agent's current belief state, a distribution over ghost
        locations conditioned on all evidence and time passage. This method
        essentially converts a list of particles into a belief distribution.
        """
        "*** YOUR CODE HERE ***"
        distribution = DiscreteDistribution()
        for pos in self.particles:
            if pos in distribution:
                distribution[pos] += 1
            else:
                distribution[pos] = 1
        distribution.normalize()
        return distribution


class JointParticleFilter(ParticleFilter):
    """
    JointParticleFilter tracks a joint distribution over tuples of all ghost
    positions.
    """
    def __init__(self, numParticles=600):
        self.setNumParticles(numParticles)

    def initialize(self, gameState, legalPositions):
        """
        Store information about the game, then initialize particles.
        """
        self.numGhosts = gameState.getNumAgents() - 1
        self.ghostAgents = []
        self.legalPositions = legalPositions
        self.initializeUniformly(gameState)

    def initializeUniformly(self, gameState):
        """
        Initialize particles to be consistent with a uniform prior. Particles
        should be evenly distributed across positions in order to ensure a
        uniform prior.
        """
        self.particles = []
        allPermutations = list(itertools.product(self.legalPositions, repeat = self.numGhosts))
        random.shuffle(allPermutations)
        for i in range(self.numParticles):
            index = i % len(allPermutations)
            self.particles.append(allPermutations[index])
        return self.particles

    def addGhostAgent(self, agent):
        """
        Each ghost agent is registered separately and stored (in case they are
        different).
        """
        self.ghostAgents.append(agent)

    def getJailPosition(self, i):
        return (2 * i + 1, 1)

    def observe(self, gameState):
        """
        Resample the set of particles using the likelihood of the noisy
        observations.
        """
        observation = gameState.getNoisyGhostDistances()
        self.update(observation, gameState)

    def update(self, observation, gameState):
        """
        Update beliefs based on the distance observation and Pacman's position.

        The observation is the estimated Manhattan distances to all ghosts you
        are tracking.
        """
        pacmanPosition = gameState.getPacmanPosition()
        cur_beliefs = DiscreteDistribution()
        for particle in self.particles:
            jointP = 1
            for k in range(self.numGhosts):
                jailPosition = self.getJailPosition(k)
                weight = self.getObservationProb(observation[k], pacmanPosition, particle[k], jailPosition)
                jointP *= weight
            cur_beliefs[particle] += jointP
        if (cur_beliefs.total() == 0):
            self.initializeUniformly(gameState)
        else:
            cur_beliefs.normalize()
            for k in range(self.numParticles):
                new_particle = cur_beliefs.sample()
                self.particles[k] = new_particle

        
    def predict(self, gameState):
        """
        Sample each particle's next state based on its current state and the
        gameState.
        """
        newParticles = []
        posDistDic = {}
        for oldParticle in self.particles:
            newParticle = list(oldParticle)  # A list of ghost positions
            prevGhostPositions = list(oldParticle)
            for i in range(self.numGhosts):
                if (oldParticle,i) in posDistDic:
                    newPosDist = posDistDic[oldParticle,i]
                else:
                    newPosDist = self.getPositionDistribution(gameState, prevGhostPositions, i, self.ghostAgents[i]) 
                    posDistDic[oldParticle,i] = newPosDist
                new_ghost_pos = newPosDist.sample()
                newParticle[i] = new_ghost_pos
            newParticles.append(tuple(newParticle))
        self.particles = newParticles


# One JointInference module is shared globally across instances of MarginalInference
jointInference = JointParticleFilter()


class MarginalInference(InferenceModule):
    """
    A wrapper around the JointInference module that returns marginal beliefs
    about ghosts.
    """
    def initializeUniformly(self, gameState):
        """
        Set the belief state to an initial, prior value.
        """
        if self.index == 1:
            jointInference.initialize(gameState, self.legalPositions)
        jointInference.addGhostAgent(self.ghostAgent)

    def observe(self, gameState):
        """
        Update beliefs based on the given distance observation and gameState.
        """
        if self.index == 1:
            jointInference.observe(gameState)

    def predict(self, gameState):
        """
        Predict beliefs for a time step elapsing from a gameState.
        """
        if self.index == 1:
            jointInference.predict(gameState)

    def getBeliefDistribution(self):
        """
        Return the marginal belief over a particular ghost by summing out the
        others.
        """
        jointDistribution = jointInference.getBeliefDistribution()
        dist = DiscreteDistribution()
        for t, prob in jointDistribution.items():
            dist[t[self.index - 1]] += prob
        return dist
