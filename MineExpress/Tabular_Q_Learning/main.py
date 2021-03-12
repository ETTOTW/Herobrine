import argparse, time
import numpy as np
from MineExpressEnv.MineExpress import MineExpress
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

import os
os.chdir("../MineExpressEnv")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--total_episodes", type=int, default=1000)
    parser.add_argument("--total_steps", type=int, default=100)
    parser.add_argument("--learning_rate", type=float, default=0.8)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--epsilon", type=float, default=1)
    parser.add_argument("--max_epsilon", type=float, default=1)
    parser.add_argument("--min_epsilon", type=float, default=0.01)
    parser.add_argument("--decay_rate", type=float, default=0.01)
    parser.add_argument("--save-model-interval", type=int, default=50)
    parser.add_argument("--seed", type=int, default=None)
    config = parser.parse_args()
    
    epsilon = config.epsilon
    env = MineExpress(config.seed)
    q_table = np.zeros((env.state_num, env.action_num))
    running_reward = 0.0
    
    current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
    
    
    if not os.path.exists(f"runs/{current_time}"):
        os.makedirs(f"runs/{current_time}")
        os.makedirs(f"runs/{current_time}/data")
        os.makedirs(f"runs/{current_time}/model")
    
    avgep_writer = SummaryWriter(f"runs/{current_time}/data")
    ep_writer = SummaryWriter(f"runs/{current_time}/data")
    
    for episode in tqdm(range(config.total_episodes), ascii=True, desc="Episode Progress", position=0,ncols=100):

        state = env.reset()
        ep_reward = 10
        
        if episode % config.save_model_interval == 0 and episode > 0:
            np.save(f"runs/{current_time}/model/episode-{episode}", q_table)
        
        
        # for step in tqdm(range(config.total_steps), ascii=True, desc="Step Progress", position=1, ncols=100):
        for step in range(config.total_steps):
        
            e = np.random.uniform(0, 1)
            
            action = np.argmax(q_table[state, :]) if e > epsilon else env.action_space.sample()

            new_state, reward, done, _ = env.step(action)
            
            q_table[state, action] += config.learning_rate * (
                    reward + config.gamma * np.max(q_table[new_state, :]) - q_table[state, action])
            
            ep_reward += reward
            
            if done or step == config.total_steps - 1:
                
                running_reward = 0.05 * ep_reward + (1 - 0.05) * running_reward
                
                avgep_writer.add_scalar("Mean Episode Reward", running_reward, episode)
                ep_writer.add_scalar("Episode Reward", reward, episode)
                
                tqdm.write(
                    "Episode {}\tLast reward: {:.2f}\tAverage reward: {:.2f}".format(episode, ep_reward, running_reward)
                )
                
                break
            
            state = new_state
        
        epsilon = config.min_epsilon + (config.max_epsilon - config.min_epsilon) * np.exp(-config.decay_rate)
    
    ep_writer.close()
    avgep_writer.close()