import argparse, time, pickle
import numpy as np
from MineExpressSimulator import MineExpressSimulator
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm
import torch
from torch import nn
import os

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(1, 512),
            nn.Linear(256, 64),
            nn.Linear(64, 6)
        )
    
    def forward(self, x):
        x = self.net(x)
        return x


class DQN:
    def __init__(self, memory_size, batch_size, learning_interval, learning_rate, gamma):
        self.memory_size = memory_size
        self.learning_interval = learning_interval
        self.batch_size = batch_size
        self.gamma = gamma
        
        self.eval, self.target = Net(), Net()
        
        if torch.cuda.is_available():
            self.eval.cuda()
            self.target.cuda()
        
        self.learning_counter = 0
        self.memory_counter = 0
        self.memory = np.zeros((memory_size, 4))
        self.optimizer = torch.optim.Adam(self.eval.parameters(), lr=learning_rate)
        self.loss_func = nn.MSELoss()
    
    def selectAction(self, state):
        state = torch.tensor([state]).float().unsqueeze(0).to(DEVICE)
        action = self.eval(state)
        return torch.argmax(action)
    
    def storeStepInfo(self, step_info):
        index = self.memory_counter % self.memory_size
        self.memory[index] = np.array(step_info)
        self.memory_counter += 1
    
    def learn(self):
        if self.learning_counter % self.learning_interval == 0:
            self.target.load_state_dict(self.eval.state_dict())
        self.learning_counter += 1
        
        indexes = np.random.choice(self.memory_size, self.batch_size)
        
        states, actions, rewards, states_ = np.split(self.memory[indexes], 4, axis=1)
        
        states = torch.from_numpy(states).float().to(DEVICE)
        actions = torch.from_numpy(actions).long().to(DEVICE)
        rewards = torch.from_numpy(rewards).float().to(DEVICE)
        states_ = torch.from_numpy(states_).float().to(DEVICE)
        
        q_eval = self.eval(states).gather(1, actions)
        q_target = rewards + self.gamma * self.target(states_).max(1)[0]
        loss = self.loss_func(q_target, q_eval)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--total_episodes", type=int, default=5000)
    parser.add_argument("--total_steps", type=int, default=100)
    
    parser.add_argument("--memory_size", type=int, default=500)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--learning_interval", type=int, default=50)
    
    parser.add_argument("--learning_rate", type=float, default=0.7)
    parser.add_argument("--gamma", type=float, default=0.618)
    parser.add_argument("--epsilon", type=float, default=1)
    parser.add_argument("--max_epsilon", type=float, default=1)
    parser.add_argument("--min_epsilon", type=float, default=0.3)
    parser.add_argument("--decay_rate", type=float, default=0.001)
    parser.add_argument("--save-model-interval", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    config = parser.parse_args()
    
    epsilon = config.epsilon
    env = MineExpressSimulator(config.seed)
    dqn = DQN(config.memory_size, config.batch_size, config.learning_interval, config.learning_rate, config.gamma)
    
    running_reward = 10.0
    total_reward = 0
    
    current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
    if not os.path.exists(f"runs/{current_time}"):
        os.makedirs(f"runs/{current_time}")
        os.makedirs(f"runs/{current_time}/data")
        os.makedirs(f"runs/{current_time}/model")
    writer = SummaryWriter(f"runs/{current_time}/data")
    
    data = []
    
    for episode in tqdm(range(config.total_episodes), ascii=True, desc="Episode Progress", position=0, ncols=100):
        
        state = env.reset()
        ep_reward = 0
        status = 0
        
        if episode % config.save_model_interval == 0 and episode > 0:
            torch.save(dqn, f"runs/{current_time}/model/episode-{episode}.pt")
        
        for step in range(config.total_steps):
            
            e = np.random.uniform(0, 1)
            
            action = dqn.selectAction(state) if e > epsilon else env.action_space.sample()
            
            new_state, reward, done, _ = env.step(action)
            
            dqn.storeStepInfo([state, action, reward, new_state])
            
            if dqn.memory_counter > config.memory_size:
                dqn.learn()
            
            ep_reward += reward
            total_reward += reward
            
            # tqdm.write(
            #     f"Step:{step}, Reward: {reward}, State {state},Action: {_}, AL: {env.agent_loc}, PL: {env.package_loc}, DL:{env.package_dest}")
            
            state = new_state
            
            if reward == 0:
                status = 1
            
            if done:
                status = 2
                tqdm.write("Mission Success!")
                break
        
        epsilon = config.min_epsilon + (config.max_epsilon - config.min_epsilon) * np.exp(-config.decay_rate * episode)
        
        running_reward = 0.05 * ep_reward + (1 - 0.05) * running_reward
        writer.add_scalar("Running Reward", running_reward, episode)
        writer.add_scalar("Episode Reward", ep_reward, episode)
        
        # tqdm.write(
        #     f"Episode {episode}\tLast reward: {ep_reward:.2f}\tAverage reward: {running_reward:.2f}"
        # )
        
        data.append([episode, ep_reward, status])
    
    writer.close()
    
    with open(f"runs/{current_time}/data/data.plk", "wb") as f:
        pickle.dump(data, f)
