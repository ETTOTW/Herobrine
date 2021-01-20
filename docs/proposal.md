---
layout: default
title: Proposal
---

## Summary of the Project
The project will train our game agent to deliver resources to survivors in an extremely dangerous world after the outbreak of an unknown zombie virus. In this chaotic world, Zombies will be spawning from random places and hunting for any human survivors. Our agent needs to avoid the attacks from zombies and distribute supplies to different sanctuaries as efficiently as possible. In this scenario, our agent not only needs to learn how to avoid zombies but also find the path with the minimum amount of time. Currently, Our main research goal is to implement the Q-learning, A* and D* Algorithms; and compare their performance in the specified pathfinding problem. We will utilize Minecraft to visualize the situation of the problem to help us understand Algorithms better.


## Assumptions
The test ground is a 100 * 100 grid map
Each grid is 5 * 5
Different Blocks represents the different cost of each path:
Start Point: Redstone block
Delivery Point: Emerald
Basic Path: Diamond
Faster Path: Ice, Minecart
Slower Path: Soul Sand
Unavailable Path: Air
Randomness
The initial map will be consist of diamond blocks 
Sides of grids will be replaced randomly with blocks mentioned above


## AI/ML Algorithms
We currently will implement Q-learning, A* and D* Algorithms, and study their differences in performance. 


## Evaluation Plan
Our metric is the time to deliver all resources. On the baseline, our agent always goes to the nearest survivor and chooses the nearest path. Our goal is to find a path that can minimize the total time to deliver the resources. We will test our agent with the different searching algorithms and compare the performance.

The first sanity check verifies that the agent takes the minimum distance. We create a 2x10 map that only contains the diamond in the path. It has survivors in rows 3, 6, 9 and column 0. Our agent is initialized at (0,0). It should go to (3,0), (6,0), (9,0) one by one and go back to (0,0) at the end. The second sanity check verifies that the agent considers the speed of different blocks. We create a 3x5 map that has block type ice in row 0 and block type soul sand in row 2. Our agent is initialized at (1,0), and a survivor is located at (1,4). The agent should choose row 2 to deliver the resource. Our moonshot case is a 100x100 map that has a random number of survivors. Our agent allocates all resources within the shortest time.



## Appointment with the Instructor
Our Appointment has been scheduled for 16:00, Wednesday, January 20, 2021
