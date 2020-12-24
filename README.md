# Pacman Capture the Flag Project Template


 <p align="center"> 
    <img src="img/capture_the_flag.png" alt="logo project 2" width="400">
 </p>
 
Note that the Pacman tournament has different rules as it is a game of two teams, where your Pacmans become ghosts in certain areas of the grid. Please read carefully the rules of the Pacman tournament. Understanding it well and designing a controller for it is part of the expectations for this project. Additional technical information on the contest project can be found in file [CONTEST.md](CONTEST.md). 

## Your task

**Your task** is to develop an autonomous Pacman agent team to play the [Pacman Capture the Flag Contest](http://ai.berkeley.edu/contest.html) by suitably modifying file `myTeam.py` (and maybe some other auxiliarly files you may implement). The code submitted should be internally commented at high standards and be error-free and _never crash_. 

In your solution, you have to use at **least 2 AI-related techniques** (**3 techniques at least for groups of 4**) that have been discussed in the subject or explored by you independently, and you can combine them in any form. **We won't accept a final submission with less than 2/3 techniques**. Some candidate techniques that you may consider are:

1. Blind or Heuristic Search Algorithms (using general or Pacman specific heuristic functions).
2. Classical Planning (PDDL and calling a classical planner).
3. Policy iteration or Value Iteration (Model-Based MDP).
4. Monte Carlo Tree Search or UCT (Model-Free MDP).
5. Reinforcement Learning – classical, approximate or deep Q-learning (Model-Free MDP).
6. Goal Recognition techniques (to infer intentions of opponents).
7. Game Theoretic Methods.

We recommend you to start by using search algorithms, given that you already implemented their code in the first project. You can always use hand coded decision trees to express behaviour specific to Pacman, but they won't count as a required technique. You are allowed to express domain knowledge, but remember that we are interested in "autonomy", and hence using techniques that generalise well. The 7 techniques mentioned above can cope with different rules much easier than any decision tree (if-else rules). If you decide to compute a policy, you can save it into a file and load it at the beginning of the game, as you have 15 seconds before every game to perform any pre-computation. If you want to use classical planning, I recommend reading [these tips](CONTEST.md#pac-man-as-classical-planning-with-pddl).


* * *

# Approximate Q-Function & BFS search Algorithms

# Table of Contents
- [Governing Strategy Tree](#governing-strategy-tree)
  * [Motivation](#motivation)
  * [Application](#Application)
  * [Trade-offs](#trade-offs)     
     - [Advantages](#advantages)
     - [Disadvantages](#disadvantages)
  * [Future improvements](#future-improvements)

## Governing Strategy Tree  

### Motivation 

The key idea of Approximate Q-Function is to approximate the Q-function using a linear combination of features and their weights. Instead of recording everything in detail, we think about what is most important to know, and model that. In terms of Pacman game, using a group of weights makes it possible to apply the algorithm to a larger scale, and it is very efficient to calculate the Q-value for actions attached state as well.

Breadth-First Search algorithm is an algorithm for traversing or searching tree or graph data structures. It starts at the tree root (or some arbitrary node of a graph, sometimes referred to as a search key), and explores all of the neighbour nodes at the present depth prior to moving on to the nodes at the next depth level. In the Pacman game, we try to calculate the steps from every position (except walls) to our current location by producing a BFS map before choosing action. Also, we consider the neighbour positions of observed enemies as walls.


[Back to top](#table-of-contents)

### Application 
### Two Attackers
As the game rules mentioned, a game ends when one team eats all but two of the opponents' dots or reached 1200 move limitation. Our strategy is that if our two agents can work with others to get food efficiently, two attackers might be more helpful than one defender and one attacker. However, it does not mean that our agents have no defense actions, our agents would turn into defense mode after eating most of the food which means the game is very close to ending.

### Target Food Selection
In the initial selection, we try to separate each agent to top and bottom because one of our agents can pester the defensive enemy (generally, there is only one defensive enemy) while another will be free. After crossing the border, our agents will select the closest food as target food. If two targets are within 10 distance, one of our agents will randomly choose another food which is far away from that particular target as a new target. This strategy can guarantee that the attackers will not chase two adjacent targets and be captured by one enemy.

### Safety Food
We classify food into two different groups, safe food and dangerous food. Initially, we treat the food as a wall and see if there are two or more paths that our agents can escape. If yes, that food would be safe food and vice versa.

### Early Go Back
Generally, the distribution of food is not always equal. When the total number of food decreases below a specific threshold, our two attackers strategy becomes unnecessary. One of our agents can go back to our territory and try to capture the enemies. This strategy can improve our winning rate when we are close to the end game because we usually get food faster than the enemies with two attackers strategy and one of our agent can go back earlier to catch the enemies.

### Teammate Salvaged
Sometimes, our teammate is trying to escape away from the enemies but a capsule is far away (or no capsule) or there would be no path to escape in later few steps. In this scenario, another agent could try to get a capsule or distract the attention of the enemies.


### Events Triggers
In this approach, we use six different events to manage which action should be applied in a particular state. We choose features based on different events and calculate the successor's Q-value to decide which action is better to be executed.

- Capture enemy

  Based on Game rules, agents can only observe an opponent's configuration (position and direction) if they or their teammate is within 5 squares (Manhattan distance). This event will be triggered when our agents can observe an opponent's position and he/she is a Pacman.

- Score

  If the successor back to the border and get some score, this event will be triggered.

- Escape

  When our agents try to eat dangerous food and an opponent is within 5 squares, this event will be triggered and our agents will try to escape and find a capsule if there is any or go back home.

- Go home

  Go Home event will be triggered when we are very close to the end game, which means the rest number of food is small or agents moves are close to the game limitation.

- Get food

  If the successor will certainly get a safe food, this event will be switched on.

- Find food

  This event will be executed like a general action when all the above events are not triggered. 

### Features
We selected 8 features to calculate Q-value for each action. **Target food distance**, **Number of food carrying**, **Distance to capsules**, **Distance to teammate**, **Distance to defense target**, **Distance to initial home**, **Bias value**.

In the beginning, we selected the initial weight values of each feature and update weight values by each game. We use Event Trigger strategy as above mentioned to decide how many features points a certain event could get and calculate the successor's Q-value to determine which action should be taken under those specific conditions.

[Back to top](#table-of-contents)

### Trade-offs  
#### *Advantages*  
One of the advantages is efficiency compared with classic Q-Learning approach. In Approximate Q-Function, calculating counter of weights and features is not complicated and it is easy to implement. Another advantage is that the Q-value could be propagated after the previous updating.


#### *Disadvantages*
Two significant drawbacks while using Approximate Q-Function. The first one is that it is hard to converge feature weights that is suitable under all possible conditions. In terms of Pacman problems, if the regular game rules change, our model may not be effective. The second disadvantage is how to choose features because the quality of feature selection would have a major impact on the performance.


[Back to top](#table-of-contents)

### Future improvements  
To settle all the above problems, we could try to focus on some decision tree methods to classify the problems under different conditions and to consider about more complex events that could happen based on the game rules. 


[Back to top](#table-of-contents)