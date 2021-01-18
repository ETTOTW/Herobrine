---
layout: default
title: Proposal
---

## Summary of the Project
The project will train our game agent to deliver resources to survivors in an extremely dangerous world after the outbreak of an unknown zombie virus. Each survivor will have a corresponding resource. Our agent needs to avoid the attacks from zombies and distribute all resources as efficiently as possible. In this scenario, our agent not only needs to learn how to avoid zombies but also needs to find the shorter path. We will utilize Minecraft to visualize the situation.


## AI/ML Algorithms
We will use reinforcement learning/Q-learning to decide the action of our agent in a state.


## Evaluation Plan
The metrics are the damage our agent got and the total distance. On the baseline, our agent finds the nearest resource and delivers it to the corresponding survivor. Our main goal is to avoid all attacks. We also aim to find the minimum distance to deliver all resources.

The first sanity check verifies that the agent takes the minimum distance. We create a 2x20 map that has all resources in the middle and all survivors at the end (1,19). Our agent is initialized at (0,0). it should first pick up all resources and then deliver them to survivors.
The second sanity check verifies that the agent avoids all zombies. We create a 10x4 map that has zombies in rows 2,4,6,8, wandering from columns 1 to 4. Our agent is initialized at (0,0). It should pick up the resource at (0,1), avoid all creatures, and reach the survivor at (9,3).
Our moonshot case has a random number of pairs of resources and survivors. Our agent allocates all resources within the shortest possible distance and avoids all zombies.


## Appointment with the Instructor
Our Appointment has been scheduled for 16:00, Wednesday, January 20, 2021
