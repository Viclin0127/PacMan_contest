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
import copy

from captureAgents import CaptureAgent
import random, util


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'DummyAgent', second = 'DummyAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

targetFood = None
class DummyAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    self.start = gameState.getAgentPosition(self.index)


    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''
    self.cost = 0
    self.food = self.getFood(gameState).asList()
    self.totalFoodNumber = len(self.food)
    self.foodLeft = self.totalFoodNumber
    self.carry = gameState.getAgentState(self.index).numCarrying
    self.myPosition = gameState.getAgentPosition(self.index)
    self.isDefense = False
    # maze distance to my position, it's a dictionary
    self.myStepTo = self.stepToMe(gameState)
    self.targetFood = random.choice(self.getFood(gameState).asList())
    self.initalTarget(gameState)
    self.safeFoddList = self.initialSafeFoodList(gameState)
    self.defenseTarget = self.start

    global targetFood
    targetFood = self.targetFood

    self.weights = util.Counter({"Food": 93, "FoodCarrying": 87, "Enemy": 100,
                                "Capsule": 87, "Teammate": 5,"Defense": 50, "Home": 500, "Bias": 55})

    # self.weights = util.Counter()
    # # read weights from file
    # file = open("weightUpdating.txt", "r+")
    # f = file.readlines()
    # print("Read file: ", f)
    # for line in f:
    #   line = line.split(":")
    #   weight = line[0].strip()
    #   value = float(line[1])
    #   self.weights[weight] = value
    # file.close()




  #################
  # derived funcs #
  #################

  # choose an action based on Q_value of that specific action
  # set up some conditions
  def chooseAction(self, gameState):
    global targetFood

    # if both enemies are not pacman, no need to be defense mode!
    if not self.getEnemy(gameState)[0][0] and self.getEnemy(gameState)[1][0]:
      self.isDefense = False

    # [condition] : avoid enemy, treat its surrounding as walls
    for isPacman, position, distance, isScared in self.getEnemy(gameState):
      if (not isPacman) and (not isScared) and (position is not None):
        x, y = position
        gameState.data.layout.walls[x][y] = True
        gameState.data.layout.walls[x + 1][y] = True
        gameState.data.layout.walls[x - 1][y] = True
        gameState.data.layout.walls[x][y + 1] = True
        gameState.data.layout.walls[x][y - 1] = True

    self.cost+=1
    self.food = self.getFood(gameState).asList()
    self.foodLeft = len(self.food)
    self.carry = gameState.getAgentState(self.index).numCarrying
    self.myPosition = gameState.getAgentPosition(self.index)
    self.myStepTo = self.stepToMe(gameState)

    # [condition] : if defense mode on! and agent is not pacman
    if (self.isDefense) and (not gameState.getAgentState(self.index).isPacman):
      # if agent still has capsule to eat, change to defense that capsule
      if len(self.getCapsulesYouAreDefending(gameState))>0 and self.defenseTarget == self.start:
        self.defenseTarget = self.getCapsulesYouAreDefending(gameState)[0]

    # [condition] : if this is not first move, which means agent has Previous State
    # agent need to check the different from previous state
    if not self.getPreviousObservation() is None:
      # capsules miss? change agent target
      if len(self.getCapsules(self.getPreviousObservation())) - len(self.getCapsules(gameState)) == 1:
        self.changeNearestFood(gameState)
      # food miss? change agent target
      if (not self.targetFood in self.food):
        self.changeNearestFood(gameState)
      # ate a food, change agent target
      if self.getPreviousObservation().getAgentState(self.index).numCarrying < self.carry:
        self.changeNearestFood(gameState)

      # previous agent is not pacman and now is pacman
      if (not self.getPreviousObservation().getAgentState(self.index).isPacman) and gameState.getAgentState(
              self.index).isPacman:
        self.changeNearestFood(gameState)
      # detect if any food was eaten, if any, change target to that position
      defendFood = self.getFoodYouAreDefending(gameState).asList()
      preDefendFood = self.getFoodYouAreDefending(self.getPreviousObservation()).asList()
      if len(preDefendFood) - len(defendFood) == 1:
        for food in preDefendFood:
          if not(food in defendFood):
            self.defenseTarget = food
            break
        print("food be eaten", self.defenseTarget)

    # [condition] : if food left (3-5), which means very close to end game,
    # one of agent can go back to defense
    if self.foodLeft <=5 and self.foodLeft >= 3:
      if self.carry == 0 and gameState.getAgentState((self.index+2)%4).isPacman:
        self.isDefense = True
      else:
        self.isDefense = False

    # [condition] : if my target is very close to my teammate's (10 steps ),
    # if yes, change my target far away from my teammates
    if self.getMazeDistance(self.targetFood, targetFood) <= 10 and \
      self.getMazeDistance(self.myPosition, self.targetFood)>= \
      self.getMazeDistance(gameState.getAgentPosition((self.index+2)%4), self.targetFood):
      self.changeTargetAwayToTeammate(gameState)


    print("Agent ", self.index)
    # print("Defense Mode: ", self.isDefense)
    # print("Cost ", self.cost)
    # print("current pos: ", self.myPosition)
    # print("target: ", self.targetFood)
    # print("Carrying: ", self.carry)
    # print("enemy: ", self.getEnemy(gameState))

    action = self.selectAction(gameState)
    # update target food to global variable, so teammate can detect my target
    targetFood = self.targetFood
    print("choose action:", action)

    # Doing updating
    # if gameState.getLegalActions(self.index) is not None:
    #   if len(gameState.getLegalActions(self.index)) != 0 and action != "Stop":
    #     self.updateWeights(gameState, action)

    print("------------------------------------")

    return action


  # calculate the features value based on a specific action which could trigger some events
  # using Decision Trees
  def getFeatures(self, gameState, action):
    successor = self.getSuccessor(gameState, action)
    features = util.Counter({"Food": 0, "FoodCarrying": 0, "Enemy": 0,
                                "Capsule": 0, "Teammate": 0, "Defense": 0, "Home": 0, "Bias": 1})

    # [condition] : agent is away from the enemy  , get point!
    # enemy(isPacman, position, distance, isScared)
    for i in range(len(self.getEnemy(gameState))):
      if (self.getEnemy(successor)[i][2] - self.getEnemy(gameState)[i][2]) > 1 and \
        successor.getAgentPosition(self.index) != self.start:
        features["Enemy"] = 100
        return features


    # [condition] : agent get a capsule while enemy is not scared! , get point!
    if len(self.getCapsules(gameState))-len(self.getCapsules(successor)) == 1:
      enemy1, enemy2 = self.getEnemy(gameState)
      if (not enemy1[3]) or (not enemy2[3]):
        features["Capsule"] = 200

    # [condition] : if teammate is close to me, lose point!
    if self.getMazeDistance(self.myPosition, gameState.getAgentPosition((self.index+2)%4)) <= 5:
      features["Teammate"] = -1


    """
    [Event] : capture enemy(pacman) -> if enemy is pacman , position can be observed, distance to me <=5
    and I'm ghost, not scared, (and no capsules in our area??!!)
    OR enemy is pacman, and I'm ghost and I'm defense
    """
    enemy = self.getEnemy(gameState)
    for i in range(len(self.getEnemy(gameState))):
      if (enemy[i][0] and (enemy[i][1] is not None) and enemy[i][2] < 5
          and (not gameState.getAgentState(self.index).isPacman)
          and gameState.getAgentState(self.index).scaredTimer ==0) and (not enemy[i][3]) \
        or (enemy[i][0] and self.isDefense and (not gameState.getAgentState(self.index).isPacman)):
        # more closer to enemy, get point!   ;  away from enemy, lose point!
        features["Enemy"] = enemy[i][2] - self.getEnemy(successor)[i][2]

        # if I have to save my teammate
        if self.isSaveTeammate(gameState):
          # there is a capsule I can eat (no barrier)
          if min(self.getCapsulesDistance(gameState))<9999:
            features["Enemy"] = 0
            features["Defense"] = 0
        # if in defense mode , and more closer to defense target, get point!
        elif self.isDefense:
          features["Defense"] = self.getMazeDistance(self.myPosition, self.defenseTarget) - \
                                self.getMazeDistance(successor.getAgentPosition(self.index), self.defenseTarget)
        # if enemy was captured (which means enemy reborn at start position)
        if features["Enemy"] < -1:
          features["Enemy"] = 100

        # if I'm scared, stay away from the enemy  (negative point of current features["Enemy])
        # no defense point
        if gameState.getAgentState(self.index).scaredTimer != 0:
          features["Enemy"] = -features["Enemy"]
          features["Defense"] = 0

        if self.isDefense:
          features["Bias"] = 0

        #TODO: if I can be the barrier on the path that enemy go back
        print("Capture Enemy ", action, features)
        return features
    """
    [Event] : Score!  -> if this successor back to the border and scored some points
    """
    # get point when this action can go back to score
    if self.backToScore(gameState, successor):
      features["FoodCarrying"] = abs(self.carry-successor.getAgentState(self.index).numCarrying)* 1000
      features["Home"] = self.getDistanceToHome(gameState) - self.getDistanceToHome(successor)
      print("Score! ", action, features)
      return features

    """
    [Event] : Escape! -> when I'm trying to eat (not safe food) food, if in below conditions, Escape!
    1. if target food is not safe or
    2. target food safe and teammate is pacman or
    3. no way home and no way to get capsule or
    4. there is a way to capsule
    """
    if not (self.targetFood in self.safeFoddList) or ((self.targetFood in self.safeFoddList) and
      gameState.getAgentState((self.index + 2) % 4).isPacman) or \
      (self.myStepTo[self.start] > 999 and min(self.getCapsulesDistance(gameState)) > 999) or \
            (min(self.getCapsulesDistance(gameState)) < 9999):

      # if enemy is 5 step close to me, not scared, and not pacman and I'm pacman, Escape!
      doEscape = False
      enemy = self.getEnemy(gameState)
      for i in range(len(self.getEnemy(gameState))):
        if gameState.getAgentState(self.index).isPacman and (not enemy[i][0]) and (not enemy[i][3]) and \
          (self.getEnemyDistance(gameState)[i] <= 5):
          doEscape = True
      # if no way home and no way to get capsule, Escape!
      if (self.myStepTo[self.start] > 999 and min(self.getCapsulesDistance(gameState)) > 999):
        doEscape = True
      # ok, do Escape!
      if (doEscape):

        # if there is still food, choose random food
        if len(self.food) != 0:
          self.targetFood = random.choice(self.getFood(gameState).asList())

        # if food left <= 2 and there is a way home(which means no barrier)
        # OR no way to get a capsule or no capsule anymore

        if (self.foodLeft <= 2 and self.getDistanceToHome(gameState) < 9999) or \
          (min(self.getCapsulesDistance(gameState)) > 999) or (len(self.getCapsules(gameState)) == 0):
          # lose point! when you get closer to teammate
          print("Event happened!")
          features["Teammate"] = self.getMazeDistance(successor.getAgentPosition(self.index),
                              successor.getAgentPosition((self.index + 2) % 4))- \
          self.getMazeDistance(gameState.getAgentPosition(self.index),
                               gameState.getAgentPosition((self.index + 2) % 4))

          # if I have a way home (no barrier)
          if self.getDistanceToHome(gameState) < 9999:
            features["Home"] = self.getDistanceToHome(gameState)- self.getDistanceToHome(successor)

          # if no way home
          else:
            features["Home"] = self.getMazeDistance(self.start, self.myPosition) - \
                               self.getMazeDistance(self.start, successor.getAgentPosition(self.index))
        else:

          # if still not get a capsule, add point if go closer to a capsule
          if features["Capsule"] != 200 :
            features["Capsule"] = min(self.getCapsulesDistance(gameState)) - min(self.getCapsulesDistance(successor))
        print("Escape! ", action, features)
        return features

    """
    [Event] : Go Home! -> if isGoHome condition is true, go home for some reason, still save teammate?!
    """
    if (self.isGoHome(gameState)):
      features["Home"] = self.getDistanceToHome(gameState) - self.getDistanceToHome(successor)
      # if I have to save my teammate
      if self.isSaveTeammate(gameState) and len(self.getCapsules(gameState)) != 0:
        if gameState.getAgentState((self.index + 2) % 4).isPacman:
          if self.getMazeDistance(self.myPosition, gameState.getAgentPosition((self.index+2)%4)) >= 3:
            features["Capsule"] = min(self.getCapsulesDistance(gameState)) - \
                                  min(self.getCapsulesDistance(successor))
            features["Home"] = 0
      # if teammate and I are both pacman or both ghost, keep distance to each other
      if gameState.getAgentState(self.index).isPacman == gameState.getAgentState((self.index + 2) % 4).isPacman:
        features["Teammate"] = self.getMazeDistance(successor.getAgentPosition(self.index),
                              successor.getAgentPosition((self.index + 2) % 4))- \
          self.getMazeDistance(gameState.getAgentPosition(self.index),
                               gameState.getAgentPosition((self.index + 2) % 4))

      # if there is no way home
      if self.getDistanceToHome(gameState) >999:
        features["Home"] = self.getMazeDistance(gameState.getAgentPosition(self.index), self.start) - \
                           self.getMazeDistance(successor.getAgentPosition(self.index), self.start)

      # if I'm ghost
      if (not gameState.getAgentState(self.index).isPacman):
        features["Home"] = 0
        features["Teammate"] = 0
        features["Bias"] = 0

      print("Go Home! ", action, features)
      return features

    """
    [Event] : Get Food! -> when I'm eating a (safe) food
    """
    if gameState.getAgentState(self.index).numCarrying - successor.getAgentState(self.index).numCarrying == -1:
      # if I certainly get 1 food, add point!
      if successor.getAgentPosition(self.index) == self.targetFood:
        features["Food"] = 2
        features["FoodCarrying"] = 1
      print("Get Food! ", action, features)
      return features

    """
    [Event] : Find Food! -> if above events are not triggered, do this event! (like a general action)
    """
    if gameState.getAgentState(self.index).numCarrying < self.totalFoodNumber - 2:

      features["Food"] = self.getDistanceToTarget(gameState) - self.getDistanceToTarget(successor)
      # if there is no way to target food(BFSMap), use maze distance
      if self.getDistanceToTarget(gameState) > 999:
        features["Food"] = self.getMazeDistance(self.myPosition, self.targetFood) - self.getMazeDistance(
          successor.getAgentPosition(self.index), self.targetFood)

      enemy = self.getEnemy(gameState)
      if features["Capsule"] != 200:
        features["Capsule"] = min(self.getCapsulesDistance(gameState)) - min(self.getCapsulesDistance(successor))
      # if enemies are scared, no need to eat capsules
      if (enemy[0][3]) and (enemy[1][3]):
        features["Capsule"] = 0
      # if there are barriers to get food, capsule,and I can observe an enemy, go home!
      if self.getDistanceToTarget(gameState) >999 and \
        min(self.getCapsulesDistance(gameState)) > 999 and min(self.getEnemyDistance(gameState)) <=2:
        features["Home"] = self.getDistanceToHome(gameState) - self.getDistanceToHome(successor)

      # if enemy and I are all around border! I can block them
      for i in range(len(self.getEnemy(gameState))):
        if (not gameState.getAgentState(self.index).isPacman) and (not enemy[i][0]) and \
          (enemy[i][1] is not None) and (self.getEnemyDistance(gameState)[i]<=3) and (not enemy[i][3]):
          if len(self.food) != 0 :
            self.targetFood = random.choice(self.food)
          features["Food"] = enemy[i][2]*0.1
          features["Capsule"] = 0

      # save teammate, and if this action can not eat a capsule
      if self.isSaveTeammate(gameState) and min(self.getCapsulesDistance(gameState))<9999 \
              and features["Capsule"] != 200:
        # if there is a capsule that I can find, try to get it
        features["Capsule"] = 2*(min(self.getCapsulesDistance(gameState)) - min(self.getCapsulesDistance(successor)))
        # if I actually got it
        if len(self.getCapsules(gameState))-len(self.getCapsules(successor)) == 1:
          features["Capsule"] = 200

      print("Find Food! ", action, features)
      return features

    return features


  #################
  # help function #
  #################

  # When to go home (to the border)?
  def isGoHome(self, gameState):
    # 1. if food left <= 2 which means we can end game, then go home and stop eating
    if self.foodLeft <= 2:
      if gameState.getAgentState(self.index).numCarrying == 0:
        self.isDefense = True
      return True
    # 2. if food left 3~5 , if teammate is more closer to food, I can go home
    if self.foodLeft >2 and self.foodLeft <=5:
      teammateMap = self.BFSMap(gameState, gameState.getAgentPosition((self.index + 2) % 4))
      teammateFoodList = []
      for food in self.food:
        if food in teammateMap:
          teammateFoodList.append(teammateMap[food])
      if len(teammateFoodList) > 0 and min(self.getDistanceOfFoods(gameState)) > max(teammateFoodList):
        return True
    # 3. if I carry much food, and my target food is far away to me, I can go home
    if gameState.getAgentState(self.index).numCarrying > 10 and \
      self.getMazeDistance(gameState.getAgentPosition(self.index), self.targetFood) > 20:
      return True
    # 4. if in the end game, go home and defense
    if self.cost >= 250 and gameState.getAgentState(self.index).numCarrying > 0:
      return True
    # 5. if no way to target food (enemy there?!), go home and reset target
    if self.targetFood in self.myStepTo and self.myStepTo[self.targetFood] > 999 and \
            (min(self.getDistanceOfFoods(gameState)) < 999):
      if len(self.food) != 0:
        self.targetFood = random.choice(self.getFood(gameState).asList())
      return True
    return False


  # set up initial target, which make 2 agents have different target - highest one and lowest one (Y-axis)
  def initalTarget(self, gameState):
    x, y = self.targetFood
    for food in self.food:
      x_food, y_food = food
      if gameState.isOnRedTeam(self.index) and (self.index == 0):
        if y_food < y:
          y = y_food
          self.targetFood = (x_food, y_food)
      elif (gameState.isOnRedTeam(self.index) and (self.index >= 2)):
        if y_food > y:
          y = y_food
          self.targetFood = (x_food, y_food)
      elif (self.index >=2):
        if y_food > y:
          y = y_food
          self.targetFood = (x_food, y_food)
      else:
        if y_food < y:
          y = y_food
          self.targetFood = (x_food, y_food)

  # return a list of enemy includes (isPacman, position, distance, isScared)
  def getEnemy(self, gameState):
    myPosition = gameState.getAgentPosition(self.index)
    enemy = self.getOpponents(gameState)
    enemyState = []
    for e in enemy:
      enemyPosition = gameState.getAgentPosition(e)
      isEnemyScared = gameState.getAgentState(e).scaredTimer > 0
      if enemyPosition == None:
        enemyDistance = gameState.getAgentDistances()[e]
        enemyState.append((gameState.getAgentState(e).isPacman, enemyPosition, enemyDistance, isEnemyScared))
      else:
        enemyDistance = self.getMazeDistance(enemyPosition, myPosition)
        enemyState.append((gameState.getAgentState(e).isPacman, enemyPosition, enemyDistance, isEnemyScared))
    return enemyState

  # change target food based on the lowest distance to foods (heuristic search)
  def changeNearestFood(self, gameState):
    distanceOfFoods = self.getDistanceOfFoods(gameState)
    foodList = self.getFood(gameState).asList()
    if len(foodList) > 1:
      self.targetFood = foodList[distanceOfFoods.index(min(distanceOfFoods))]
    if len(foodList) != 0:
      self.targetFood = foodList[0]

  # return a list of all foods distance based on Map,
  # if not in map which means enemy is 1 distance away there
  def getDistanceOfFoods(self, gameState):
    foodList = self.getFood(gameState).asList()
    foodDistance = []
    for food in foodList:
      if food in self.myStepTo:
        foodDistance.append(self.myStepTo[food])
      else:
        foodDistance.append(9999)
    return foodDistance

  # avoid to choose a target food too close to my teammate's
  def changeTargetAwayToTeammate(self, gameState):
    foodList = self.getFood(gameState).asList()
    if self.targetFood in foodList:
      for food in foodList:
        if self.getMazeDistance(food, targetFood)<=10:
          foodList.remove(food)
    if len(foodList) >0:
      self.targetFood = random.choice(foodList)

  # get successor from an action,
  # if there is a very close enemy, treat its surroundings as walls
  def getSuccessor(self, gameState, action):
    for isPacman,position,distance,isScared in self.getEnemy(gameState):
      if (not isPacman) and (position is not None) and distance<10 and (not isScared):
        x,y = position
        gameState.data.layout.walls[x][y] = True
        gameState.data.layout.walls[x+1][y] = True
        gameState.data.layout.walls[x-1][y] = True
        gameState.data.layout.walls[x][y+1] = True
        gameState.data.layout.walls[x][y-1] = True
    successor = gameState.generateSuccessor(self.index, action)
    return successor

  # calculate the "step" distance to my current position, using BFSMap algorithm
  def stepToMe(self, gameState):
    myPosition = gameState.getAgentPosition(self.index)
    return self.BFSMap(gameState, myPosition)

  # BFS algorithm, uses to scan the map and calculates the "step" distance for each node
  # (not including walls, and the surrounding of enemy)
  # (when distance == 9999, it means no way to that node)
  def BFSMap(self, gameState, position):
    myPosition = position
    validNodes = gameState.data.layout.walls.asList(False)
    step = {}
    closed = {}
    for node in validNodes:
      step[node] = 9999
    queue = util.PriorityQueue()
    queue.push(myPosition, 0)
    step[myPosition] = 0
    while (not queue.isEmpty()):
      node = queue.pop()
      if node in closed:
        continue
      closed[node] = True
      nodeStep = step[node]
      adjacentList = []
      x, y = node
      if not (gameState.data.layout.isWall((x + 1, y))):
        adjacentList.append((x + 1, y))
      if not (gameState.data.layout.isWall((x - 1, y))):
        adjacentList.append((x - 1, y))
      if not (gameState.data.layout.isWall((x, y + 1))):
        adjacentList.append((x, y + 1))
      if not (gameState.data.layout.isWall((x, y - 1))):
        adjacentList.append((x, y - 1))
      for adjNode in adjacentList:
        if not adjNode in step:
          continue
        old = step[adjNode]
        new = nodeStep + 1
        if new < old:
          step[adjNode] = new
          queue.push(adjNode, new)

    return step

  # produce a safe list of food
  def initialSafeFoodList(self, gameState):
    safeFoodList = []
    for x,y in self.food:
      initalState = gameState.deepCopy()
      initalState.data.layout.walls[x][y] = True
      BFSMap = self.BFSMap(initalState,self.start)
      count = 0
      if (x, y + 1) in BFSMap and BFSMap[(x, y + 1)] == 9999:
        count += 1
      if (x, y - 1) in BFSMap and BFSMap[(x, y - 1)] == 9999:
        count += 1
      if (x - 1, y) in BFSMap and BFSMap[(x - 1, y)] == 9999:
        count += 1
      if (x + 1, y) in BFSMap and BFSMap[(x + 1, y)] == 9999:
        count += 1
      if count < 3:
        safeFoodList.append((x,y))
    return safeFoodList

  # return true if I have to save my teammate
  def isSaveTeammate(self, gameState):
    # if teammate's target food is safe and 20 distance away to capsules, no need to save her
    if targetFood in self.safeFoddList and min(self.getCapsulesDistance(gameState)) >= 20:
      return False
    for enemy in self.getEnemy(gameState):
      if (not enemy[0]) and (not enemy[1] is None) and (not enemy[3]) \
        and self.getMazeDistance(enemy[1], gameState.getAgentPosition((self.index+2)%4)) < 5:
        return True
    return False

  # return a list of my position to capsules
  def getCapsulesDistance(self, gameState):
    capsulesList = self.getCapsules(gameState)
    myStepTo = self.stepToMe(gameState)
    if capsulesList != []:
      capsulesDistance = []
      for cap in capsulesList:
        if cap in myStepTo:
          capsulesDistance.append(myStepTo[cap])
        else:
          capsulesDistance.append(9999)
    else:
      capsulesDistance = [9999]
    return capsulesDistance

  # return a list of my position to enemies
  def getEnemyDistance(self, gameState):
    enemys = self.getOpponents(gameState)
    enemyDistance = []
    for enemy in enemys:
      if gameState.getAgentPosition(enemy) == None:
        enemyDistance.append(9999)
      else:
        enemyDistance.append(self.getMazeDistance(gameState.getAgentPosition(self.index),
                                                  gameState.getAgentPosition(enemy)))
    return enemyDistance

  # return true, if the successor crosses the border to home and get score!
  def backToScore(self, gamestate, successor):
    # if successor is alive (which means not in the initial position)
    if successor.getAgentPosition(self.index) != successor.getInitialAgentPosition(self.index):
      if (gamestate.getAgentState(self.index).numCarrying -
        successor.getAgentState(self.index).numCarrying) > 1:
        return True
      if self.foodLeft <=2 and gamestate.getAgentState(self.index).numCarrying - successor.getAgentState(
            self.index).numCarrying == 1:
        return True
    return False

  # calculate the distance to my target, and return (9999 means there is a barrier)
  def getDistanceToTarget(self, gameState):
    myPosition = gameState.getAgentPosition(self.index)
    # if not safe
    if not (self.targetFood in self.getFood(gameState).asList()):
      return 0
    # if I'm not reborn in start position
    if myPosition == self.myPosition:
      if self.targetFood in self.myStepTo:
        distance = self.myStepTo[self.targetFood]
      else:
        distance = 9999
    # I died
    else:
      # recalculate my map
      myStepTo = self.stepToMe(gameState)
      if self.targetFood in myStepTo:
        distance = myStepTo[self.targetFood]
      else:
        distance = 9999
    return distance

  # compute distance to home
  def getDistanceToHome(self, gameState):
    currentPosition = gameState.getAgentPosition(self.index)
    if (currentPosition == self.myPosition):
      distance = self.myStepTo[self.start]
    else:
      distance = self.stepToMe(gameState)[self.start]
    return distance

  # select an action based on the Q score it gets
  def selectAction(self, gameState):
    if gameState.getLegalActions(self.index) is not None:
      actions = gameState.getLegalActions(self.index)
    else:
      actions = ["Stop"]
    qScoreList = []
    for action in actions:
      score = self.getFeatures(gameState, action) * self.weights
      qScoreList.append(score)
    print(qScoreList)
    if len(qScoreList) == 0:
      action = "Stop"
    else:
      if max(qScoreList) == 0:
        action = "Stop"
      else:
        myActions = []
        for i in range(len(qScoreList)):
          if qScoreList[i] == max(qScoreList):
            myActions.append(actions[i])
        action = random.choice(myActions)
    return action

  # Update weight
  # Q(s,a) = (1- alpha) * Q(s,a) + alpha * (reward + estimated future value)
  # w(i) = w(i) + alpha((reward + discount*value(nextState)) - Q(s,a)) * f(i)(s,a)
  # def updateWeights(self, gameState, action):
  #   if gameState.getLegalActions(self.index) is not None:
  #     if len(gameState.getLegalActions(self.index)) != 0:
  #       successor = self.getSuccessor(gameState, action)
  #       if not(successor.data._win) :
  #         # update
  #         # learningValue = abs(10*self.getScore(successor))
  #         # update
  #         actions = successor.getLegalActions(self.index)
  #         futureValue = [self.getFeatures(successor, action) * self.weights for action in actions]
  #         learningValue = 0.01 * (0 + 0.8*max(futureValue) - self.getFeatures(gameState,action)*self.weights)
  #       else:
  #         learningValue = 0
  #       self.weightsCopy = util.Counter()
  #       for key, value in self.weights.items():
  #         updatedValue = value + learningValue * self.getFeatures(gameState, action).get(key)
  #         self.weightsCopy[key] = updatedValue
  #
  #       file = open("weightUpdating.txt", "w+")
  #       for key, value in self.weightsCopy.items():
  #         line = key + ": "+str(self.weightsCopy[key])+"\n"
  #         file.write(line)
  #       print("Update weights")
  #       file.close()


