---
layout: default
title:  Status
---
Food Delivery Service Project

Project summary
Our project aims to find a path that minimizes the time travel to a randomized destination. Our training environment is a 20 * 20 grid map. Each grid is a 4 * 4 hollow squares, whose edges consist of different kinds of blocks,such as Stone, Ice, and Soul Sand, to give agents different speed properties in the different paths. We train our client by machine learning algorithm to reach our goal.
Approach
We use the q-learning algorithm to train the client.  Our q-table has a state number that corresponds to the non-air block number. Our actions include up, down, left, and right. 
For each iteration, we update our q value according to the algorithm:

Our reward function for now just gives a high reward to the path from blocks near destination to the destination. We will adjust it in the future. By doing this, we guarantee that our rewards are updated for every iteration from states to other states. 
Start Point: Redstone block
Delivery Point: Emerald
Common Speed: Diamond
Speed Up: Ice, Minecart
Speed Down: Soul Sand
Evaluation
Our baseline chooses the shortest path regardless of the block type and time cost. It picks a random path if more than one path is the shortest one. We used the Dijkstra algorithm from assignment 1. It ensures that the agent is traveling within the minimum amount of distance. 

The algorithm we are utilizing is (To Be determined) by using (TBD) library. 
The core task of this mission is to save our client within a fast amount of time, so the evaluation is highly based on the waiting. The 
Quantitive:
(Image to be inserted)
(Chart or Graph TBD)
Remaining Goals and Challenges
Need more time to do the training (The algorithm cost long time to train, we hope to find the balance between the running time and the performance)
We hope to improve our simple reward function to improve the performance.
We will test more QL input such as the learning rate.
Need optimization to improve performance and time consumption
We are currently evaluating our agent’s performance by only distance travelled, and we will add other factors into consideration like block types (meaning the traveling speed), and amount of waiting time of all customers. 
We will expand our map to 10*10 later. 
Multiple agents to deliver our resources, and we will consider queuing algorithms later. 
Resources:
Q-learning library  https://pypi.org/project/pyqlearning/
Assignment one from CS 175
Q table from Python Tutorial

