'''
Created on 11.09.2017

@author: Jason
'''
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import ANNdetection_train as nnd
import os, re, argparse

def nn_datasynth():   
    run_id = args.runid
    tf.reset_default_graph()
    #load experiment
    schemename = args.schemepath
    scheme = np.loadtxt(schemename, skiprows=1)     
    grad_dir = scheme[:,0:3]*5
    grad_str = np.absolute(scheme[:,3])*10    
    # form x array
    exp = np.column_stack((grad_dir, grad_str))   
    tf_x = tf.placeholder(tf.float32, [None, int(exp.shape[1]+2)])    
    # neural network layers
    neurons_no = args.neuron_no
    activation_function = tf.nn.relu
    l1 = tf.layers.dense(tf_x, neurons_no, activation_function)          # hidden layer
    l2 = tf.layers.dense(l1, neurons_no, activation_function)          # hidden layer
    output = tf.layers.dense(l2, 1, activation_function)                     # output layer  
    saver = tf.train.Saver()   
    def visualizer():
        #load actual signals
        bfloat_list = []
        bfloatpath = args.bfloatpath
        print(bfloatpath + " is used to locate .Bfloat files\n")
        for file in os.listdir(bfloatpath):
            if file.endswith(".Bfloat"):
                bfloat_list.append(bfloatpath + file)        
        with tf.Session() as sess:
            saver.restore(sess, "checkpoints/" + run_id)
            cmap = plt.get_cmap('jet')
            colors = [cmap(i) for i in np.linspace(0, 1, len(bfloat_list))]
            c = 0 # counter for line color
            for bfloat in bfloat_list:
                l = 0 # counter for label
                #plot real data
                filename = bfloat
                data = np.fromfile(filename, dtype='>f')
                signals = np.absolute(data)/10000     #divided by number of walkers (10000)
                signals = np.reshape(signals,(-1,1))                                   
                #gather geometry stats
                #IMPORTANT: filename MUST be in the format generated by the MATLAB script with stats in file name
                gstats = os.path.basename(os.path.splitext(os.path.splitext(filename)[0])[0])
                gstats = re.findall(r"[-+]?\d*\.\d+|\d+",gstats)
                rad = np.full((exp.shape[0], 1), gstats.pop(0))
                amp = np.full((exp.shape[0], 1), np.float32(gstats.pop(0)))
                g = np.full((exp.shape[0], 1), gstats.pop(0))
                volfract = np.full((exp.shape[0], 1), np.float32(gstats.pop(0)))                
                #visualization
                label, labels = nnd.findlabels(amp[0][0], volfract[0][0])                               
                exp_section = 62 #visualize only the first 2 directions, which incl parallel and perpendicular           
                plt.scatter(exp[:exp_section,3]/10, signals[:exp_section,:], s=15, label='Camino ('+ str(labels[label]) + ')')             
                #plot predicted data
                x_test = np.column_stack((exp, amp, volfract))
                pred = sess.run(output, {tf_x: x_test})
                for p in np.arange(0, exp_section, 31):
                    if l==0:
                        plt.plot(x_test[p:(p+31),3]/10, pred[p:(p+31),:], color=colors[c], alpha=0.7, label='ANN ('+ str(labels[label]) +')')
                    else:
                        plt.plot(x_test[p:(p+31),3]/10, pred[p:(p+31),:], linestyle='dashed', color=colors[c], alpha=0.7)
                    l+=1
                
                c+=1
            plt.xlabel('Gradient strength', fontsize=10)
            plt.ylabel('Normalized diffusion signal', fontsize=10)
            plt.text(0.1, 1, '(solid='+r'$\bot$'+', dashed='+r'$\parallel$'+')', fontsize=10, horizontalalignment='center', verticalalignment='center')
            plt.xticks(fontsize=14)
            plt.yticks(fontsize=14)
            plt.legend(loc=1, prop={'size': 10})
            plt.show()   
    def synthesizer():
        # load ply files
        ply_list = []
        plypath = args.plypath
        print(plypath + " is used to locate .Bfloat files\n")
        for file in os.listdir(plypath):
            if file.endswith(".ply"):
                ply_list.append(plypath + file)                  
        with tf.Session() as sess:
            saver.restore(sess, "checkpoints/" + run_id)
            print("Found .ply files: ")
            for ply in ply_list:
                print(ply)
                filename = ply
                #gather geometry stats
                #IMPORTANT: filename MUST be in the format generated by the MATLAB script with stats in file name
                filename_noext = os.path.basename(os.path.splitext(filename)[0])
                gstats = re.findall(r"[-+]?\d*\.\d+|\d+",filename_noext)
                rad = np.full((exp.shape[0], 1), gstats.pop(0))
                amp = np.full((exp.shape[0], 1), np.float32(gstats.pop(0)))
                g = np.full((exp.shape[0], 1), gstats.pop(0))
                volfract = np.full((exp.shape[0], 1), np.float32(gstats.pop(0)))
                x_test = np.column_stack((exp, amp, volfract))
                pred = sess.run(output, {tf_x: x_test})               
                np.savetxt('nn_datasynth' + filename_noext + os.path.basename(schemename) + '.txt', pred, fmt='%10.4f')           
    if(args.bfloatpath):
        visualizer()      
    elif(args.plypath):
        synthesizer()
    else:
        parser.error("No operation specified. Please specify -vis or -syn.")
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("runid")
    parser.add_argument("neuron_no", type=int)
    parser.add_argument("schemepath")
    parser.add_argument("-syn", "--plypath")
    parser.add_argument("-vis", "--bfloatpath")
    args = parser.parse_args()
    nn_datasynth()