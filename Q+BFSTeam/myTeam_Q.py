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
import random, time, util

from distanceCalculator import Distancer
from game import Directions
import game

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed, first='myAgent', second='myAgent'):
  return [eval(first)(firstIndex), eval(second)(secondIndex)]


targetFood = None
teamDefence = False


##########
# Agents #
##########


class myAgent(CaptureAgent):

  def registerInitialState(self, gameState):
    print(gameState)
    print("Don't spy on me123")

    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

    self.setup()
    self.cost = 1
    self.food = self.getFood(gameState).asList()
    self.totalFoodNumber = len(self.food)
    self.foodLeft = self.totalFoodNumber
    self.targetFood = self.getFood(gameState).asList()[0]
    self.carry = gameState.getAgentState(self.index).numCarrying
    self.setUpTarget(gameState)
    self.defence = False
    self.myPosition = gameState.getAgentPosition(self.index)
    self.myDistance = self.computeDistances(gameState)
    self.safeFood = self.initialSafeFood(gameState)
    self.defenceTarget = self.start
    enermy = self.getOpponents(gameState)
    self.e1Home = gameState.getInitialAgentPosition(enermy[0])
    self.e2Home = gameState.getInitialAgentPosition(enermy[1])

    global targetFood
    global teamDefence
    targetFood = self.start
    teamDefence = self.defence
    print("initial SafeFoodList", self.safeFood)
    print("initial target", self.targetFood)
  '''
  Your initialization code goes here, if you need any.
  '''

  # set up target  make 2 agent have different target highest one and lowest one (Y-axis)
  def setUpTarget(self, gameState):
    a, b = self.targetFood
    for foodX, foodY in self.food:
      if self.index >= 2 and gameState.isOnRedTeam(self.index):
        if foodY < b:
          b = foodY
          self.targetFood = (foodX, foodY)
      elif gameState.isOnRedTeam(self.index):
        if foodY > b:
          b = foodY
          self.targetFood = (foodX, foodY)
      elif self.index >= 2:
        if foodY <= b:
          b = foodY
          self.targetFood = (foodX, foodY)
      else:
        if foodY >= b:
          b = foodY
          self.targetFood = (foodX, foodY)

  # change to the nearest food to me
  def changeNearestTarget(self, gameState):
    dis = self.getAllFoodDistance(gameState)
    foodList = self.getFood(gameState).asList()
    if len(foodList) > 1:
      self.targetFood = foodList[dis.index(min(dis))]
    if len(foodList) != 0:
      self.targetFood = foodList[0]

  # if teammate target food is within square 5 of mine, I change to another target group
  def changeTargetGroup(self, gameState):
    foodList = self.getFood(gameState).asList()
    if self.targetFood in foodList:
      for food in foodList:
        if self.getMazeDistance(self.targetFood, targetFood) <= 10:
          foodList.remove(food)
    if len(foodList) > 0:
      self.targetFood = random.choice(foodList)

  def getSuccessor(self, gameState, action):
    """
	Finds the next successor which is a grid position (location tuple).
	"""
    for ispacman, position, distance, scared in self.getEnermy(gameState):
      if (position is not None) and (not ispacman) and distance < 10 and not scared:
        x, y = position
        gameState.data.layout.walls[x][y] = True
        gameState.data.layout.walls[x + 1][y] = True
        gameState.data.layout.walls[x][y + 1] = True
        gameState.data.layout.walls[x][y - 1] = True
        gameState.data.layout.walls[x - 1][y] = True

    successor = gameState.generateSuccessor(self.index, action)

    pos = successor.getAgentState(self.index).getPosition()
    if pos != util.nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def chooseAction(self, gameState):
    global targetFood
    time1 = time.time()

    if not self.getEnermy(gameState)[0][0] and self.getEnermy(gameState)[1][0]:
      self.defence = False

    for ispacman, position, distance, scared in self.getEnermy(gameState):
      if (position is not None) and (not ispacman) and not scared:
        x, y = position
        gameState.data.layout.walls[x][y] = True
        gameState.data.layout.walls[x + 1][y] = True
        gameState.data.layout.walls[x][y + 1] = True
        gameState.data.layout.walls[x][y - 1] = True
        gameState.data.layout.walls[x - 1][y] = True

    self.cost += 1
    self.food = self.getFood(gameState).asList()
    self.foodLeft = len(self.food)
    self.carry = gameState.getAgentState(self.index).numCarrying
    self.myDistance = self.computeDistances(gameState)
    self.myPosition = gameState.getAgentPosition(self.index)

    # defense / you are not pacman
    if self.defence and not gameState.getAgentState(self.index).isPacman:
      # self.getCapsulesYouAreDefending(gameState) return [(x,y)]
      # still have capsules in our territory, change to defense that Capsules
      if len(self.getCapsulesYouAreDefending(gameState)) > 0 and self.defenceTarget == self.start:
        self.defenceTarget = self.getCapsulesYouAreDefending(gameState)[0]

    # if not the first move, we have previous state
    if self.getPreviousObservation() is not None:
      # target food miss?
      if self.targetFood not in self.food or self.getPreviousObservation().getAgentState(
              self.index).numCarrying < self.carry:
        self.changeNearestTarget(gameState)
        print("food disappear, change to nearest food")
      # capsules miss?
      if len(self.getCapsules(gameState)) - len(self.getCapsules(self.getPreviousObservation())) == -1:
        self.changeNearestTarget(gameState)
        print("capsule disappear, change to nearest food")
      # previous is not pacman and now is pacman
      if (not self.getPreviousObservation().getAgentState(self.index).isPacman) and gameState.getAgentState(
              self.index).isPacman:
        self.changeNearestTarget(gameState)
      # detect that if your food is eaten?
      dfood = self.getFoodYouAreDefending(gameState).asList()
      dpfood = self.getFoodYouAreDefending(self.getPreviousObservation()).asList()
      if len(dfood) - len(dpfood) == -1:
        for food in dpfood:
          if food not in dfood:
            # find the food that is eaten by enemy
            self.defenceTarget = food
            break
        print("your food being eaten", self.defenceTarget)

    # if teammate target food is within square 5 of mine, I change to another target group
    if self.getMazeDistance(targetFood, self.targetFood) <= 10 \
            and self.getMazeDistance(self.myPosition, self.targetFood) >= self.getMazeDistance(
      gameState.getAgentPosition((self.index + 2) % 4), self.targetFood):
      self.changeTargetGroup(gameState)
      print("same target, change to another group")

    # food left = 3,4,5
    if self.foodLeft > 2 and self.foodLeft <= 5:
      # if I am not carrying food , and my teammate is pacman, I go home defense
      if gameState.getAgentState(self.index).numCarrying == 0 and gameState.getAgentState(
              (self.index + 2) % 4).isPacman:
        self.defence = True
      else:
        self.defence = False

    distance_to_target = self.getTargetFoodDistance(gameState)

    print("Agent", self.index)
    print("cost", self.cost)
    print("target food", self.targetFood)
    print("food distance", distance_to_target)
    print("home distance", self.myDistance)
    print("enemy", self.getEnermy(gameState))
    print("carry", self.carry)
    print("position", gameState.getAgentPosition(self.index))

    # print(gameState)
    action = self.choose_action(gameState)
    targetFood = self.targetFood

    time2 = time.time()
    print("calculateTime", time2 - time1)
    print("-------------------------------------------------")
    return action

  def getHomeDistance(self, gameState):
    current_position = gameState.getAgentPosition(self.index)
    if current_position[0] == self.myPosition[0] and current_position[1] == self.myPosition[1]:
      home_distance = self.myDistance[self.start]
    else:
      home_distance = self.computeDistances(gameState)[self.start]
    return home_distance + 1

  def getHome(self, gameState):
    current_position = gameState.getAgentPosition(self.index)
    return self.getMazeDistance(current_position, self.start) + 1

  # return target food distance
  def getTargetFoodDistance(self, gameState):
    current_position = gameState.getAgentPosition(self.index)
    if self.targetFood not in self.getFood(gameState).asList():
      return 0
    # food_distance = self.getMazeDistance(self.targetFood, current_position)
    if current_position[0] == self.myPosition[0] and current_position[1] == self.myPosition[1]:
      if self.targetFood in self.myDistance:
        food_distance = self.myDistance[self.targetFood]
      else:
        food_distance = 99999
    else:
      myDistance = self.computeDistances(gameState)
      if self.targetFood in myDistance:
        food_distance = myDistance[self.targetFood]
      else:
        food_distance = 99999
    return food_distance

  # get a list of food distance to me
  def getAllFoodDistance(self, gameState):
    food_list = self.getFood(gameState).asList()
    food_distance = []
    for x, y in food_list:
      food = tuple((x, y))
      if food in self.myDistance:
        food_distance.append(self.myDistance[food])
      else:
        food_distance.append(99999)

    return food_distance

  def getCapsuleDistance(self, gameState, a=0):
    my_position = gameState.getAgentPosition(self.index)
    ca_list = self.getCapsules(gameState)

    if a != 1 and my_position[0] == self.myPosition[0] and my_position[1] == self.myPosition[1] or len(
            self.getCapsules(gameState)) == 0:
      myDistance = self.myDistance
    else:
      myDistance = self.computeDistances(gameState)

    if ca_list != []:
      ca_distance = []
      for x, y in ca_list:
        ca = tuple((x, y))
        if ca in myDistance:
          ca_distance.append(myDistance[ca])
        else:
          ca_distance.append(99999)
    else:
      ca_distance = [99999]
    return ca_distance

  def getEnermy(self, gameState):
    # pacman, position, distance, scared
    my_position = gameState.getAgentPosition(self.index)
    enermy = self.getOpponents(gameState)
    enermyState = []
    for e in enermy:
      enermy_position = gameState.getAgentPosition(e)
      enermy_scared = gameState.getAgentState(e).scaredTimer > 0
      if enermy_position == None:
        enermy_distance = gameState.getAgentDistances()[e]
        enermyState.append((gameState.getAgentState(e).isPacman, enermy_position, enermy_distance, enermy_scared))
      else:
        enermy_distance = self.getMazeDistance(enermy_position, my_position)
        enermyState.append((gameState.getAgentState(e).isPacman, enermy_position, enermy_distance, enermy_scared))
    return enermyState

  def getEnermyDistanceToMe(self, gameState):
    my_position = gameState.getAgentPosition(self.index)
    enermy = self.getOpponents(gameState)
    enermyDistance = []
    for e in enermy:
      enermy_position = gameState.getAgentPosition(e)
      if enermy_position == None:
        enermy_distance = 99999
        enermyDistance.append(enermy_distance)
      else:
        enermy_distance = self.getMazeDistance(enermy_position, my_position)
        enermyDistance.append(enermy_distance)
    return enermyDistance

  def getTeamateDistance(self, gameState):
    my_position = gameState.getAgentPosition(self.index)
    teamMate = gameState.getAgentPosition((self.index + 2) % 4)
    return self.getMazeDistance(my_position, teamMate)

  def foodSafe(self):
    return self.targetFood in self.safeFood

  def initialSafeFood(self, gameState):
    safeFood = []
    for food in self.food:
      x, y = food
      myState = gameState.deepCopy()
      myState.data.layout.walls[x][y] = True
      safeMap = self.bfs(myState, self.start)
      count = []
      if (x, y + 1) in safeMap and safeMap[(x, y + 1)] < 10000:
        count.append("a")
      if (x + 1, y) in safeMap and safeMap[(x + 1, y)] < 10000:
        count.append("b")
      if (x - 1, y) in safeMap and safeMap[(x - 1, y)] < 10000:
        count.append("c")
      if (x, y - 1) in safeMap and safeMap[(x, y - 1)] < 10000:
        count.append("d")
      if ("a" in count and "d" in count) or ("b" in count and "c" in count):
        safeFood.append(food)
    return safeFood

  def bfs(self, gameState, position):
    pos1 = position
    allNodes = gameState.data.layout.walls.asList(False)

    dist = {}
    closed = {}
    for node in allNodes:
      dist[node] = 99999
    import util
    queue = util.PriorityQueue()
    queue.push(pos1, 0)
    dist[pos1] = 0
    while not queue.isEmpty():
      node = queue.pop()
      if node in closed:
        continue
      closed[node] = True
      nodeDist = dist[node]
      adjacent = []
      x, y = node
      if not gameState.data.layout.isWall((x, y + 1)):
        adjacent.append((x, y + 1))
      if not gameState.data.layout.isWall((x, y - 1)):
        adjacent.append((x, y - 1))
      if not gameState.data.layout.isWall((x + 1, y)):
        adjacent.append((x + 1, y))
      if not gameState.data.layout.isWall((x - 1, y)):
        adjacent.append((x - 1, y))
      for other in adjacent:
        if not other in dist:
          continue
        oldDist = dist[other]
        newDist = nodeDist + 1
        if newDist < oldDist:
          dist[other] = newDist
          queue.push(other, newDist)
    return dist

  def computeDistances(self, gameState):
    # print("跑了一次")
    pos1 = gameState.getAgentPosition(self.index)
    return self.bfs(gameState, pos1)

  def getFeatures(self, gameState, action):
    # print("start get features")
    successor = self.getSuccessor(gameState, action)

    features = {"food": 0,
                "foodCarry": 0,
                "distanceHome": 0,
                "capsule": 0,
                "ghostMin": 0,
                "ghostMax": 0,
                "ways": 0,
                "friend": 0,
                "b": 1,
                "defenceTarget": 0
                }

    e1, e2 = self.getEnermy(gameState)
    successor_pos = successor.getAgentPosition(self.index)
    # if enemy distance to me increase (>1) good thing?!
    if self.getEnermy(successor)[0][2] - e1[2] > 1 and successor_pos[0] != self.start[0] and successor_pos[1] != \
            self.start[1]:
      features["ghostMin"] = -1000
      return util.Counter(features)
    if self.getEnermy(successor)[1][2] - e2[2] > 1 and successor_pos[0] != self.start[0] and successor_pos[1] != \
            self.start[1]:
      features["ghostMax"] = -1000
      return util.Counter(features)

    # teammate is close to me, (+) close to my teammate (-) away from my teammate
    if self.getTeamateDistance(successor) <= 5:
      features["friend"] = self.getTeamateDistance(gameState) - self.getTeamateDistance(successor)
    # get a capsule   and if enemy is not scared   (+2000)
    if len(self.getCapsules(gameState)) - len(self.getCapsules(successor)) == 1:
      if (not self.getEnermy(gameState)[0][3]) or (not self.getEnermy(gameState)[1][3]):
        features["capsule"] = 2000

    # chase pacman
    # e1 is pacman and e1 position is not none, e1 dist to me <3 and I'm not pacman not scared
    # and capsules == 0
    # OR e1 is pacman and I'm defense and I'm ghost
    if (e1[0] and e1[1] is not None
        and self.getEnermyDistanceToMe(gameState)[0] < 3 and (not gameState.getAgentState(self.index).isPacman)
        and gameState.getAgentState(self.index).scaredTimer == 0 and (not e1[3]) and len(
              self.getCapsulesYouAreDefending(gameState)) == 0) \
            or (e1[0] and self.defence and (not gameState.getAgentState(self.index).isPacman)):
      # distance between current enemy and succ enemy
      features["ghostMin"] = self.getEnermy(successor)[0][2] - e1[2]
      # save my teammate
      if self.saveFriend(gameState) and min(self.getCapsuleDistance(gameState)) < 10000:
        features["ghostMin"] = 0
        features["defenceTarget"] = 0
      # defense target (+) when the distance is close
      elif self.defence:
        features["defenceTarget"] = self.getMazeDistance(self.myPosition, self.defenceTarget) - self.getMazeDistance(
          successor.getAgentPosition(self.index), self.defenceTarget)
      # successor distance to enemy is larger than current state (away from enemy) and not save friend
      if features["ghostMin"] > 1:
        features["ghostMin"] = -1000
      # if I'm scared. stay away to enemy
      if not gameState.getAgentState(self.index).scaredTimer == 0:
        features["ghostMin"] = - features["ghostMin"]
        features["defenceTarget"] = 0
      # ??!!
      if self.defence == True:
        features["b"] = 0

      # if enemy distance to me >=2 and enemy can be observed (within 5 distance)
      if self.getEnermyDistanceToMe(gameState)[0] >= 2 and e1[1] is not None:
        myX, myY = self.myPosition
        gs = gameState.deepCopy()
        gs.data.layout.walls[myX][myY] = True
        gs.data.layout.walls[myX + 1][myY] = True
        gs.data.layout.walls[myX - 1][myY] = True
        gs.data.layout.walls[myX][myY + 1] = True
        gs.data.layout.walls[myX][myY - 1] = True
        # if I can be the barrier on the path that enemy go back
        if self.bfs(gameState, e1[1])[self.e1Home] > 10000:
          features["ghostMin"] = 0
          features["defenceTarget"] = 0
      print("chaseA", action, features)
      return util.Counter(features)
    if (e2[0] and e2[1] is not None
        and self.getEnermyDistanceToMe(gameState)[1] < 3 and (not gameState.getAgentState(self.index).isPacman)
        and gameState.getAgentState(self.index).scaredTimer == 0 and (not e2[3]) and len(
              self.getCapsulesYouAreDefending(gameState)) == 0) \
            or (e2[0] and self.defence and (not gameState.getAgentState(self.index).isPacman)):
      features["ghostMax"] = self.getEnermy(successor)[1][2] - e2[2]
      if (features["ghostMin"] != 0 and self.getEnermyDistanceToMe(gameState)[0] <
          self.getEnermyDistanceToMe(gameState)[1]) or features["ghostMin"] == -1000:
        features["ghostMax"] = 0
      if self.saveFriend(gameState) and min(self.getCapsuleDistance(gameState)) < 10000:
        features["ghostMax"] = 0
        features["ghostMin"] = 0
        features["defenceTarget"] = 0
      if self.defence:
        features["defenceTarget"] = self.getMazeDistance(self.myPosition, self.defenceTarget) - self.getMazeDistance(
          successor.getAgentPosition(self.index), self.defenceTarget)
      if features["ghostMax"] > 1:
        features["ghostMax"] = -1000
      if not gameState.getAgentState(self.index).scaredTimer == 0:
        features["ghostMax"] = - features["ghostMax"]
        features["defenceTarget"] = 0
      if self.defence == True:
        features["b"] = 0
      if self.getEnermyDistanceToMe(gameState)[1] >= 2 and e2[1] is not None:
        myX, myY = self.myPosition
        gs = gameState.deepCopy()
        gs.data.layout.walls[myX][myY] = True
        gs.data.layout.walls[myX + 1][myY] = True
        gs.data.layout.walls[myX - 1][myY] = True
        gs.data.layout.walls[myX][myY + 1] = True
        gs.data.layout.walls[myX][myY - 1] = True
        if self.bfs(gameState, e2[1])[self.e2Home] > 10000:
          features["ghostMax"] = 0
          features["defenceTarget"] = 0
      print("chaseB", action, features)
      return util.Counter(features)

    # go back to Score
    if self.goBackScore(gameState, successor):
      features["foodCarry"] = abs(
        successor.getAgentState(self.index).numCarrying - gameState.getAgentState(self.index).numCarrying) * 10000
      features["distanceHome"] = self.getHomeDistance(gameState) - self.getHomeDistance(successor)
      print("goBackScore", action, features)
      return util.Counter(features)

    # Escape
    # when target food is not safe OR target food is safe, teammate is pacman
    # OR no way home, no capsules
    # OR a capsule
    if not self.foodSafe() or (self.foodSafe() and gameState.getAgentState((self.index + 2) % 4).isPacman) \
            or (self.myDistance[self.start] > 10000 and min(self.getCapsuleDistance(gameState)) > 10000) or min(
      self.getCapsuleDistance(gameState)) < 10000:

      # enemy1 5 distance close to me, and I'm pacman and enemy1 is not scared and is ghost
      # OR enemy2 5 distance close to me, and I'm pacman and enemy1 is not scared and is ghost
      # OR no way home and no way to capsules
      if (self.getEnermyDistanceToMe(gameState)[0] < 5 and gameState.getAgentState(self.index).isPacman and (
      not self.getEnermy(gameState)[0][3]) and (not self.getEnermy(gameState)[0][0])) \
              or (self.getEnermyDistanceToMe(gameState)[1] < 5 and gameState.getAgentState(self.index).isPacman and (
      not self.getEnermy(gameState)[1][3]) and (not self.getEnermy(gameState)[1][0])) \
              or (self.myDistance[self.start] > 10000 and min(self.getCapsuleDistance(gameState)) > 10000):

        # still have food, find a random food
        if len(self.food) != 0:
          self.targetFood = random.choice(self.getFood(gameState).asList())
          print("find safe food while escape")
        # if food left <=2, and there is a way home
        # OR capsules == 0
        # OR there are some barrier to capsules
        if (self.foodLeft <= 2 and self.getHomeDistance(gameState) < 10000) or len(
                self.getCapsules(gameState)) == 0 or min(self.getCapsuleDistance(gameState)) > 10000:
          features["friend"] = self.getTeamateDistance(gameState) - self.getTeamateDistance(successor)
          features["ways"] = len(successor.getLegalActions(self.index)) - len(gameState.getLegalActions(self.index))
          # home path is available
          if self.getHomeDistance(gameState) < 10000:
            features["distanceHome"] = self.getHomeDistance(gameState) - self.getHomeDistance(successor)
          # home path is not available, there are some barrier
          else:
            print("no way home, try your skills, be Messi")
            features["distanceHome"] = self.getHome(gameState) - self.getHome(successor)
            features["ways"] = 0
          print("escapeForHome", action, features)
          print("distanceToHome", self.getHomeDistance(gameState))
        else:
          # if this action not eat a capsule
          if features["capsule"] != 2000:
            features["capsule"] = min(self.getCapsuleDistance(gameState)) - min(self.getCapsuleDistance(successor))
          print("escapeForCap", action, features)
        return util.Counter(features)

    # go back
    if self.goBack(gameState, successor):
      # if we all pacman or we all ghost
      if gameState.getAgentState(self.index).isPacman == gameState.getAgentState((self.index + 2) % 4).isPacman:
        features["friend"] = self.getTeamateDistance(gameState) - self.getTeamateDistance(successor)
      features["distanceHome"] = self.getHomeDistance(gameState) - self.getHomeDistance(successor)

      # save teammate, and it is pacman
      if self.saveFriend(gameState) and gameState.getAgentState((self.index + 2) % 4).isPacman:
        # still have capsules, I'm more than 3 distance away to teammate
        if len(self.getCapsules(gameState)) != 0 and 3 <= self.getTeamateDistance(gameState):
          # treat teammate as enemy (walls = True)  , and ??!!
          myX, myY = gameState.getAgentPosition((self.index + 2) % 4)
          gs = gameState.deepCopy()
          gs.data.layout.walls[myX][myY] = True
          gs.data.layout.walls[myX + 1][myY] = True
          gs.data.layout.walls[myX - 1][myY] = True
          gs.data.layout.walls[myX][myY + 1] = True
          gs.data.layout.walls[myX][myY - 1] = True
          su = self.getSuccessor(gs, action)
          #??!!
          features["capsule"] = min(self.getCapsuleDistance(gs, 1)) - min(self.getCapsuleDistance(su))
          features["distanceHome"] = 0
          if features["capsule"] < -1:
            features["capsule"] = 2000
        print("HeadingForCap")

      # no way home
      if self.getHomeDistance(gameState) > 10000:
        features["distanceHome"] = self.getHome(gameState) - self.getHome(successor)

      # I'm ghost
      if not gameState.getAgentState(self.index).isPacman:
        features["distanceHome"] = 0
        features["b"] = 0
        features["friend"] = 0
        print("finish and stay for defend")

      print("goBack", action, features)
      return util.Counter(features)

    if successor.getAgentState(self.index).numCarrying - gameState.getAgentState(self.index).numCarrying == 1:
      # eating food
      pos = successor.getAgentPosition(self.index)
      # eat 1 food
      if pos[0] == self.targetFood[0] and pos[1] == self.targetFood[1]:
        features["food"] = 2
        features["foodCarry"] = 1
      # ??!!
      elif (e1[2] >= 5 or e1[3]) and (e2[2] >= 5 or e2[3]):
        features["food"] = 1
        features["foodCarry"] = 1
      # number of actions between successor and current node
      features["ways"] = len(successor.getLegalActions(self.index)) - len(gameState.getLegalActions(self.index))
      print("eatingFood", action, features)
      return util.Counter(features)

    # go to eat ( like general action?!, if above event is not happened)
    if self.goEat(gameState, successor):
      e1, e2 = self.getEnermy(successor)
      # if this action is not eating a capsule
      if features["capsule"] != 2000:
        features["capsule"] = min(self.getCapsuleDistance(gameState)) - min(self.getCapsuleDistance(successor))
      # if enemies are all scared
      if e1[3] and e2[3]:
        features["capsule"] = 0
      features["food"] = self.getTargetFoodDistance(gameState) - self.getTargetFoodDistance(successor)
      if self.getTargetFoodDistance(gameState) == 99999:
        features["food"] = self.getMazeDistance(self.myPosition, self.targetFood) - self.getMazeDistance(
          successor.getAgentPosition(self.index), self.targetFood)
      # if no way to capsules, no way to target food, enemy is so close to me(<=2)
      if min(self.getCapsuleDistance(gameState)) == 99999 and self.getTargetFoodDistance(gameState) == 99999 and min(
              self.getEnermyDistanceToMe(gameState)) <= 2:
        features["distanceHome"] = self.getHomeDistance(gameState) - self.getHomeDistance(successor)
      # I'm ghost, enemy is close to me (<=3), enemy is not pacman and not scared and not noise observe
      # which means we are around the border!
      if (not gameState.getAgentState(self.index).isPacman) and self.getEnermyDistanceToMe(gameState)[0] <= 3 and (
      not e1[0]) and (not e1[3]) and (e1[1] is not None):
        print("wondering")
        if len(self.food) != 0:
          self.targetFood = random.choice(self.food)
        features["food"] = e1[2] / 10
        features["capsule"] = 0
      if (not gameState.getAgentState(self.index).isPacman) and self.getEnermyDistanceToMe(gameState)[1] <= 3 and e2[
        2] < e1[2] and (not e2[0]) and (not e2[3]) and (e2[1] is not None):
        print("wondering")
        if len(self.food) != 0:
          self.targetFood = random.choice(self.food)
        features["food"] = e2[2] / 10
        features["capsule"] = 0

      # save friend event, and if there is a path to capsules, and this action is not to get cap
      if self.saveFriend(gameState) and min(self.getCapsuleDistance(gameState)) < 10000 and features["capsule"] != 2000:
        print("Save your friend")
        if 3 <= self.getTeamateDistance(gameState):
          myX, myY = gameState.getAgentPosition((self.index + 2) % 4)
          gs = gameState.deepCopy()
          gs.data.layout.walls[myX][myY] = True
          gs.data.layout.walls[myX + 1][myY] = True
          gs.data.layout.walls[myX - 1][myY] = True
          gs.data.layout.walls[myX][myY + 1] = True
          gs.data.layout.walls[myX][myY - 1] = True
          su = self.getSuccessor(gs, action)
          if action != "Stop":
            features["capsule"] = min(self.getCapsuleDistance(gs, 1)) - min(self.getCapsuleDistance(su))
        features["capsule"] = 2 * features["capsule"]
        # redundant?!
        if len(self.getCapsules(gameState)) - len(self.getCapsules(successor)) == 1:
          features["capsule"] = 2000
      print("goEat", action, features, "Safe Eating")
      return util.Counter(features)

    print("what???")
    return util.Counter(features)


  # save my teammate
  def saveFriend(self, gameState):
    e1, e2 = self.getEnermy(gameState)
    # (teammate) targetFood is safe, and 20 more distance away to capsules
    if targetFood in self.safeFood and min(self.getCapsuleDistance(gameState)) >= 20:
      return False
    # e1 is ghost, e1 can be observed, and not scared and distance to teammate < 4
    if (not e1[0]) and e1[1] is not None and self.getMazeDistance(gameState.getAgentPosition((self.index + 2) % 4),
                                                                  e1[1]) < 4 and (not e1[3]):
      return True
    if (not e2[0]) and e2[1] is not None and self.getMazeDistance(gameState.getAgentPosition((self.index + 2) % 4),
                                                                  e2[1]) < 4 and (not e2[3]):
      return True
    return False

  def goEat(self, gameState, successor):
    if gameState.getAgentState(self.index).numCarrying < self.totalFoodNumber - 2:
      return True
    return False
  # go back
  def goBack(self, gameState, successor):
    # food left <= 2
    if self.foodLeft <= 2:
      # if no carrying, turn to defense mode
      if gameState.getAgentState(self.index).numCarrying == 0:
        self.defence = True
      return True

    if 2 < self.foodLeft <= 5:
      # check teammate food distance map
      teamFood = self.bfs(gameState, gameState.getAgentPosition((self.index + 2) % 4))
      dis = []
      for food in self.food:
        if food in teamFood:
          dis.append(teamFood[food])
      # if there is still some food, and teammate is closer to every food
      if len(dis) > 0 and min(self.getAllFoodDistance(gameState)) > max(dis):
        return True
    # if I carry more than 11, 21 distance away from my target, go back
    if (gameState.getAgentState(self.index).numCarrying > 11 and
            self.getMazeDistance(gameState.getAgentPosition(self.index), self.targetFood) > 21):
      return True
    # if I carry more than 1, and cost >=260
    if gameState.getAgentState(self.index).numCarrying >= 1 and self.cost >= 260:
      return True
    # if there is a barrier(enemy) in path to target food, change target food
    if self.targetFood in self.myDistance and self.myDistance[self.targetFood] > 10000 and min(
            self.getAllFoodDistance(gameState)) < 10000:
      if len(self.food) != 0:
        self.targetFood = random.choice(self.getFood(gameState).asList())
      print("no way!,go home, change another target")
      return True
    return False

  # go back to score
  def goBackScore(self, gamestate, successor):
    # if numCarrying will decrease and successor not in inital state
    if gamestate.getAgentState(self.index).numCarrying - successor.getAgentState(self.index).numCarrying > 1 \
            and not successor.getAgentPosition(self.index) == successor.getInitialAgentPosition(self.index):
      return True
    # food left <=2 and  ??!!
    if self.foodLeft <= 2 and gamestate.getAgentState(self.index).numCarrying - successor.getAgentState(
            self.index).numCarrying == 1 \
            and not successor.getAgentPosition(self.index) == successor.getInitialAgentPosition(self.index):
      return True
    return False

  def setup(self, actions=["North", "South", "West", "East", "Stop"], learning_rate=0.01, reward_decay=0.9, e_greedy=1,
            first=True, ):
    self.actions = actions  # a list
    self.lr = learning_rate  # 学习率
    self.gamma = reward_decay  # 奖励衰减
    self.epsilon = e_greedy  # 贪婪度
    self.weights = util.Counter({"food": 93.19970348920681,
                                    "foodCarry": 87.0637492041355,
                                    "distanceHome": 5138.773437266105,
                                    "capsule":  87,
                                    "ghostMin": -100,
                                    "ghostMax": -100,
                                    "ways": 5,
                                    "friend": -3,
                                    "b": 55.172944964376505,
                                    "defenceTarget":50})

  def choose_action(self, gameState):
    if gameState.getLegalActions(self.index) is not None:
      legal_actions = gameState.getLegalActions(self.index)
    else:
      legal_actions = ["Stop"]
    Qvalue = [self.getFeatures(gameState, action) * self.weights for action in legal_actions]
    if len(Qvalue) == 0:
      action = "Stop"
    elif random.uniform(1, 0.5) < self.epsilon and len(Qvalue) != 0:  # 选择 Q value 最高的 action
      if max(Qvalue) == 0:
        action = "Stop"
      else:
        good_action = []
        for i in range(len(legal_actions)):
          if Qvalue[i] == max(Qvalue):
            good_action.append(legal_actions[i])
        if self.foodLeft <= 2:
          if "West" in good_action:
            action = "West"
          elif "East" in good_action:
            action = "East"
          else:
            action = random.choice(good_action)
        else:
          action = random.choice(good_action)
    else:  # 随机选择 action
      action = random.choice(legal_actions)
    print("action:", action)
    return action