# implemented using sum_tree

import os
import random

import gym
import numpy as np
import tensorflow as tf
from memory import Memory

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
env = gym.make("MountainCar-v0")
env.reset()
model_save_path = "C:/Users/sanka/codes/mountain car openai/mc_save"
save_file="mc_save-Copy.meta"


class dqn(object):
    def __init__(self):
        self.batch_size = 64
        self.episodes = 20000
        self.input_size = env.observation_space.sample().size
        self.output_size = env.action_space.n
        self.gamma = 0.99
        self.epsilon = 1.0
        self.step = 0
        self.learning_rate = 0.001
        self.lambda1 = 0.01
        self.initial_epsilon = self.epsilon
        self.final_epsilon = 0.01
        self.weights = {}
        self.biases = {}
        self.target_weights = {}
        self.target_biases = {}
        self.create_nn()
        self.create_training_network()
        self.max_size = 10000
        self.memory = Memory(size=self.max_size)
        self.sess = tf.InteractiveSession()
        self.graph=tf.get_default_graph()
        self.saver = tf.train.import_meta_graph(save_file)
        self.saver.restore(self.sess,"mc_save-Copy")

    def load_variables(self):
        self.step=load()
        pass

    def create_nn(self):
        try:
            for i in range(1,5,1):
                self.weights[i] = self.graph.get_tensor_by_name('w{0}'.format(i))
                self.biases[i] = self.graph.get_tensor_by_name('b{0}'.format(i))
                self.target_weights[i] = self.graph.get_tensor_by_name('tw{0}'.format(i))
                self.target_biases[i] = self.graph.get_tensor_by_name('tb{0}'.format(i))
        except:
            pass

    def feed_forward(self, z):
        q = tf.nn.relu(tf.matmul(z, self.weights[1]) + self.biases[1])
        for i in range(2, len(self.weights), 1):
            q = tf.nn.relu(tf.matmul(q, self.weights[i]) + self.biases[i])
        q = tf.matmul(q, self.weights[len(self.weights)]) + self.biases[len(self.biases)]
        return q

    def feed_forward_target(self, z):
        q = tf.nn.relu(tf.matmul(z, self.target_weights[1]) + self.target_biases[1])
        for i in range(2, len(self.weights), 1):
            q = tf.nn.relu(tf.matmul(q, self.target_weights[i]) + self.target_biases[i])
        q = tf.matmul(q, self.target_weights[len(self.weights)]) + self.target_biases[len(self.weights)]
        return q

    def create_training_network(self):
        self.x = tf.placeholder(tf.float32, [None, self.input_size])
        self.y = tf.placeholder(tf.float32, [None])
        self.a = tf.placeholder(tf.float32, [None, self.output_size])
        self.q_value = self.feed_forward(self.x)
        self.q_value_target = self.feed_forward_target(self.x)
        self.output = tf.reduce_sum(tf.multiply(self.q_value, self.a), reduction_indices=1)
        self.action = tf.argmax(self.q_value, 1)
        self.loss = tf.reduce_mean(tf.square(self.output - self.y))
        self.optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate).minimize(self.loss)

    def append_to_memory(self, state, action, reward, next_state, done):
        one_hot_action = np.zeros(self.output_size)
        one_hot_action[action] = 1.0
        prob = (abs(reward) + .01) ** 0.6
        self.memory.append(prob, (state, one_hot_action, reward, next_state, done))
        if self.memory.current_size >= self.memory.size:
            self.step += 1
            #self.epsilon = self.final_epsilon + (self.initial_epsilon - self.final_epsilon) * np.exp(
            #    -self.lambda1 * (self.step / 100))
            self.epsilon=self.initial_epsilon-(self.step/200)*0.01
            if (self.flag == 0):
                print("started training")
                self.flag = 1
            self.train()

    def get_reward(self, q1, q2, reward, done):
        if done:
            return reward
        else:
            return reward + self.gamma * q2[np.argmax(q1)]

    def train(self):
        index, sample = self.memory.sample(self.batch_size)
        train_x = [i[0] for i in sample]
        action = [i[1] for i in sample]
        reward = [i[2] for i in sample]
        next_state = [i[3] for i in sample]
        train_y = []
        q = self.sess.run(self.q_value, feed_dict={self.x: np.array(train_x)})
        q_1 = self.sess.run(self.q_value, feed_dict={self.x: np.array(next_state)})
        q_next = self.sess.run(self.q_value_target, feed_dict={self.x: np.array(next_state)})
        for i in range(len(reward)):
            train_y.append(self.get_reward(q_1[i], q_next[i], reward[i], sample[i][4]))
        train_y = np.array(train_y)
        train_x = np.array(train_x)
        action = np.array(action)
        self.sess.run(self.optimizer, feed_dict={self.x: train_x, self.y: train_y, self.a: action})
        for i in range(self.batch_size):
            error = abs(np.max(q[i]) - train_y[i])
            self.memory.update(index[i], (error + 0.01) ** 0.6)
            # return loss

    def copy_variables(self):
        for i in range(1, len(self.weights) + 1, 1):
            self.sess.run(self.target_weights[i].assign(self.weights[i]))
            self.sess.run(self.target_biases[i].assign(self.biases[i]))

    def save(self):
        self.saver.save(self.sess, model_save_path)
        print("model saved")


def main():
    obj = dqn()
    for e in range(obj.episodes):
        p = env.reset()
        for i in range(500):
            ac = obj.sess.run(obj.action, feed_dict={obj.x: np.array([p])})[0]
            if np.random.rand() < obj.epsilon:
                ac = random.randint(0, obj.output_size - 1)

            obs, rew, done, _ = env.step(ac)
            obj.append_to_memory(p, ac, rew, obs, done)
            p = obs
            if done:
                break
            if obj.step % 1000 == 0 and obj.flag==1:
                obj.copy_variables()
        # print("episode {0} completed with loss: {1}".format(e, total_loss))

        if e % 100 == 0:
            print("episodes {0} completed".format(e), )
            av = []
            for f in range(10):
                p = env.reset()
                r = 0
                for i in range(200):
                    ac = obj.sess.run(obj.action, feed_dict={obj.x: np.array([p])})[0]
                    p, rew, done, _ = env.step(ac)
                    r += rew
                    if done:
                        break
                av.append(r)
            print("average score is {0}".format(np.average(np.array(av))))
            obj.save()


if __name__ == '__main__':
    main()
