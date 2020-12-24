# myTeam.py
# ---------
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


from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game
from util import nearestPoint


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'AttackAgent', second = 'DefendAgent'):
    # The following line is an example only; feel free to change it.
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


class ReflexCaptureAgent(CaptureAgent):
    """
    A base class for reflex agents that chooses score-maximizing actions
    """
 
    def registerInitialState(self, gameState):
        self.start = gameState.getAgentPosition(self.index)
        CaptureAgent.registerInitialState(self, gameState)

    def chooseAction(self, gameState):       
        
        actions = gameState.getLegalActions(self.index)
        
        actions.remove(Directions.STOP)
        
        values = [self.MTCS(gameState.generateSuccessor(self.index, a),a) for a in actions]
        bestActions = [a for a, v in zip(actions, values) if v == max(values)]
            
        return random.choice(bestActions)

    def getSuccessor(self, gameState, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
          # Only half a grid position was covered
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
        """
        Computes a linear combination of features and feature weights
        """
        
        features = self.getFeatures(gameState)
        weights = self.getWeights(gameState)
        
        return features * weights

    def getFeatures(self, gameState, action):
        """
        Returns a counter of features for the state
        """
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)
        return features

    def getWeights(self, gameState, action):
        """
        Normally, weights do not depend on the gamestate.  They can be either
        a counter or a dictionary.
        """
        return {'successorScore': 1.0}


class AttackAgent(ReflexCaptureAgent):

    def MTCS(self,gameState,a):
        """
        Monte-Carlo search works with a gameState and action
        
        """
        result_list = [] #result_list stores the result of each playout 
        

        """
        Copying the current state and evaluating it.
        
        """
        copy_state = gameState.deepCopy()
        value = self.evaluate(copy_state, a)
        
 
        """
        Depth is a var to which gameState will be evaluated.
        d id the decay value, helps reduce bias
        
        """       
        
        depth = 2
        d = 1
        result_list.append(value)
        
        while depth > 0:

            actions = copy_state.getLegalActions(self.index)
            
            """
            Removing STOP direction to reduce evaluation time as STOPing the agent
            won't do any good in most of the cases.
            
            """  
            
            actions.remove(Directions.STOP)
            current_direction = copy_state.getAgentState(self.index).getDirection()
            
            
            """
            Removing REVERSE direction to reduce evaluation time also reduces back and forth movement of the Agent
            
            """  
            
            if Directions.REVERSE[current_direction] in actions and len(actions) > 1:
                actions.remove(Directions.REVERSE[current_direction])
            
            selectAction = random.choice(actions)
            
            
            """
            Generating new GameState for the action selected at Random.
            
            """  
            
            copy_state = copy_state.generateSuccessor(self.index, selectAction)

#            0.6 reduces bias
            """
            Evaluate the new GameState and add result to the list.
            
            """  
    
            result_list.append(0.6 ** d * self.evaluate(copy_state, selectAction))
            depth -= 1
            d += 1
            
        return sum(result_list)
    
    
    """
    Get all the vertical points in middle of the Agents home maze.

    """  
    def getMid(self,gameState):
        if self.red:
            midX = (gameState.data.layout.width - 2)//2
        else:
            midX = ((gameState.data.layout.width - 2)//2) + 1
        
        safetyLayoutList = [(midX, y) for y in range(gameState.data.layout.height) if not gameState.hasWall(midX, y)]                      
        return safetyLayoutList

    def getFeatures(self, gameState):
        
        
        """
        Get features used for state evaluation.
        """
        features = util.Counter()
        successor = gameState.deepCopy()

        features['successorScore'] = self.getScore(successor)

        currentPos = successor.getAgentState(self.index).getPosition()
        
        
        """
        Distance to Nearest Middle point from getMid .
        """
        getSafe = self.getMid(gameState)
        features['midDistance'] = min([self.getMazeDistance(currentPos, getSafe[loc]) for loc in range(len(getSafe))]) 
        
        
        """
        Number for food Agent is carrying .
        """
        features['numCarrying'] = successor.getAgentState(self.index).numCarrying
        
        
        """
        Distance to nearest Food from Agent's current position .
        """
        foodList = self.getFood(successor).asList()
        if len(foodList) > 0 :            
            features['foodDistance'] = min([self.getMazeDistance(currentPos, food) for food in foodList]) 

        
        """
        Distance to nearest capsule from Agent's current position .
        """
        capsulesList = self.getCapsules(successor)
        if len(capsulesList) > 0:
            features['capsuleDistance'] = min([self.getMazeDistance(currentPos, capsule) for capsule in capsulesList])
        else:
            features['capsuleDistance'] = 0
        
        
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        
        
        """
        Distance to nearest Enemy from Agent's current position in Home maze.
        If not seen than Noisy distance of both Enemies and select minimum distance
        """
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        if len(invaders) > 0:
            features['invaderDistance'] = min([self.getMazeDistance(currentPos, a.getPosition()) for a in invaders])
        else:
            features['invaderDistance'] = min([successor.getAgentDistances()[i] for i in self.getOpponents(successor)])
           
        
        """
        Distance to nearest Enemy from Agent's current position OUTSITE Home maze.
        If not seen than Noisy distance of both Enemies and select minimum distance
        """ 
        enemyPos = [a for a in enemies if (not a.isPacman) and a.getPosition() != None]
        if len(enemyPos) > 0:
            features['minEnemyDist'] = min([self.getMazeDistance(currentPos, a.getPosition()) for a in enemyPos])
        else:
            features['minEnemyDist'] = min([successor.getAgentDistances()[i] for i in self.getOpponents(successor)])
            
        return features

    def getWeights(self, gameState):
        """
        Get weights for the features used in the evaluation.
        """

        # If opponent is scared, the agent should not care about invaderDistance
        successor = gameState.deepCopy()
        numCarrying = successor.getAgentState(self.index).numCarrying
        
        currentPos = successor.getAgentState(self.index).getPosition()        
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        
        enemyPos = [a for a in enemies if (not a.isPacman) and a.getPosition() != None]
        if len(enemyPos) > 0:
            for agent in enemyPos:
                
                
                """
                If enemy scared, reduce food priority and try eating the capsule avoiding the enemy
                """
                if agent.scaredTimer > 0:
                    return {'successorScore': 1000, 'foodDistance': -5, 'invaderDistance': -2, 'capsuleDistance': -20,'minEnemyDist': -8, 'midDistance': -8, 'numCarrying': 100}
                
        """
        Weights when not scared. Priority to Food and also similar to enemy in home maze
        """     
        return {'successorScore': 1000*numCarrying, 'foodDistance': -9, 'invaderDistance': -7, 'capsuleDistance': -10,'minEnemyDist': -17, 'midDistance': -13, 'numCarrying': 400}

##########
# Agents #
##########    
        
class DefendAgent(CaptureAgent):

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.ownFood = self.getFoodYouAreDefending(gameState).asList()
        

    """
    Get all the vertical points in middle of the Agents home maze.

    """  
    def getMid(self,gameState):
        if self.red:
            midX = (gameState.data.layout.width - 2)//2
        else:
            midX = ((gameState.data.layout.width - 2)//2) + 1
        
        safetyLayoutList = [(midX, y) for y in range(gameState.data.layout.height) if not gameState.hasWall(midX, y)]                      
        return safetyLayoutList
    
    def chooseAction(self, gameState):
        currentPos = gameState.getAgentState(self.index).getPosition()
                
        mid = self.getMid(gameState)
        
        
        """
        Reach to the vertical middle area of home Maze when no enemy around.

        """ 
        distanceToMid = [(self.getMazeDistance(currentPos, midPoint), midPoint) for midPoint in mid]
        nearestMid, midpoint = min(distanceToMid)
        
        if nearestMid < 5:
            distanceToMid.remove((nearestMid, midpoint))
            nearestMid, midpoint = max(distanceToMid)
        
        
        """
        Get list of Own Food.
        Check if any food is eaten
        Set nearestPoint and midPoint to the food location with dist
        """ 
        currentFood = self.getFoodYouAreDefending(gameState).asList()
        if( (len(currentFood) - len(self.ownFood)) != 0 ):
            foodEaten = set(self.ownFood).difference(set(currentFood))
            
            if len(foodEaten) != 0:
                nearestMid, midpoint = min([(self.getMazeDistance(currentPos,food),food) for food in foodEaten])

            self.ownFood = currentFood
        
        
        """
        Get list of Enemies.
        Get list of Enemy in home maze.
        If yes, then Update the nearestPoint and midPoint
        """ 
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        if len(invaders) > 0:
            nearestMid, midpoint = min([(self.getMazeDistance(currentPos, a.getPosition()),a.getPosition()) for a in invaders])

#        actions = gameState.getLegalActions(self.index)
        copy_state = gameState.deepCopy()
        
        
        """
        Getting actions for current state and  removing STOP direction
        """ 
        actions = copy_state.getLegalActions(self.index)
        actions.remove(Directions.STOP)
        
        """
        Getting List of all the positions possible after taking the legal actions
        List = [(Pos,action)]
        """ 
        getNewPosList = [(copy_state.generateSuccessor(self.index, selectAction).getAgentPosition(self.index),selectAction) for selectAction in actions]
        
        """
        Getting List of distance from the NewPos above and the MIDPOINT var set above, along with the action that fulfills the task
        List = min[(Dist,action)]
        """ 
        getNewPosDist,action = min([(self.getMazeDistance(getPos, midpoint), action) for getPos,action in getNewPosList])
            
        return action        
        